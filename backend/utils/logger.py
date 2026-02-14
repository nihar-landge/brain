"""
Structured Logging - File + console with daily rotation.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logger(name: str = "brain") -> logging.Logger:
    """Create structured logger with file + console output."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler with daily rotation, keep 30 days
    file_handler = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


# Default logger instance
log = setup_logger()
