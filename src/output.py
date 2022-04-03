import os
from threading import Lock

import colorama
from tabulate import tabulate

from core import cl, logger
from mhddos import Tools

if os.name == "nt":
    colorama.init()


def cls():
    os.system("cls" if os.name == "nt" else "clear")


class AtomicCounter:
    def __init__(self, initial=0):
        self.value = initial
        self._lock = Lock()

    def __iadd__(self, value):
        self.increment(value)
        return self

    def __int__(self):
        return self.value

    def increment(self, num=1):
        with self._lock:
            self.value += num

    def reset(self, value=0):
        with self._lock:
            old = self.value
            self.value = value
        return old


def show_statistic(statistics, refresh_rate, table, vpn_mode, proxies_cnt, period, passed):
    tabulate_text = []
    total_pps = 0
    total_bps = 0
    for k in statistics:
        counters = statistics[k]
        pps = int(counters["requests"].reset() / refresh_rate)
        total_pps += pps
        bps = int(8 * counters["bytes"].reset() / refresh_rate)
        total_bps += bps
        if table:
            tabulate_text.append(
                (
                    f"{cl.YELLOW}%s" % k.url.host,
                    k.url.port,
                    k.method,
                    k.threads,
                    Tools.humanformat(pps),
                    f"{Tools.humanbits(bps)}{cl.RESET}",
                )
            )
        else:
            logger.info(
                f"{cl.YELLOW}Ціль:{cl.BLUE} {k.url.host},{cl.YELLOW} Порт:{cl.BLUE} {k.url.port},{cl.YELLOW} "
                f"Метод:{cl.BLUE} {k.method}{cl.YELLOW} Потоків:{cl.BLUE} {k.threads}{cl.YELLOW} "
                f"PPS:{cl.BLUE} {Tools.humanformat(pps)},{cl.YELLOW} BPS:{cl.BLUE} {Tools.humanbits(bps)}{cl.RESET}"
            )

    if table:
        tabulate_text.append(
            (
                f"{cl.GREEN}Усього",
                "",
                "",
                "",
                Tools.humanformat(total_pps),
                f"{Tools.humanbits(total_bps)}{cl.RESET}",
            )
        )

        cls()
        print(
            tabulate(
                tabulate_text,
                headers=[
                    f"{cl.BLUE}Ціль",
                    "Порт",
                    "Метод",
                    "Потоки",
                    "Запити/c",
                    f"Трафік/c{cl.RESET}",
                ],
                tablefmt="fancy_grid",
            )
        )
        print_banner(vpn_mode)

    print_progress(period, passed, proxies_cnt)


def print_progress(period, passed, proxies_cnt):
    logger.info(f"{cl.GREEN}Новий цикл через: {round(period - passed)} секунд{cl.RESET}")
    if proxies_cnt:
        logger.info(f"{cl.GREEN}Кількість проксі: {proxies_cnt}{cl.RESET}")
    else:
        logger.info(f"{cl.GREEN}Атака без проксі - переконайтеся що ви анонімні{cl.RESET}")


def print_banner(vpn_mode):
    print(
        f"""
- {cl.YELLOW}Навантаження (кількість потоків){cl.RESET} - параметр `-t 3000`, за замовчуванням - CPU * 1000
- {cl.YELLOW}Статистика у вигляді таблиці або тексту{cl.RESET} - прапорець `--table` або `--debug`
- {cl.YELLOW}Повна документація{cl.RESET} - https://github.com/porthole-ascend-cinnamon/mhddos_proxy
    """
    )

    if not vpn_mode:
        print(
            f"{cl.MAGENTA}Щоб використовувати VPN або власний IP замість проксі - додайте прапорець `--vpn`{cl.RESET}\n"
        )
