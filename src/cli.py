import sys
import argparse

from .core import COPIES_AUTO, DEFAULT_THREADS, Methods, SCHEDULER_FORK_SCALE, SCHEDULER_INITIAL_CAPACITY
from .i18n import LANGUAGES, translate as t
from .app_config import read_config, save_config, CONFIG_DEFAULT_PATH


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'targets',
        nargs='*',
        help='List of targets, separated by spaces',
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
        '--itarmy',
        action='store_true',
        default=False,
        help='Use targets from https://itarmy.com.ua/'
    )
    parser.add_argument(
        '--lang',
        type=str.lower,
        choices=LANGUAGES,
        help='Select language (default is ua)'
    )
    parser.add_argument(
        '--vpn',
        dest='use_my_ip',
        const=2,
        default=0,
        nargs='?',
        type=int,
        action='store',
        help='Use both my IP and proxies for the attack. '
             'Optionally, specify a chance of using my IP (default is 2%%)',
    )
    parser.add_argument(
        '-c',
        '--config',
        dest='targets_config',
        metavar='URL|path',
        help='URL or local path to file with attack targets',
    )
    parser.add_argument(
        '--proxies',
        metavar='URL|path',
        help='URL or local path to file with proxies to use',
    )
    parser.add_argument(
        '--proxy',
        nargs='*',
        help='List of proxies to use, separated by spaces',
    )
    parser.add_argument(
        '--http-methods',
        nargs='+',
        type=str.upper,
        default=['GET'],
        choices=Methods.HTTP_METHODS,
        help='List of HTTP(L7) methods to use. Default is GET',
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
    parser.add_argument(
        '--save-config',
        action='store_true',
        default=False,
        required=False,
        help=f'Save current configuration in `{CONFIG_DEFAULT_PATH}` config file'
    )

    # Deprecated
    parser.add_argument('--table', action='store_true', help='[DEPRECATED]')
    parser.add_argument('--debug', action='store_true', help='[DEPRECATED]')

    # Either save selected defaults config, or load it from file
    new_config = vars(parser.parse_args())
    if new_config['save_config']:
        del new_config['save_config']
        save_config(new_config)
        print(f"{t('Config file')} `{CONFIG_DEFAULT_PATH}` {t('has been created successfully')}. {t('It will override command-line default values')}")
        print(t('Now you may remove unnecessary options from it, and leave the config with some meaningful defaults'))
        sys.exit(0)
    elif len(defaults_config := read_config()):
        parser.set_defaults(**defaults_config)

    return parser
