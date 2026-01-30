"""Open WebUI Bootstrap - A tool to bootstrap Open WebUI deployments."""

from .cli import main
from .config_manager import ConfigManager
from .database.base import DatabaseInterface
from .database.sqlite import SQLiteDatabase
from .exceptions import (
    ConfigurationError,
    ConfigurationFileError,
    ConfigurationValidationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationError,
    DatabaseTransactionError,
    DryRunError,
    OpenWebUIBootstrapError,
    ResetError,
    UpsertError,
)
from .logging_config import get_logger, setup_logging
from .models import (
    AuthEntity,
    ConnectionConfig,
    DatabaseConfig,
    GroupConfig,
    GroupEntity,
    GroupMemberEntity,
    ModelConfig,
    ModelEntity,
    OpenWebUIConfig,
    UserConfig,
    UserEntity,
)
from .utils import get_resource_path


def bootstrap_openwebui(
    config_path: str,
    database_path: str | None = None,
    reset: bool = False,
    dry_run: bool = False,
    log_level: str = "info",
) -> None:
    """Public API function to bootstrap Open WebUI configuration.

    This function provides the same functionality as the CLI tool but can be used
    programmatically from third-party applications.

    Args:
        config_path: Path to YAML configuration file
        database_path: Optional path to SQLite database file. If not provided,
                      will be read from the configuration file.
        reset: Whether to reset the database before applying configuration
        dry_run: Whether to run in dry run mode (test without making changes)
        log_level: Log level (debug, info, warning, error, critical)

    Raises:
        ConfigurationError: If configuration file cannot be read or parsed
        DatabaseError: If database operations fail
        OpenWebUIBootstrapError: For other errors

    Example:
        >>> from openwebui_bootstrap import bootstrap_openwebui
        >>> bootstrap_openwebui("config.yaml", reset=True, dry_run=False)
    """
    # Set up logging
    logger = setup_logging(log_level)
    logger.info("Starting Open WebUI Bootstrap via public API")

    # Create database interface
    database = SQLiteDatabase(database_path)

    # Create configuration manager
    config_manager = ConfigManager(database)
    config_manager.set_dry_run(dry_run)

    # Load configuration
    logger.info(f"Loading configuration from {config_path}")
    config = config_manager.load_config(config_path)

    # Reset database if requested
    if reset:
        logger.info("Resetting database")
        config_manager.reset_database()

    # Apply configuration
    logger.info("Applying configuration")
    config_manager.apply_config(config)

    logger.info("Open WebUI Bootstrap completed successfully")


def reset_database(database_path: str, dry_run: bool = False) -> None:
    """Reset the Open WebUI database by clearing all managed tables.

    Args:
        database_path: Path to SQLite database file
        dry_run: Whether to run in dry run mode (test without making changes)

    Raises:
        DatabaseError: If database operations fail
        DryRunError: If dry run mode is enabled

    Example:
        >>> from openwebui_bootstrap import reset_database
        >>> reset_database("/path/to/webui.db", dry_run=False)
    """
    logger = setup_logging("info")
    logger.info("Resetting database via public API")

    database = SQLiteDatabase(database_path)
    config_manager = ConfigManager(database)
    config_manager.set_dry_run(dry_run)
    config_manager.reset_database()

    logger.info("Database reset completed successfully")


def load_config(config_path: str) -> OpenWebUIConfig:
    """Load and validate Open WebUI configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Parsed and validated OpenWebUIConfig object

    Raises:
        ConfigurationFileError: If configuration file cannot be read or parsed
        ConfigurationValidationError: If configuration is invalid

    Example:
        >>> from openwebui_bootstrap import load_config
        >>> config = load_config("config.yaml")
    """
    logger = setup_logging("info")
    logger.info(f"Loading configuration from {config_path}")

    database = SQLiteDatabase(None)  # Dummy database for config loading
    config_manager = ConfigManager(database)
    return config_manager.load_config(config_path)


def apply_config(
    config: OpenWebUIConfig, database_path: str, dry_run: bool = False
) -> None:
    """Apply Open WebUI configuration to the database.

    Args:
        config: OpenWebUIConfig object to apply
        database_path: Path to SQLite database file
        dry_run: Whether to run in dry run mode (test without making changes)

    Raises:
        DatabaseError: If database operations fail
        DryRunError: If dry run mode is enabled
        ConfigurationError: If database_path is None or empty

    Example:
        >>> from openwebui_bootstrap import apply_config, load_config
        >>> config = load_config("config.yaml")
        >>> apply_config(config, "/path/to/webui.db", dry_run=False)
    """
    logger = setup_logging("info")
    logger.info("Applying configuration via public API")

    # Validate database_path is not None or empty
    if database_path is None:
        logger.error("Database path cannot be None")
        raise ConfigurationError("Database path cannot be None")
    if not database_path or not isinstance(database_path, str):
        logger.error("Database path must be a non-empty string")
        raise ConfigurationError("Database path must be a non-empty string")

    logger.info(f"Using database path: {database_path}")

    database = SQLiteDatabase(database_path)
    config_manager = ConfigManager(database)
    config_manager.set_dry_run(dry_run)
    config_manager.apply_config(config)

    logger.info("Configuration applied successfully")


__version__ = "0.3.9"
__all__ = [
    "main",
    "ConfigManager",
    "DatabaseInterface",
    "SQLiteDatabase",
    "OpenWebUIBootstrapError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseOperationError",
    "DatabaseTransactionError",
    "ConfigurationError",
    "ConfigurationFileError",
    "ConfigurationValidationError",
    "ResetError",
    "UpsertError",
    "DryRunError",
    "setup_logging",
    "get_logger",
    "OpenWebUIConfig",
    "DatabaseConfig",
    "UserConfig",
    "GroupConfig",
    "ConnectionConfig",
    "ModelConfig",
    "UserEntity",
    "AuthEntity",
    "GroupEntity",
    "GroupMemberEntity",
    "ModelEntity",
    # Public API functions
    "bootstrap_openwebui",
    "reset_database",
    "load_config",
    "apply_config",
    "get_resource_path",
]
