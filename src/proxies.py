import os
import random
from concurrent.futures import as_completed
from time import time
from typing import Generator

import requests
from PyRoxy import Proxy, ProxyUtiles
from yarl import URL

from core import PROXIES_URL, ROOT_DIR, cl, logger
from dns_utils import resolve_host


def download_proxies() -> Generator:
    try:
        response = requests.get(PROXIES_URL, timeout=10)
        for line in response.iter_lines(decode_unicode=True):
            yield Proxy.fromString(line)
    except requests.ConnectionError:
        yield None


def update_proxies(thread_pool, period, targets, proxy_timeout):
    #  NOTE: Avoid parsing proxies too often when restart happens
    proxies_file = ROOT_DIR / "files/proxies.txt"
    if proxies_file.exists():
        last_update = os.path.getmtime(proxies_file)
        if (time() - last_update) < period / 2:
            proxies = ProxyUtiles.readFromFile(str(proxies_file))
            logger.info(f"{cl.GREEN}Використовується список {len(proxies)} проксі з попереднього запуску{cl.RESET}")
            return proxies

    logger.info(f"{cl.GREEN}Завантажуємо список проксі...{cl.RESET}")
    proxies = list(set(download_proxies()))
    random.shuffle(proxies)

    size = len(targets)
    logger.info(
        f"{cl.YELLOW}Перевіряємо на працездатність {cl.BLUE}{len(proxies):,}{cl.YELLOW}"
        f" проксі - це може зайняти пару хвилин:{cl.RESET}"
    )

    future_to_proxy = {}
    for target, chunk in zip(targets, (proxies[i::size] for i in range(size))):
        resolved_target = URL(target).with_host(resolve_host(target))
        future_to_proxy.update(
            {thread_pool.submit(proxy.check, resolved_target, proxy_timeout): proxy for proxy in chunk}
        )

    working_proxies = [future_to_proxy[future] for future in as_completed(future_to_proxy) if future.result()]

    if not working_proxies:
        logger.error(
            "Не знайдено робочих проксі. "
            "Переконайтеся що інтернет з`єднання стабільне і ціль доступна. "
            "Перезапустіть Docker"
        )
        exit()

    logger.info(f"{cl.YELLOW}Знайдено робочих проксі: {cl.BLUE}{len(working_proxies):,}{cl.RESET}")

    with proxies_file.open("w") as wr:
        for proxy in working_proxies:
            wr.write(str(proxy) + "\n")

    return working_proxies
