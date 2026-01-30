"""Logging configuration for LiteSpeech."""

import logging
import os
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_logger: logging.Logger | None = None


def setup_logging(
    level: LogLevel | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """
    Set up logging for LiteSpeech.

    Args:
        level: Log level (defaults to LITESPEECH_LOG_LEVEL env var or INFO)
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    # Get log level from env or default to INFO
    if level is None:
        level = os.environ.get("LITESPEECH_LOG_LEVEL", "INFO").upper()  # type: ignore

    # Create logger
    logger = logging.getLogger("litespeech")
    logger.setLevel(getattr(logging, level))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level))

        if format_string is None:
            format_string = "[%(levelname)s] %(name)s: %(message)s"

        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the LiteSpeech logger, setting it up if necessary."""
    global _logger
    if _logger is None:
        return setup_logging()
    return _logger
