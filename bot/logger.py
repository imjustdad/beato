import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path

LOG_DIR = "logs"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    formatter = logging.Formatter(
        '%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s'
    )

    Path(LOG_DIR).mkdir(exist_ok=True)

    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = RotatingFileHandler(
            f"{LOG_DIR}/app.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def setup_library_loggers(level: str = "INFO"):
    praw_level = logging.DEBUG if level.upper() == "DEBUG" else logging.WARNING
    pymongo_level = logging.DEBUG if level.upper() == "DEBUG" else logging.WARNING

    for lib, path in [("praw", f"{LOG_DIR}/praw.log"), ("prawcore", f"{LOG_DIR}/praw.log")]:
        logger = logging.getLogger(lib)
        logger.setLevel(praw_level)
        if not logger.handlers:
            file_handler = RotatingFileHandler(
                path,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT
            )
            logger.addHandler(file_handler)

    pymongo_logger = logging.getLogger("pymongo.command")
    pymongo_logger.setLevel(pymongo_level)
    if not pymongo_logger.handlers:
        file_handler = RotatingFileHandler(
            f"{LOG_DIR}/pymongo.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        pymongo_logger.addHandler(file_handler)
