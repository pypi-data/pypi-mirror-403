"""Extended tests for logging configuration to improve coverage."""

import io
import logging
from unittest.mock import MagicMock, patch  # noqa: F401

import pytest  # noqa: F401

from openwebui_bootstrap.logging_config import get_logger, setup_logging


def test_setup_logging_critical() -> None:
    """Test setup_logging with critical log level."""
    logger = setup_logging("critical")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "openwebui_bootstrap"
    assert logger.level == logging.CRITICAL

    # Verify handler was added
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.CRITICAL


def test_setup_logging_multiple_calls() -> None:
    """Test that multiple calls to setup_logging work correctly."""
    # First call
    logger1 = setup_logging("debug")
    assert logger1.level == logging.DEBUG
    assert len(logger1.handlers) == 1

    # Second call should replace handlers
    logger2 = setup_logging("info")
    assert logger2.level == logging.INFO
    assert len(logger2.handlers) == 1

    # Both should reference the same logger
    assert logger1 is logger2


def test_get_logger_none_name() -> None:
    """Test get_logger with None name."""
    logger = get_logger(None)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "openwebui_bootstrap.logging_config"


def test_get_logger_same_name() -> None:
    """Test that get_logger returns the same logger for the same name."""
    logger1 = get_logger("test_logger")
    logger2 = get_logger("test_logger")
    assert logger1 is logger2


def test_setup_logging_handler_properties() -> None:
    """Test that handler has correct properties."""
    logger = setup_logging("info")

    # Get the handler
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)

    # Check formatter
    formatter = handler.formatter
    assert formatter is not None

    # Check log colors
    assert hasattr(formatter, "log_colors")
    expected_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }
    for level, color in expected_colors.items():
        assert level in formatter.log_colors
        assert formatter.log_colors[level] == color


def test_setup_logging_format_string() -> None:
    """Test that format string contains expected elements."""
    logger = setup_logging("info")

    # Get the handler and formatter
    handler = logger.handlers[0]
    formatter = handler.formatter

    # Check format string
    assert hasattr(formatter, "_fmt")
    format_str = formatter._fmt

    # Verify all expected elements are in the format
    assert "%(log_color)s" in format_str
    assert "%(asctime)s" in format_str
    assert "%(name)s" in format_str
    assert "%(levelname)s" in format_str
    assert "%(message)s" in format_str


def test_setup_logging_with_patched_stream() -> None:
    """Test setup_logging with mocked stream."""
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        logger = setup_logging("info")
        logger.info("Test message")

        # Verify message was written to stdout
        output = mock_stdout.getvalue()
        assert "Test message" in output
        assert "INFO" in output


def test_get_logger_with_different_names() -> None:
    """Test get_logger with various different names."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module1")  # Same as logger1

    assert logger1.name == "module1"
    assert logger2.name == "module2"
    assert logger3.name == "module1"
    assert logger1 is logger3  # Same logger instance
    assert logger1 is not logger2  # Different logger instances


def test_setup_logging_removes_all_handlers() -> None:
    """Test that setup_logging removes ALL existing handlers."""
    # Create a logger with multiple handlers
    logger = logging.getLogger("openwebui_bootstrap")
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler("/tmp/test.log"))
    logger.addHandler(logging.NullHandler())

    # Setup logging should remove all handlers
    setup_logging("info")
    assert len(logger.handlers) == 1  # Only the new handler should remain


def test_setup_logging_preserves_logger_name() -> None:
    """Test that setup_logging preserves the logger name."""
    logger = setup_logging("info")
    assert logger.name == "openwebui_bootstrap"

    # Call again
    logger2 = setup_logging("debug")
    assert logger2.name == "openwebui_bootstrap"
    assert logger is logger2  # Same logger instance


def test_get_logger_returns_root_logger() -> None:
    """Test that get_logger returns the root logger when appropriate."""
    # Get the root logger
    root_logger = logging.getLogger()
    assert isinstance(root_logger, logging.Logger)

    # Get logger without name should return module logger
    module_logger = get_logger()
    assert module_logger.name == "openwebui_bootstrap.logging_config"


def test_setup_logging_with_uppercase_level() -> None:
    """Test setup_logging with uppercase log level."""
    logger = setup_logging("INFO")
    assert logger.level == logging.INFO

    logger = setup_logging("DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logging_with_mixed_case_level() -> None:
    """Test setup_logging with mixed case log level."""
    logger = setup_logging("InFo")
    assert logger.level == logging.INFO

    logger = setup_logging("DeBuG")
    assert logger.level == logging.DEBUG
