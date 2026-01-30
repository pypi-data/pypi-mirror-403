"""Debug utilities and logging configuration for LiteSpeech."""

import logging
import os
import sys


def setup_logging() -> None:
    """
    Setup logging configuration from environment variables.

    Environment variables:
    - LITESPEECH_LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      Example: export LITESPEECH_LOG_LEVEL=DEBUG

    - LITESPEECH_LOG_FORMAT: Set log format (simple, detailed, json)
      Default: simple

    Usage in your code:
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> logger.debug("Debug message")  # Only shows if LITESPEECH_LOG_LEVEL=DEBUG
    """
    # Get log level from environment (default: WARNING)
    log_level_str = os.getenv("LITESPEECH_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_str, logging.WARNING)

    # Get log format preference
    log_format_type = os.getenv("LITESPEECH_LOG_FORMAT", "simple").lower()

    if log_format_type == "detailed":
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    elif log_format_type == "json":
        # Simple JSON-like format
        log_format = '{"time":"%(asctime)s", "logger":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
    else:  # simple
        log_format = "[%(levelname)s] %(name)s: %(message)s"

    # Configure root logger for litespeech
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stderr,
        force=True,
    )

    # Set level for litespeech namespace
    litespeech_logger = logging.getLogger("litespeech")
    litespeech_logger.setLevel(log_level)


# Auto-setup on import
setup_logging()
