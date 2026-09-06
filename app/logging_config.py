"""Centralized logging configuration for the application."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


LOGGER_NAME = "youtube_audio_extractor"
LOG_FILENAME = "youtube_audio_extractor.log"


def configure_logging(log_directory: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure application logging once and return the application logger.

    Console output remains available during development, while a rotating file
    keeps a persistent diagnostic history for packaged/desktop executions.
    Repeated calls do not add duplicate handlers.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    directory = log_directory or os.path.join(os.path.expanduser("~"), "Audio")
    os.makedirs(directory, exist_ok=True)
    log_path = os.path.join(directory, LOG_FILENAME)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logging da aplicação configurado | arquivo=%s", log_path)
    return logger


def get_logger(component: str) -> logging.Logger:
    """Return a named child logger for an application component."""
    return logging.getLogger(f"{LOGGER_NAME}.{component}")
