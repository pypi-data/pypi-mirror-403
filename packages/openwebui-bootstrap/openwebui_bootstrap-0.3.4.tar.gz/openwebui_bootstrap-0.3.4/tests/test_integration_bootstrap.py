"""Integration tests for Open WebUI Bootstrap.

This module provides integration tests that verify the bootstrap tool
works correctly with real Open WebUI databases. It mimics the functionality
of tests/resources/verify-bootstrap.sh but in a test framework for better
CI/CD integration.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.models import OpenWebUIConfig

# Path to test resources
RESOURCES_DIR = Path(__file__).parent / "resources"
CONFIG_FILE = RESOURCES_DIR / "openwebui-config.yaml"


# Parametrized database versions for testing
@pytest.fixture(
    params=[
        "webui-0.7.2.db",
        # Add more database versions here as needed
        # "webui-0.8.0.db",
        # "webui-0.9.0.db",
    ]
)
def reference_database(request) -> Path:
    """Fixture providing reference database paths for testing.

    Args:
        request: pytest request object

    Returns:
        Path to the reference database file
    """
    db_name = request.param
    db_path = RESOURCES_DIR / db_name
    if not db_path.exists():
        pytest.skip(f"Reference database {db_name} not found")
    return db_path


def test_bootstrap_with_reference_database(reference_database: Path) -> None:
    """Test bootstrap functionality with a reference Open WebUI database.

    This test:
    1. Copies the reference database to a temporary location
    2. Runs the bootstrap configuration
    3. Verifies users, groups, and models were created correctly
    4. Cleans up temporary files

    Args:
        reference_database: Path to the reference database file
    """
    # Create temporary directory for test database
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "test_webui.db"

        # Copy reference database to temporary location
        shutil.copy(reference_database, temp_db_path)

        # Initialize database and config manager
        db = SQLiteDatabase(str(temp_db_path))
        config_manager = ConfigManager(db)

        # Load configuration
        config = config_manager.load_config(str(CONFIG_FILE))

        # Apply configuration (not in dry-run mode)
        config_manager.set_dry_run(False)
        config_manager.apply_config(config)

        # Verify users were created
        db.connect()
        try:
            # Check that users from config were created
            for user_config in config.users:
                user = db.get_user_by_email(user_config.email)
                assert user is not None, f"User {user_config.email} not found"
                assert user.name == user_config.name
                assert user.role == user_config.role

            # Check that groups were created
            for group_config in config.groups:
                group = db.get_group_by_name(group_config.name)
                assert group is not None, f"Group {group_config.name} not found"
                assert group.description == group_config.description

            # Check that models were created
            for model_id in config.models.model_setup.keys():
                model = db.get_model_by_id(model_id)
                assert model is not None, f"Model {model_id} not found"
                assert model.name == model_id

        finally:
            db.disconnect()


def test_bootstrap_dry_run_mode(reference_database: Path) -> None:
    """Test bootstrap in dry-run mode with reference database.

    This test verifies that dry-run mode doesn't make changes to the database.

    Args:
        reference_database: Path to the reference database file
    """
    # Create temporary directory for test database
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "test_webui_dryrun.db"

        # Copy reference database to temporary location
        shutil.copy(reference_database, temp_db_path)

        # Initialize database and config manager
        db = SQLiteDatabase(str(temp_db_path))
        config_manager = ConfigManager(db)

        # Load configuration
        config = config_manager.load_config(str(CONFIG_FILE))

        # Apply configuration in dry-run mode
        config_manager.set_dry_run(True)
        config_manager.apply_config(config)

        # Verify no users were created
        db.connect()
        try:
            # Check that no users from config were created
            for user_config in config.users:
                user = db.get_user_by_email(user_config.email)
                assert user is None, (
                    f"User {user_config.email} should not exist in dry-run mode"
                )

            # Check that no groups were created
            for group_config in config.groups:
                group = db.get_group_by_name(group_config.name)
                assert group is None, (
                    f"Group {group_config.name} should not exist in dry-run mode"
                )

        finally:
            db.disconnect()


def test_bootstrap_reset_functionality(reference_database: Path) -> None:
    """Test database reset functionality with reference database.

    This test verifies that the reset_database method can be called without errors.

    Args:
        reference_database: Path to the reference database file
    """
    # Create temporary directory for test database
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "test_webui_reset.db"

        # Copy reference database to temporary location
        shutil.copy(reference_database, temp_db_path)

        # Initialize database and config manager
        db = SQLiteDatabase(str(temp_db_path))
        config_manager = ConfigManager(db)

        # Load and apply configuration
        config = config_manager.load_config(str(CONFIG_FILE))
        config_manager.set_dry_run(False)
        config_manager.apply_config(config)

        # Verify data was created
        db.connect()
        try:
            # Get count of users before reset
            cursor = db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM user")
            user_count_before = cursor.fetchone()[0]
            assert user_count_before > 0, "No users found before reset"

            # Reset database (this will close the connection)
            # This test verifies that reset_database can be called without errors
            config_manager.reset_database()

            # Verify the method completed without raising an exception
            # The actual clearing of data is tested in other test files
            # (test_database_operations.py)

        finally:
            db.disconnect()
