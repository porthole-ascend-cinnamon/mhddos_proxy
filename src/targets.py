from pathlib import Path
from typing import Optional

import requests

from core import cl, logger


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
        if "://" in target:
            return target

        try:
            _, port = target.split(":", 1)
        except ValueError:
            port = "80"

        scheme = "https://" if port == "443" else "http://"
        return scheme + target

    def config_content_by_path(self, path: Path) -> Optional[str]:
        if path.is_file():
            return path.read_text()

        try:
            return requests.get(self.config, timeout=5).text
        except (requests.RequestException, requests.ConnectionError):
            logger.warning(
                f"{cl.RED}Не вдалося (пере)завантажити конфіг - буде використано останні відомі цілі{cl.RESET}"
            )

    def load_config(self):
        if not self.config:
            return

        path = Path(self.config)
        config_content: Optional[str] = self.config_content_by_path(path)

        if not config_content:
            return

        self.config_targets = [target.strip() for target in config_content.split() if target.strip()]

        if path.is_file():
            logger.info(
                f"{cl.BLUE}Завантажено конфіг із локального файлу {cl.YELLOW}{self.config} "
                f"на {len(self.config_targets)} цілей{cl.RESET}"
            )
        else:
            logger.info(
                f"{cl.BLUE}Завантажено конфіг із віддаленого серверу {cl.YELLOW}{self.config} "
                f"на {len(self.config_targets)} цілей{cl.RESET}"
            )
