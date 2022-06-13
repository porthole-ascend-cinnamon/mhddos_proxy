import logging
import warnings
from asyncio.log import logger as asyncio_logger
from contextlib import suppress
from multiprocessing import cpu_count
from pathlib import Path
from typing import Optional, Tuple

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

CPU_PER_COPY = 2
COPIES_AUTO = "auto"
MAX_COPIES_AUTO = 4

USE_ONLY_MY_IP = 100
SCHEDULER_INITIAL_CAPACITY = 3
SCHEDULER_MIN_INIT_FRACTION = 0.1
SCHEDULER_MAX_INIT_FRACTION = 0.5
SCHEDULER_FORK_SCALE = 3
CONN_PROBE_PERIOD = 5
GRACEFUL_SHUTDOWN_SECONDS = 2.0

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
