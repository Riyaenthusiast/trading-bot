"""
Logging configuration for the trading bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "trading_bot", log_dir: str = "logs") -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.

    Args:
        name: Logger name (used as log file prefix).
        log_dir: Directory where log files will be stored.

    Returns:
        Configured Logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler — DEBUG and above
    fh = logging.FileHandler(log_filename, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)

    # Console handler — INFO and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Logger initialised. Log file: %s", log_filename)
    return logger
