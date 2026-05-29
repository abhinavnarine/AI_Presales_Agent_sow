"""Shared logging setup for the backend. Call setup_logging() once at process start."""
from __future__ import annotations

import logging
import os

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure the root logger from the ``LOG_LEVEL`` environment variable.

    Uses ``INFO`` when ``LOG_LEVEL`` is unset or invalid. Safe to call multiple
    times; subsequent calls only adjust the root level if handlers already exist.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=LOG_FORMAT)
    else:
        root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        Standard library ``logging.Logger`` instance.
    """
    return logging.getLogger(name)
