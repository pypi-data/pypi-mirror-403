"""Tests for config manager edge cases and additional coverage."""

import os
import tempfile

import pytest
import yaml

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import (
    DatabaseError,
)


def test_config_manager_model_parsing() -> None:
    """Test model configuration parsing and entity creation."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a test configuration with model setup
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.example.com/v1",
            "bearer": "test-token",
            "model_ids": ["gpt-4", "gpt-3.5-turbo"],
            "tags": ["Online-Models"],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {
                "gpt-4": {
                    "context_size": "8192",
                    "system_prompt": "system_prompt.txt",
                    "icon": "gpt4_icon.png",
                    "capabilities": "image-recognition,file-upload,websearch",
                    "default_capabilities": "websearch,code-interpreter",
                },
                "gpt-3.5-turbo": {
                    "context_size": "4096",
                    "system_prompt": "chat_prompt.txt",
                    "icon": "gpt3_icon.png",
                },
            },
        },
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Load configuration
        config = config_manager.load_config(config_file)

        # Verify model configuration parsing
        assert len(config.models.model_setup) == 2
        assert "gpt-4" in config.models.model_setup
        assert "gpt-3.5-turbo" in config.models.model_setup

        # Test model entity creation (this would be called during apply)
        model_entity = config_manager._create_model_entity(
            "gpt-4", config.models.model_setup["gpt-4"], config
        )

        assert model_entity.id == "gpt-4"
        assert model_entity.name == "gpt-4"
        assert model_entity.params["context_size"] == 8192
        assert "vision" in model_entity.meta["capabilities"]
        assert "web_search" in model_entity.meta["default_capabilities"]

    finally:
        os.unlink(config_file)


def test_config_manager_group_operations() -> None:
    """Test group operations in config manager."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a test configuration with groups
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [
            {"name": "Admin User", "email": "admin@example.com", "role": "Admin"},
            {"name": "Regular User", "email": "user@example.com", "role": "User"},
        ],
        "groups": [
            {
                "name": "admins",
                "description": "Administrator group",
                "permissions": ["import_models", "export_models", "manage_users"],
                "members": ["admin@example.com"],
            },
            {
                "name": "users",
                "description": "Regular users group",
                "permissions": ["use_models"],
                "members": ["user@example.com", "admin@example.com"],
            },
        ],
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

        # Verify group configuration
        assert len(config.groups) == 2
        assert config.groups[0].name == "admins"
        assert len(config.groups[0].permissions) == 3
        assert len(config.groups[0].members) == 1

        # Test group entity creation
        group_entity = config_manager._create_group_entity(config.groups[0])
        assert group_entity.name == "admins"
        assert group_entity.description == "Administrator group"
        assert "import_models" in group_entity.permissions
        assert group_entity.permissions["import_models"] is True

        # Test permission conversion
        permissions = config_manager._convert_permissions(["test_perm1", "test_perm2"])
        assert permissions == {"test_perm1": True, "test_perm2": True}

    finally:
        os.unlink(config_file)


def test_config_manager_user_operations() -> None:
    """Test user operations in config manager."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a test configuration with users
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [
            {"name": "Admin User", "email": "admin@example.com", "role": "Admin"},
            {"name": "Regular User", "email": "user@example.com", "role": "User"},
            {"name": "Test User", "email": "test@example.com", "role": "User"},
        ],
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

        # Test user entity creation
        user_entity = config_manager._create_user_entity(config.users[0])
        assert user_entity.name == "Admin User"
        assert user_entity.email == "admin@example.com"
        assert user_entity.role == "Admin"
        assert user_entity.username == "admin"  # Email prefix

        # Test auth entity creation
        auth_entity = config_manager._create_auth_entity(
            config.users[0], user_entity.id
        )
        assert auth_entity.email == "admin@example.com"
        assert auth_entity.active is True
        assert len(auth_entity.password) == 64  # SHA256 hash length

    finally:
        os.unlink(config_file)


def test_config_manager_error_handling() -> None:
    """Test error handling in config manager."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))

    # Test error handling by trying to access non-existent table
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
        # Load configuration
        config = config_manager.load_config(config_file)

        # Apply configuration (should work)
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
        os.unlink(config_file)


def test_config_manager_dry_run_comprehensive() -> None:
    """Test dry run mode comprehensively."""
    config_manager = ConfigManager(SQLiteDatabase(":memory:"))
    config_manager.set_dry_run(True)

    # Create a comprehensive configuration
    config_data = {
        "database": {"type": "sqlite", "database_location": ":memory:"},
        "users": [
            {"name": "Admin User", "email": "admin@example.com", "role": "Admin"},
            {"name": "Regular User", "email": "user@example.com", "role": "User"},
        ],
        "groups": [
            {
                "name": "admins",
                "description": "Administrator group",
                "permissions": ["import_models"],
                "members": ["admin@example.com"],
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
                    "system_prompt": "system_prompt.txt",
                    "icon": "gpt4_icon.png",
                }
            },
        },
    }

    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        # Load and apply configuration in dry run mode
        config = config_manager.load_config(config_file)
        config_manager.apply_config(config)

        # In dry run mode, verify the config was parsed correctly
        assert len(config.users) == 2
        assert len(config.groups) == 1
        assert config.groups[0].name == "admins"
        assert len(config.models.model_setup) == 1

    finally:
        os.unlink(config_file)
