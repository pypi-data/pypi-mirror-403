"""Final coverage tests to reach 85%+ target."""

import os
import tempfile
import time
from uuid import uuid4

import yaml

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.models import (
    UserEntity,
)


def test_config_manager_connection_parsing() -> None:
    """Test connection configuration parsing."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a test configuration with connections
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.example.com/v1",
            "bearer": "test-token",
            "model_ids": ["gpt-4", "gpt-3.5-turbo"],
            "tags": ["Online-Models", "Production"],
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
        # Load configuration
        config = config_manager.load_config(config_file)

        # Verify connection configuration parsing
        # connections is now always a list (normalized by validator)
        assert isinstance(config.connections, list)
        assert len(config.connections) == 1
        assert config.connections[0].type == "openai"
        assert config.connections[0].url == "https://api.example.com/v1"
        assert config.connections[0].bearer == "test-token"
        assert len(config.connections[0].model_ids) == 2
        assert len(config.connections[0].tags) == 2
        assert "Online-Models" in config.connections[0].tags

    finally:
        os.unlink(config_file)


def test_config_manager_empty_config() -> None:
    """Test config manager with minimal configuration."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a minimal configuration
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [],
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
        # Load and apply configuration
        config = config_manager.load_config(config_file)
        config_manager.apply_config(config)

        # Verify empty configurations were handled
        assert len(config.users) == 0
        assert len(config.groups) == 0
        assert len(config.models.model_setup) == 0

    finally:
        os.unlink(config_file)


def test_database_upsert_operations_with_existing_data(
    sqlite_database: SQLiteDatabase,
) -> None:
    """Test upsert operations with existing data."""
    # Create initial user
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        api_key=None,
        settings=None,
        info=None,
        oauth_sub=None,
    )
    sqlite_database.upsert_user(user)

    # Update the same user (upsert)
    user.name = "Updated Test User"
    user.role = "Admin"
    sqlite_database.upsert_user(user)

    # Verify update worked
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user.name == "Updated Test User"
    assert retrieved_user.role == "Admin"
    assert retrieved_user.id == user_id  # Same ID


def test_database_transaction_rollback(sqlite_database: SQLiteDatabase) -> None:
    """Test database transaction rollback."""
    # Start a transaction
    sqlite_database.begin_transaction()

    # Insert some data
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="rollback_test",
        name="Rollback Test User",
        email="rollback@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        api_key=None,
        settings=None,
        info=None,
        oauth_sub=None,
    )
    sqlite_database.upsert_user(user)

    # Verify data was inserted
    assert sqlite_database.get_user_by_email("rollback@example.com") is not None

    # Rollback the transaction
    sqlite_database.rollback_transaction()

    # Verify data was rolled back
    assert sqlite_database.get_user_by_email("rollback@example.com") is None
