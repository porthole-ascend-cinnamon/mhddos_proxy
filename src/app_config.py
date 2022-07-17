import os
import json
from .path_utils import CONFIG_DEFAULT_PATH


def read_config(config_file: str = CONFIG_DEFAULT_PATH) -> dict:
    """
    Config is a JSON file normally located in the users' $HOME directory,
    and overwrites defaults for the application.
    If the file does not exist, we just proceed with application defaults.
    For example, if you always want to pick up targets from IT Army,
    and permanently set Ukrainian language for the interface,
    you create file `.mhddos.json` in your $HOME with those values:
    {
        "itarmy": true,
        "lang": "UA"
    }
    :param config_file: absolute path to config file
    :return: Python dictionary
    """
    if not os.path.isfile(config_file):
        return {}
    # read JSON file
    with open(config_file, 'r') as config_file:
        config = json.load(config_file)
    return config


def save_config(config: dict, config_file: str = CONFIG_DEFAULT_PATH):
    """
    Save config to file
    :param config: Python dictionary
    :param config_file: absolute path to config file
    :return:
    """
    with open(config_file, 'w+', encoding='utf8') as outfile:
        outfile.write(json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False))
