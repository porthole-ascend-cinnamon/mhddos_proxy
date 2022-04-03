import argparse
import random
from multiprocessing import cpu_count

from .core import MAX_DEFAULT_THREADS, THREADS_PER_CORE
from .mhddos import Methods


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "targets",
        nargs="*",
        help="List of targets, separated by spaces",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="URL to remote or path to local config file",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=min(THREADS_PER_CORE * cpu_count(), MAX_DEFAULT_THREADS),
        help="Total number of threads to run (default is CPU * 1000)",
    )
    parser.add_argument(
        "-p",
        "--period",
        type=int,
        default=900,
        help="How often to update the proxies (in seconds) (default is 900)",
    )
    parser.add_argument(
        "--rpc",
        type=int,
        default=2000,
        help="How many requests to send on a single proxy connection (default is 2000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Print log as text",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        default=False,
        help="Print log as table",
    )
    parser.add_argument(
        "--vpn",
        dest="vpn_mode",
        action="store_true",
        default=False,
        help="Disable proxies to use VPN",
    )
    parser.add_argument(
        "--http-methods",
        nargs="+",
        type=str.upper,
        default=[random.choice(["GET", "PPS"]), random.choice(["POST", "STRESS"])],
        choices=Methods.LAYER7_METHODS,
        help="List of HTTP(s) attack methods to use. Default is GET|PPS + POST|STRESS",
    )
    parser.add_argument(
        "--proxy-timeout",
        type=float,
        default=5,
        help="How many seconds to wait for the proxy to make a connection (default is 5)",
    )
    parser.add_argument(
        "--itarmy",
        action="store_true",
        default=False,
    )
    return parser
