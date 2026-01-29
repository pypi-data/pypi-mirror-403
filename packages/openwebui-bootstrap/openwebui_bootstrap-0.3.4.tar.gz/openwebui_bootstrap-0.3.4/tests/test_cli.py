"""Tests for CLI functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml

from openwebui_bootstrap.cli import main, parse_arguments


def test_parse_arguments_valid() -> None:
    """Test parsing valid command line arguments."""
    with patch(
        "sys.argv",
        [
            "openwebui-bootstrap",
            "--config",
            "test.yaml",
            "--database-path",
            "/test/path.db",
            "--log-level",
            "debug",
        ],
    ):
        args = parse_arguments()
        assert args.config == "test.yaml"
        assert args.database_path == "/test/path.db"
        assert args.log_level == "debug"
        assert args.reset is False
        assert args.dry_run is False


def test_parse_arguments_with_reset() -> None:
    """Test parsing arguments with reset flag."""
    with patch(
        "sys.argv",
        [
            "openwebui-bootstrap",
            "--config",
            "test.yaml",
            "--database-path",
            "/test/path.db",
            "--reset",
            "--dry-run",
        ],
    ):
        args = parse_arguments()
        assert args.config == "test.yaml"
        assert args.database_path == "/test/path.db"
        assert args.reset is True
        assert args.dry_run is True
        assert args.log_level == "info"  # default


def test_parse_arguments_missing_config() -> None:
    """Test parsing arguments with missing required config."""
    with patch("sys.argv", ["openwebui-bootstrap"]):
        with pytest.raises(SystemExit):
            parse_arguments()


def test_parse_arguments_with_database_path() -> None:
    """Test parsing arguments with explicit database path."""
    with patch(
        "sys.argv",
        [
            "openwebui-bootstrap",
            "--config",
            "test.yaml",
            "--database-path",
            "/custom/path.db",
        ],
    ):
        args = parse_arguments()
        assert args.config == "test.yaml"
        assert args.database_path == "/custom/path.db"


def test_main_with_valid_config(temp_db_path: str) -> None:
    """Test main function with valid configuration."""
    # Create a valid configuration
    config_data = {
        "database": {"type": "sqlite", "database_location": temp_db_path},
        "users": [{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.example.com/v1",
            "bearer": "test-token",
            "model_ids": [],
            "tags": [],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Test main function
        with patch(
            "sys.argv",
            ["openwebui-bootstrap", "--config", config_file, "--log-level", "error"],
        ):
            # Mock the logger to avoid output during tests
            with patch("openwebui_bootstrap.cli.setup_logging") as mock_logging:
                mock_logger = MagicMock()
                mock_logging.return_value = mock_logger

                # Run main - should complete without errors
                main()

                # Verify logging was called
                mock_logging.assert_called_once_with("error")

    finally:
        # Clean up
        os.unlink(config_file)


def test_main_with_reset(temp_db_path: str) -> None:
    """Test main function with reset flag."""
    # Create a valid configuration
    config_data = {
        "database": {"type": "sqlite", "database_location": temp_db_path},
        "users": [{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.example.com/v1",
            "bearer": "test-token",
            "model_ids": [],
            "tags": [],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Test main function with reset
        with patch(
            "sys.argv",
            ["openwebui-bootstrap", "--config", config_file, "--reset", "--dry-run"],
        ):
            # Mock the logger to avoid output during tests
            with patch("openwebui_bootstrap.cli.setup_logging") as mock_logging:
                mock_logger = MagicMock()
                mock_logging.return_value = mock_logger

                # Run main - should complete without errors
                main()

                # Verify logging was called
                mock_logging.assert_called_once_with("info")  # default log level

    finally:
        # Clean up
        os.unlink(config_file)


def test_main_with_invalid_config() -> None:
    """Test main function with invalid configuration."""
    # Create an invalid configuration
    config_data = {
        "database": {
            "type": "sqlite"
            # Missing database_location
        }
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Test main function with invalid config
        with patch("sys.argv", ["openwebui-bootstrap", "--config", config_file]):
            # Mock the logger to avoid output during tests
            with patch("openwebui_bootstrap.cli.setup_logging") as mock_logging:
                mock_logger = MagicMock()
                mock_logging.return_value = mock_logger

                # Should raise SystemExit due to invalid config
                with pytest.raises(SystemExit):
                    main()

    finally:
        # Clean up
        os.unlink(config_file)


def test_main_with_nonexistent_config() -> None:
    """Test main function with non-existent configuration file."""
    with patch(
        "sys.argv", ["openwebui-bootstrap", "--config", "/nonexistent/config.yaml"]
    ):
        # Mock the logger to avoid output during tests
        with patch("openwebui_bootstrap.cli.setup_logging") as mock_logging:
            mock_logger = MagicMock()
            mock_logging.return_value = mock_logger

            # Should raise SystemExit due to missing file
            with pytest.raises(SystemExit):
                main()
