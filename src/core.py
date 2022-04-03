import logging
from pathlib import Path

from colorama import Fore

logging.basicConfig(format="[%(asctime)s - %(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("mhddos_proxy")
logger.setLevel("INFO")

ROOT_DIR = Path(__file__).parent.parent

PROXIES_URL = "https://raw.githubusercontent.com/porthole-ascend-cinnamon/proxy_scraper/main/proxies.txt"
IT_ARMY_CONFIG_URL = (
    "https://gist.githubusercontent.com/ddosukraine2022/f739250dba308a7a2215617b17114be9/raw/mhdos_targets_tcp.txt"
)

PROXY_TIMEOUT = 5
UDP_THREADS = 1
LOW_RPC = 1000

THREADS_PER_CORE = 800
MAX_DEFAULT_THREADS = 4000


class cl:
    MAGENTA = Fore.LIGHTMAGENTA_EX
    BLUE = Fore.LIGHTBLUE_EX
    GREEN = Fore.LIGHTGREEN_EX
    YELLOW = Fore.LIGHTYELLOW_EX
    RED = Fore.LIGHTRED_EX
    RESET = Fore.RESET
