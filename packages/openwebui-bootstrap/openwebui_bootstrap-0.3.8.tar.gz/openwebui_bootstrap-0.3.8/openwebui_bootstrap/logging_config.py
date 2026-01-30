"""Logging configuration for Open WebUI Bootstrap."""

import logging
import sys

import colorlog


def setup_logging(log_level: str = "info") -> logging.Logger:
    """Set up color-formatted logging with the specified log level.

    Args:
        log_level: Log level as string (debug, info, warning, error, critical)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("openwebui_bootstrap")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Create color formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (defaults to module name)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger(__name__)
