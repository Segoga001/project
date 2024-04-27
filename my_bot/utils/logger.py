import json
from logging import Logger, config, getLogger
from pathlib import Path


path = Path(__file__).parent / 'logger.json'


def get_logger(name: str, template: str = "default") -> Logger:
    """
    Настройки логгера.

    :param name:
    :param template:
    :return: logger.Logger
    """
    with open(path, mode="r", encoding="utf-8") as log_file:
        dict_config = json.load(log_file)
        dict_config["loggers"][name] = dict_config["loggers"][template]

    config.dictConfig(dict_config)

    return getLogger(name)
