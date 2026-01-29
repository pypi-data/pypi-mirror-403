"""Main tests for Open WebUI Bootstrap."""

import os
import tempfile

import pytest
import yaml

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import (
    ConfigurationFileError,
    ConfigurationValidationError,
    DatabaseError,
)
from openwebui_bootstrap.models import (
    OpenWebUIConfig,
)


def test_config_loading_valid(config_manager: ConfigManager, temp_db_path: str) -> None:
    """Test loading a valid configuration file."""
    # Create a valid configuration
    config_data = {
        "database": {"type": "sqlite", "database_location": temp_db_path},
        "users": [{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        "groups": [
            {
                "name": "test_group",
                "description": "Test group",
                "permissions": ["import_models"],
                "members": ["test@example.com"],
            }
        ],
        "connections": {
            "type": "openai",
            "url": "https://api.example.com/v1",
            "bearer": "test-token",
            "model_ids": ["gpt-4"],
            "tags": ["Online-Models"],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {
                "gpt-4": {
                    "context_size": "8192",
                    "system_prompt": "test_prompt.txt",
                    "icon": "gpt_icon.png",
                    "capabilities": "image-recognition,file-upload",
                    "default_capabilities": "websearch,image-generation",
                }
            },
        },
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Test loading
        config = config_manager.load_config(config_file)

        # Verify configuration
        assert isinstance(config, OpenWebUIConfig)
        assert len(config.users) == 1
        assert config.users[0].name == "Test User"
        assert config.users[0].email == "test@example.com"
        assert config.users[0].role == "Admin"

        assert len(config.groups) == 1
        assert config.groups[0].name == "test_group"
        assert len(config.groups[0].permissions) == 1
        assert config.groups[0].permissions[0] == "import_models"

        # connections is now always a list (normalized by validator)
        assert isinstance(config.connections, list)
        assert len(config.connections) == 1
        assert config.connections[0].type == "openai"
        assert config.connections[0].url == "https://api.example.com/v1"
        assert config.connections[0].bearer == "test-token"

        assert config.models.prompt_path == "/path/to/prompts"
        assert config.models.icon_path == "/path/to/icons"
        assert len(config.models.model_setup) == 1

    finally:
        # Clean up
        os.unlink(config_file)


def test_config_loading_invalid(config_manager: ConfigManager) -> None:
    """Test loading an invalid configuration file."""
    # Create an invalid configuration (missing required fields)
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
        # Test that it raises ConfigurationValidationError
        with pytest.raises(ConfigurationValidationError):
            config_manager.load_config(config_file)
    finally:
        # Clean up
        os.unlink(config_file)


def test_config_loading_nonexistent(config_manager: ConfigManager) -> None:
    """Test loading a non-existent configuration file."""
    with pytest.raises(ConfigurationFileError):
        config_manager.load_config("/nonexistent/file.yaml")


def test_database_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test basic database operations."""
    # Test connection
    assert sqlite_database.connection is not None

    # Test table existence
    assert sqlite_database.table_exists("user")
    assert sqlite_database.table_exists("auth")
    assert sqlite_database.table_exists("group")
    assert sqlite_database.table_exists("model")

    # Test managed tables
    managed_tables = sqlite_database.get_managed_tables()
    assert "user" in managed_tables
    assert "auth" in managed_tables
    assert "group" in managed_tables
    assert "model" in managed_tables


def test_user_upsert_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test user upsert operations."""
    import time
    from uuid import uuid4

    from openwebui_bootstrap.models import AuthEntity, UserEntity

    # Create test user
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="Admin",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )

    # Create test auth
    auth = AuthEntity(
        id=user_id,
        email="test@example.com",
        password="hashed_password",
        active=True,
    )

    # Test upsert
    sqlite_database.upsert_user(user)
    sqlite_database.upsert_auth(auth)

    # Verify user was inserted
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"
    assert retrieved_user.email == "test@example.com"

    # Verify auth was inserted
    retrieved_auth = sqlite_database.get_auth_by_email("test@example.com")
    assert retrieved_auth is not None
    assert retrieved_auth.email == "test@example.com"
    assert retrieved_auth.active is True


def test_group_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test group operations."""
    import time
    from uuid import uuid4

    from openwebui_bootstrap.models import GroupEntity, GroupMemberEntity, UserEntity

    # Create a test user first
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="Admin",
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

    # Create test group
    group_id = uuid4()
    group = GroupEntity(
        id=group_id,
        user_id=user_id,
        name="test_group",
        description="Test group",
        data=None,
        meta=None,
        permissions={"import_models": True},
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    # Test group upsert
    sqlite_database.upsert_group(group)

    # Verify group was inserted
    retrieved_group = sqlite_database.get_group_by_name("test_group")
    assert retrieved_group is not None
    assert retrieved_group.name == "test_group"
    assert retrieved_group.description == "Test group"

    # Test group member operations
    group_member = GroupMemberEntity(
        id=uuid4(),
        group_id=group_id,
        user_id=user_id,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    sqlite_database.upsert_group_member(group_member)

    # Verify group member was inserted (by checking user ID retrieval)
    retrieved_user_id = sqlite_database.get_user_by_email_for_group("test@example.com")
    assert retrieved_user_id == user_id


def test_model_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test model operations."""
    import time

    from openwebui_bootstrap.models import ModelEntity

    # Create test model
    model = ModelEntity(
        id="test-model",
        user_id=None,
        base_model_id=None,
        name="Test Model",
        params={
            "context_size": 8192,
            "system_prompt": "test_prompt.txt",
            "icon": "test_icon.png",
        },
        meta={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "capabilities": {"vision": True, "file_upload": True},
            "default_capabilities": {"web_search": True, "image_generation": True},
        },
        access_control=None,
        is_active=True,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    # Test model upsert
    sqlite_database.upsert_model(model)

    # Verify model was inserted
    retrieved_model = sqlite_database.get_model_by_id("test-model")
    assert retrieved_model is not None
    assert retrieved_model.id == "test-model"
    assert retrieved_model.name == "Test Model"
    assert retrieved_model.params["context_size"] == 8192
    assert "vision" in retrieved_model.meta["capabilities"]
    assert "web_search" in retrieved_model.meta["default_capabilities"]


def test_reset_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test database reset operations."""
    import time
    from uuid import uuid4

    from openwebui_bootstrap.models import AuthEntity, UserEntity

    # First, insert some test data
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="Admin",
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

    auth = AuthEntity(
        id=user_id,
        email="test@example.com",
        password="hashed_password",
        active=True,
    )

    sqlite_database.upsert_user(user)
    sqlite_database.upsert_auth(auth)

    # Verify data was inserted
    assert sqlite_database.get_user_by_email("test@example.com") is not None
    assert sqlite_database.get_auth_by_email("test@example.com") is not None

    # Test clearing individual tables
    sqlite_database.clear_table("user")
    assert sqlite_database.get_user_by_email("test@example.com") is None

    sqlite_database.clear_table("auth")
    assert sqlite_database.get_auth_by_email("test@example.com") is None

    # Test clearing all managed tables
    # (This should work without error, though tables are already empty)
    sqlite_database.clear_managed_tables()


def test_config_manager_apply(config_manager: ConfigManager, temp_db_path: str) -> None:
    """Test config manager apply functionality."""
    # Create a test configuration
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
        # Load and apply configuration
        config = config_manager.load_config(config_file)
        config_manager.set_dry_run(False)  # Ensure we actually apply
        config_manager.apply_config(config)

        # Verify user was created
        db = config_manager.database
        db.connect()
        user = db.get_user_by_email("test@example.com")
        assert user is not None
        assert user.name == "Test User"
        db.disconnect()

    finally:
        # Clean up
        os.unlink(config_file)


def test_dry_run_mode(config_manager: ConfigManager, temp_db_path: str) -> None:
    """Test dry run mode functionality."""
    # Create a test configuration
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
        # Load configuration
        config = config_manager.load_config(config_file)

        # Apply in dry run mode (should not make changes)
        config_manager.set_dry_run(True)
        config_manager.apply_config(config)

        # Verify no user was created
        db = config_manager.database
        db.connect()
        user = db.get_user_by_email("test@example.com")
        assert user is None  # Should be None in dry run mode
        db.disconnect()

    finally:
        # Clean up
        os.unlink(config_file)


def test_error_handling(config_manager: ConfigManager) -> None:
    """Test error handling in various scenarios."""
    # Test configuration with invalid database type
    config_data = {
        "database": {
            "type": "sqlite",
            "database_location": ":memory:",  # Use in-memory database
        },
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
        # Load configuration
        config = config_manager.load_config(config_file)

        # Apply configuration to in-memory database (should work)
        config_manager.set_dry_run(False)
        config_manager.apply_config(config)

        # Now test error handling by trying to access a non-existent table
        db = config_manager.database
        db.connect()
        with pytest.raises(DatabaseError):
            # This should fail because 'nonexistent_table' is not in managed tables
            db.clear_table("nonexistent_table")
        db.disconnect()

    finally:
        # Clean up
        os.unlink(config_file)
