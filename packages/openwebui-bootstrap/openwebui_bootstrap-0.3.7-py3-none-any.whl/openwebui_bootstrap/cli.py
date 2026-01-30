"""Command-line interface for Open WebUI Bootstrap."""

import argparse
import sys

from .config_manager import ConfigManager
from .database.sqlite import SQLiteDatabase
from .exceptions import (
    ConfigurationError,
    OpenWebUIBootstrapError,
)
from .logging_config import setup_logging


def main():
    """Main entry point for the CLI tool."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Set up logging
        logger = setup_logging(args.log_level)

        logger.info("Starting Open WebUI Bootstrap")

        # Create database interface
        database = SQLiteDatabase(args.database_path)

        # Create configuration manager
        config_manager = ConfigManager(database)
        config_manager.set_dry_run(args.dry_run)

        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = config_manager.load_config(args.config)

        # Reset database if requested
        if args.reset:
            logger.info("Resetting database")
            config_manager.reset_database()

        # Apply configuration
        logger.info("Applying configuration")
        config_manager.apply_config(config, args.reset)

        logger.info("Open WebUI Bootstrap completed successfully")

    except OpenWebUIBootstrapError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Open WebUI Bootstrap - Configure Open WebUI database"
    )

    # Required arguments
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file",
    )

    # Optional arguments
    parser.add_argument(
        "--database-path",
        help="Path to SQLite database file (defaults to config database_location)",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database before applying configuration",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - test without making changes",
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set log level (default: info)",
    )

    args = parser.parse_args()

    # If database path not provided, use the one from config
    if not args.database_path:
        # We need to read the config to get the database path
        try:
            with open(args.config, encoding="utf-8") as f:
                import yaml

                config_data = yaml.safe_load(f)
                args.database_path = config_data["database"]["database_location"]
        except Exception as e:
            raise ConfigurationError(
                f"Could not determine database path: {e}. "
                "Please provide --database-path argument."
            )

    return args


if __name__ == "__main__":
    main()
