import argparse
import random
from typing import Union

from .core import COPIES_AUTO, DEFAULT_THREADS, SCHEDULER_FORK_SCALE, SCHEDULER_INITIAL_CAPACITY
from .i18n import LANGUAGES
from .mhddos import Methods


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'targets',
        nargs='*',
        help='List of targets, separated by spaces',
    )
    parser.add_argument(
        '-c',
        '--config',
        help='URL or local path to file with attack targets',
    )
    parser.add_argument(
        '-t',
        '--threads',
        type=int,
        help=f'Number of threads (default is {DEFAULT_THREADS})',
    )
    parser.add_argument(
        '--copies',
        type=lambda val: val if val == COPIES_AUTO else int(val),
        default=1,
        help='Number of copies (default is 1). Use "auto" to set the value automatically',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Detailed log for each target',
    )
    parser.add_argument(
        '--vpn',
        dest='use_my_ip',
        const=10,
        default=0,
        nargs='?',
        type=int,
        action='store',
        help='Use both my IP and proxies for the attack. '
             'Optionally, specify a percent of using my IP (default is 10%%)',
    )
    parser.add_argument(
        '--http-methods',
        nargs='+',
        type=str.upper,
        default=['GET', random.choice(['POST', 'STRESS'])],
        choices=Methods.HTTP_METHODS,
        help='List of HTTP(L7) methods to use. Default is GET + POST|STRESS',
    )
    parser.add_argument(
        '--proxies',
        help='URL or local path to file with proxies to use',
    )
    parser.add_argument(
        '--itarmy',
        action='store_true',
        default=False,
        help='Attack targets from https://t.me/itarmyofukraine2022'
    )
    parser.add_argument(
        '--lang',
        type=str.lower,
        choices=LANGUAGES,
        help='Select language (default is ua)'
    )
    parser.add_argument(
        '--timer',
        type=int,
        default=-1,
        help='For how many seconds program will work'
    )

    # Advanced
    parser.add_argument(
        '--rpc',
        type=int,
        default=2000,
        help='How many requests to send on a single proxy connection (default is 2000)',
    )
    parser.add_argument(
        '--scheduler-initial-capacity',
        type=int,
        default=SCHEDULER_INITIAL_CAPACITY,
        help='How many tasks per target to initialize on launch',
    )
    parser.add_argument(
        '--scheduler-fork-scale',
        type=int,
        default=SCHEDULER_FORK_SCALE,
        help='How many tasks to fork on successful connect to the target',
    )

    # Deprecated
    parser.add_argument('--table', action='store_true', default=False)

    return parser
