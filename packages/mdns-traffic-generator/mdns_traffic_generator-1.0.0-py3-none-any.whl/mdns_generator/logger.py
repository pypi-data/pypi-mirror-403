"""
Logging configuration for MDNS Traffic Generator.

Provides consistent logging across all modules with configurable levels and outputs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "mdns_generator",
    level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up and configure a logger instance.

    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "mdns_generator") -> logging.Logger:
    """
    Get an existing logger or create a basic one.

    Args:
        name: Logger name.

    Returns:
        logging.Logger: Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LoggerMixin:
    """Mixin class to provide logging capabilities to classes."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for the class."""
        return get_logger(self.__class__.__name__)
