import asyncio
from asyncio import events
from contextlib import suppress
import json
import os.path
import selectors
import socket
import sys
import time
from threading import Thread
from typing import Callable, Optional

import requests

from src.core import cl, CONFIG_URL, logger
from src.i18n import translate as t


WINDOWS = sys.platform == "win32"
WINDOWS_WAKEUP_SECONDS = 0.5


def fix_ulimits() -> Optional[int]:
    try:
        import resource
    except ImportError:
        return None

    min_limit = 2 ** 15
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    # Try to raise hard limit if it's too low
    if hard < min_limit:
        with suppress(ValueError):
            resource.setrlimit(resource.RLIMIT_NOFILE, (min_limit, min_limit))
            soft = hard = min_limit

    # Try to raise soft limit to hard limit
    if soft < hard:
        with suppress(ValueError):
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
            soft = hard

    return soft


async def read_or_fetch(path_or_url: str) -> Optional[str]:
    if os.path.exists(path_or_url):
        with open(path_or_url, 'r') as f:
            return f.read()
    return await fetch(path_or_url)


def _sync_fetch(url: str):
    for _ in range(3):
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            pass
    return None


async def fetch(url: str) -> Optional[str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_fetch, url)


async def load_configs():
    local_config = json.loads(await read_or_fetch('config.json'))
    remote_config_cnt = await fetch(CONFIG_URL)
    if remote_config_cnt:
        remote_config = json.loads(remote_config_cnt)
    else:
        logger.warning(f'{cl.MAGENTA}Failed to load remote config, a local copy will be used!{cl.RESET}')
        remote_config = local_config
    return local_config, remote_config


def _safe_connection_lost(transport, exc) -> None:
    try:
        transport._protocol.connection_lost(exc)
    finally:
        if hasattr(transport._sock, 'shutdown') and transport._sock.fileno() != -1:
            try:
                transport._sock.shutdown(socket.SHUT_RDWR)
            except ConnectionResetError:
                pass
        transport._sock.close()
        transport._sock = None
        server = transport._server
        if server is not None:
            server._detach()
            transport._server = None


def _patch_proactor_connection_lost() -> None:
    """
    The issue is described here:
      https://github.com/python/cpython/issues/87419

    The fix is going to be included into Python 3.11. This is merely
    a backport for already versions.
    """
    from asyncio.proactor_events import _ProactorBasePipeTransport
    setattr(_ProactorBasePipeTransport, "_call_connection_lost", _safe_connection_lost)


async def _windows_support_wakeup() -> None:
    """See more info here:
        https://bugs.python.org/issue23057#msg246316
    """
    while True:
        await asyncio.sleep(WINDOWS_WAKEUP_SECONDS)


def _handle_uncaught_exception(loop: asyncio.AbstractEventLoop, context) -> None:
    error_message = context.get("exception", context["message"])
    logger.debug(f"Uncaught event loop exception: {error_message}")


def setup_event_loop() -> asyncio.AbstractEventLoop:
    uvloop = False
    try:
        __import__("uvloop").install()
        uvloop = True
        logger.info(f"{t('`uvloop` activated successfully')} {t('(increased network efficiency)')}")
    except:
        pass

    if uvloop:
        loop = events.new_event_loop()
    elif WINDOWS:
        _patch_proactor_connection_lost()
        loop = asyncio.ProactorEventLoop()
        # This is to allow CTRL-C to be detected in a timely fashion,
        # see: https://bugs.python.org/issue23057#msg246316
        loop.create_task(_windows_support_wakeup())
    elif hasattr(selectors, "DefaultSelector"):
        selector = selectors.DefaultSelector()
        loop = asyncio.SelectorEventLoop(selector)
    else:
        loop = events.new_event_loop()
    loop.set_exception_handler(_handle_uncaught_exception)
    asyncio.set_event_loop(loop)
    return loop


def terminate_loop(loop: asyncio.AbstractEventLoop) -> None:
    with suppress(Exception):
        tasks = asyncio.all_tasks(loop)
        for t in tasks:
            if not t.cancelled():
                t.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.shutdown_default_executor()
        if loop.is_running():
            loop.close()


def exec_after(timeout_seconds: float, f: Callable[[], None]) -> None:
    def _inner():
        time.sleep(timeout_seconds)
        f()
    Thread(target=_inner, daemon=True).start()
