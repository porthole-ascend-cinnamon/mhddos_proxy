from pathlib import Path

import requests

from core import logger, cl


class Targets:
    def __init__(self, targets, config):
        self.targets = targets
        self.config = config
        self.config_targets = []

    def __iter__(self):
        self.load_config()
        for target in self.targets + self.config_targets:
            yield self.prepare_target(target)

    def prepare_target(self, target):
        if '://' in target:
            return target

        try:
            _, port = target.split(':', 1)
        except ValueError:
            port = '80'

        scheme = 'https://' if port == '443' else 'http://'
        return scheme + target

    def load_config(self):
        if not self.config:
            return

        path = Path('.') / self.config
        is_local = path.is_file()
        if is_local:
            config_content = path.read_text()
        else:
            try:
                config_content = requests.get(self.config, timeout=5).text
            except requests.RequestException:
                logger.warning(f'{cl.RED}Не вдалося (пере)завантажити конфіг - буде використано останні відомі цілі{cl.RESET}')
                return

        self.config_targets = [
            target.strip()
            for target in config_content.split()
            if target.strip()
        ]

        if is_local:
            logger.info(f'{cl.BLUE}Завантажено конфіг із локального файлу {cl.YELLOW}{self.config} '
                        f'на {len(self.config_targets)} цілей{cl.RESET}')
        else:
            logger.info(f'{cl.BLUE}Завантажено конфіг із віддаленого серверу {cl.YELLOW}{self.config} '
                        f'на {len(self.config_targets)} цілей{cl.RESET}')
