"""Shared logging setup for the backend. Call setup_logging() once at process start."""
from __future__ import annotations

import logging
import os

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure root logger from LOG_LEVEL env (default INFO)."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=LOG_FORMAT)
    else:
        root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
