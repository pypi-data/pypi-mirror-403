import logging
from collections import defaultdict


class Formatter(logging.Formatter):
    """
    Custom logging formatter to support logging warnings in the color yellow
    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    reset = "\x1b[0m"
    format_ = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = defaultdict(lambda: Formatter.grey + Formatter.format_ + Formatter.reset)
    FORMATS[logging.WARNING] = yellow + format_ + reset

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_warning_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARN)
    handler.setFormatter(Formatter())
    logger.addHandler(handler)

    return logger
