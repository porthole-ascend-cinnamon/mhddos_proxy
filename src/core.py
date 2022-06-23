import logging
import warnings
from asyncio.log import logger as asyncio_logger
from contextlib import suppress
from multiprocessing import cpu_count
from pathlib import Path
from typing import Optional, Set, Tuple

from colorama import Fore


warnings.filterwarnings("ignore")


class RemoveUselessWarnings(logging.Filter):
    def filter(self, record):
        return all((
            "socket.send() raised exception." not in record.getMessage(),
            "SSL connection is closed" not in record.getMessage()
        ))


LOGGER_MSG_FORMAT = '[%(asctime)s - %(levelname)s] %(message)s'
LOGGER_DATE_FORMAT = "%H:%M:%S"

logging.basicConfig(format=LOGGER_MSG_FORMAT, datefmt=LOGGER_DATE_FORMAT)
logger = logging.getLogger('mhddos_proxy')
logger.setLevel('INFO')

# Make asyncio logger a little bit less noisy
asyncio_logger.addFilter(RemoveUselessWarnings())


def setup_worker_logger(process_index: Optional[Tuple[int, int]]) -> None:
    if process_index is None:
        return
    ind, total = process_index
    formatter = logging.Formatter(
        f"[{ind}/{total}] {LOGGER_MSG_FORMAT}", datefmt=LOGGER_DATE_FORMAT)
    with suppress(Exception):
        logger.parent.handlers[0].setFormatter(formatter)


ROOT_DIR = Path(__file__).parent.parent

CONFIG_URL = "https://raw.githubusercontent.com/porthole-ascend-cinnamon/mhddos_proxy/main/config.json"

CPU_COUNT = cpu_count()
DEFAULT_THREADS = 8000 if CPU_COUNT > 1 else 4000
LIMITS_PADDING = 50

COPIES_AUTO = "auto"
MAX_COPIES_AUTO = 4

USE_ONLY_MY_IP = 100
SCHEDULER_INITIAL_CAPACITY = 3
SCHEDULER_MIN_INIT_FRACTION = 0.1
SCHEDULER_MAX_INIT_FRACTION = 0.5
SCHEDULER_FORK_SCALE = 3
CONN_PROBE_PERIOD = 5
PROXY_ALIVE_PRIO_THRESHOLD = 0.25
PROXY_ALIVE_PRIO_RATE = 0.5

UDP_FAILURE_BUDGET_FACTOR = 3
UDP_FAILURE_DELAY_SECONDS = 1
UDP_BATCH_PACKETS = 16
UDP_ENOBUFS_PAUSE = 0.5


class cl:
    MAGENTA = Fore.LIGHTMAGENTA_EX
    CYAN = Fore.LIGHTCYAN_EX
    BLUE = Fore.LIGHTBLUE_EX
    GREEN = Fore.LIGHTGREEN_EX
    YELLOW = Fore.LIGHTYELLOW_EX
    RED = Fore.LIGHTRED_EX
    RESET = Fore.RESET


class Methods:
    HTTP_METHODS: Set[str] = {
        "CFB", "BYPASS", "GET", "RGET", "SLGET", "HEAD", "RHEAD", "SLHEAD", "POST", "STRESS",
        "DYN", "SLOW", "NULL", "COOKIE", "PPS", "EVEN", "AVB",
        "APACHE", "XMLRPC", "DOWNLOADER", "RHEX", "STOMP",
        # this is not HTTP method (rather TCP) but this way it works with --http-methods
        # settings being applied to the entire set of targets
        "TREX"
    }
    TCP_METHODS: Set[str] = {"TCP", }
    UDP_METHODS: Set[str] = {
        "UDP", "VSE", "FIVEM", "TS3", "MCPE",
        # the following methods are temporarily disabled for further investigation and testing
        # "SYN", "CPS",
        # Amplification
        # "ARD", "CHAR", "RDP", "CLDAP", "MEM", "DNS", "NTP"
    }
    ALL_METHODS: Set[str] = {*HTTP_METHODS, *UDP_METHODS, *TCP_METHODS}
