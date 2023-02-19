import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from belphegor.settings import settings

#=============================================================================================================================#

def get_logger():
    log = logging.getLogger(settings.LOGGER)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), "ERROR")
    log.setLevel(log_level)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setStream(sys.stdout)
        formatter = logging.Formatter(settings.LOG_FORMAT)
        handler.setFormatter(formatter)
        log.addHandler(handler)

    return log