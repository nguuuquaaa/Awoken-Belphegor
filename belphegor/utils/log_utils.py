import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from belphegor.settings import settings

def get_logger():
    log = logging.getLogger(settings.LOGGER)
    log.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), "ERROR"))

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = TimedRotatingFileHandler(
        filename = f"./logs/{settings.LOGGER}.log",
        when = "midnight",
        encoding = "utf-8",
        utc = True,
        backupCount = 7
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log