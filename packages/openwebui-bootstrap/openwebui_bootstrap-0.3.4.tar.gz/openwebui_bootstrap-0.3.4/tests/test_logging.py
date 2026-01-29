"""Tests for logging configuration."""

import logging

from openwebui_bootstrap.logging_config import get_logger, setup_logging


def test_setup_logging_default() -> None:
    """Test setup_logging with default parameters."""
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "openwebui_bootstrap"
    assert logger.level == logging.INFO

    # Verify handler was added
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.INFO


def test_setup_logging_debug() -> None:
    """Test setup_logging with debug level."""
    logger = setup_logging("debug")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG

    # Verify handler was added
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.DEBUG


def test_setup_logging_warning() -> None:
    """Test setup_logging with warning level."""
    logger = setup_logging("warning")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.WARNING

    # Verify handler was added
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.WARNING


def test_setup_logging_error() -> None:
    """Test setup_logging with error level."""
    logger = setup_logging("error")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.ERROR

    # Verify handler was added
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.ERROR


def test_get_logger_default() -> None:
    """Test get_logger with default parameters."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "openwebui_bootstrap.logging_config"


def test_get_logger_custom_name() -> None:
    """Test get_logger with custom name."""
    logger = get_logger("custom_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "custom_logger"


def test_setup_logging_removes_existing_handlers() -> None:
    """Test that setup_logging removes existing handlers."""
    # Create a logger with existing handlers
    logger = logging.getLogger("openwebui_bootstrap")
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.StreamHandler())

    # Setup logging should remove existing handlers
    setup_logging()
    assert len(logger.handlers) == 1


def test_logging_output_format() -> None:
    """Test that logging output includes expected format elements."""
    logger = setup_logging("debug")

    # Test that logger has correct format by checking handler
    handler = logger.handlers[0]
    formatter = handler.formatter

    # Verify formatter has expected format
    assert hasattr(formatter, "_fmt")
    assert "%(asctime)s" in formatter._fmt
    assert "%(name)s" in formatter._fmt
    assert "%(levelname)s" in formatter._fmt
    assert "%(message)s" in formatter._fmt


def test_logging_color_formatting() -> None:
    """Test that logging uses color formatting."""
    logger = setup_logging("debug")

    # Get the handler and verify it uses color formatting
    handler = logger.handlers[0]
    formatter = handler.formatter
    assert hasattr(formatter, "log_colors")
    assert "INFO" in formatter.log_colors
    assert "ERROR" in formatter.log_colors
    assert "DEBUG" in formatter.log_colors
