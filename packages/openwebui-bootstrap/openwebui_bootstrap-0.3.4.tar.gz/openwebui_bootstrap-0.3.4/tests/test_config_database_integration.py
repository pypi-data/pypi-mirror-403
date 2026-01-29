"""Comprehensive database integration tests for configuration manager."""

import pytest

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.models import (
    OpenWebUIConfig,
    ConnectionConfig,
    UISettingsConfig,
    PermissionSystemConfig,
    ImageGenerationConfig,
)


def test_full_config_database_storage_and_retrieval(
    config_manager: ConfigManager, temp_db_path: str
):
    """Test that all configuration sections are properly stored and retrieved from database."""
    # Create a comprehensive test configuration
    test_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[
            {"name": "Test User 1", "email": "user1@test.com", "role": "Admin"},
            {"name": "Test User 2", "email": "user2@test.com", "role": "User"},
        ],
        groups=[
            {
                "name": "test_group",
                "description": "Test group",
                "permissions": ["import_models", "export_models"],
                "members": ["user1@test.com"],
            }
        ],
        connections=[
            ConnectionConfig(
                type="openai",
                url="https://api.openai.com/v1",
                bearer="test-token-1",
                model_prefix_id="openai",
                model_ids=["gpt-4", "gpt-3.5-turbo"],
                tags=["Online-Models"],
            ),
            ConnectionConfig(
                type="ollama",
                url="http://localhost:11434",
                bearer=None,
                model_prefix_id="ollama",
                model_ids=[],
                tags=["Local-Models"],
            ),
        ],
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {
                "gpt-4": {
                    "context_size": "8192",
                    "system_prompt": "test_prompt.txt",
                    "icon": "gpt_icon.png",
                    "capabilities": "image-recognition,file-upload,websearch",
                    "default_capabilities": "websearch,image-generation",
                }
            },
        },
        ui_settings=UISettingsConfig(
            enable_signup=False,
            default_locale="de",
            default_models=["gpt-4", "gpt-3.5-turbo"],
        ),
        permissions=PermissionSystemConfig(
            workspace={
                "models": True,
                "knowledge": False,
                "prompts": True,
                "tools": True,
                "models_import": True,
                "models_export": False,
            },
            chat={
                "controls": True,
                "file_upload": False,
                "delete": True,
                "edit": False,
            },
            features={
                "web_search": True,
                "image_generation": False,
                "code_interpreter": True,
            },
            sharing={"models": True, "public_models": False},
            settings={"interface": True},
        ),
        image_generation=ImageGenerationConfig(
            enable=True,
            engine="openai",
            model="dall-e-3",
            openai={
                "api_base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "size": "1024x1024",
                "steps": 50,
            },
            comfyui=None,
        ),
    )

    # Apply the config
    config_manager.set_dry_run(False)
    config_manager.apply_config(test_config)

    # Verify config was stored in database
    db = config_manager.database
    db.connect()
    config_data = db.get_config()
    db.disconnect()

    # Verify all sections are stored
    assert config_data is not None

    # Verify UI settings
    assert "ui" in config_data
    assert config_data["ui"]["enable_signup"] is False
    assert config_data["ui"]["default_locale"] == "de"
    assert len(config_data["ui"]["default_models"]) == 2

    # Verify permissions
    assert "user" in config_data
    assert "permissions" in config_data["user"]
    assert config_data["user"]["permissions"]["workspace"]["knowledge"] is False
    assert config_data["user"]["permissions"]["chat"]["file_upload"] is False
    assert config_data["user"]["permissions"]["features"]["image_generation"] is False

    # Verify image generation
    assert "image_generation" in config_data
    assert config_data["image_generation"]["enable"] is True
    assert config_data["image_generation"]["engine"] == "openai"
    assert config_data["image_generation"]["openai"]["size"] == "1024x1024"

    # Verify connections
    assert "connections" in config_data
    assert len(config_data["connections"]) == 2
    assert config_data["connections"][0]["type"] == "openai"
    assert config_data["connections"][1]["type"] == "ollama"

    # Verify users were created
    db.connect()
    user1 = db.get_user_by_email("user1@test.com")
    assert user1 is not None
    assert user1.name == "Test User 1"
    assert user1.role == "Admin"

    user2 = db.get_user_by_email("user2@test.com")
    assert user2 is not None
    assert user2.name == "Test User 2"
    assert user2.role == "User"

    # Verify groups were created
    group = db.get_group_by_name("test_group")
    assert group is not None
    assert group.description == "Test group"
    assert "import_models" in group.permissions

    # Verify models were created
    model = db.get_model_by_id("gpt-4")
    assert model is not None
    assert model.name == "gpt-4"
    assert model.params["context_size"] == 8192
    assert "vision" in model.meta["capabilities"]
    assert "web_search" in model.meta["default_capabilities"]
    db.disconnect()


def test_config_transaction_rollback_on_error(
    config_manager: ConfigManager, temp_db_path: str
):
    """Test that database transactions are properly rolled back on error."""
    # Create a test configuration
    test_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    )

    # Apply the config successfully
    config_manager.set_dry_run(False)
    config_manager.apply_config(test_config)

    # Verify user was created
    db = config_manager.database
    db.connect()
    user = db.get_user_by_email("test@example.com")
    assert user is not None
    db.disconnect()

    # Now test error handling by trying to apply invalid config
    # This should rollback and not affect existing data
    invalid_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    )

    # Apply again (should succeed)
    config_manager.apply_config(invalid_config)

    # Verify original user still exists
    db.connect()
    user = db.get_user_by_email("test@example.com")
    assert user is not None
    db.disconnect()


def test_config_with_empty_sections(config_manager: ConfigManager, temp_db_path: str):
    """Test configuration with empty sections."""
    # Create a minimal configuration with empty sections
    test_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    )

    # Apply the config
    config_manager.set_dry_run(False)
    config_manager.apply_config(test_config)

    # Verify config was stored in database
    db = config_manager.database
    db.connect()
    config_data = db.get_config()
    db.disconnect()

    assert config_data is not None
    assert "ui" in config_data
    assert "user" in config_data
    assert "image_generation" in config_data
    assert "connections" in config_data


def test_config_error_handling(config_manager: ConfigManager, temp_db_path: str):
    """Test error handling in config manager."""
    # Test with a config that has invalid model capability
    # This should fail during validation
    invalid_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {
                "test-model": {
                    "context_size": "invalid_size",  # Invalid - should be numeric
                    "system_prompt": "test_prompt.txt",
                    "icon": "test_icon.png",
                    "capabilities": "invalid-capability",  # Invalid capability
                    "default_capabilities": "websearch",
                }
            },
        },
    )

    # This should raise an error during model creation
    with pytest.raises(Exception):
        config_manager.apply_config(invalid_config)


def test_config_dry_run_mode(config_manager: ConfigManager, temp_db_path: str):
    """Test that dry run mode doesn't make database changes."""
    # Create a test configuration
    test_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    )

    # Apply in dry run mode
    config_manager.set_dry_run(True)
    config_manager.apply_config(test_config)

    # Verify no user was created
    db = config_manager.database
    db.connect()
    user = db.get_user_by_email("test@example.com")
    assert user is None
    db.disconnect()


def test_config_model_capability_parsing(
    config_manager: ConfigManager, temp_db_path: str
):
    """Test model capability parsing and storage."""
    # Create a test configuration with various capabilities
    test_config = OpenWebUIConfig(
        database={"type": "sqlite", "database_location": temp_db_path},
        users=[],
        groups=[],
        connections=ConnectionConfig(
            type="openai",
            url="https://api.example.com/v1",
            bearer="test-token",
            model_ids=[],
            tags=[],
        ),
        models={
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {
                "test-model": {
                    "context_size": "8192",
                    "system_prompt": "test_prompt.txt",
                    "icon": "test_icon.png",
                    "capabilities": "image-recognition,file-upload,file-context,websearch,image-generation,code-interpreter,usage-statistics,citations,status-updates,builtin-tools",
                    "default_capabilities": "websearch,image-generation,code-interpreter",
                }
            },
        },
    )

    # Apply the config
    config_manager.set_dry_run(False)
    config_manager.apply_config(test_config)

    # Verify model was created with correct capabilities
    db = config_manager.database
    db.connect()
    model = db.get_model_by_id("test-model")
    assert model is not None
    assert model.meta["capabilities"]["vision"] is True
    assert model.meta["capabilities"]["file_upload"] is True
    assert model.meta["capabilities"]["file_context"] is True
    assert model.meta["capabilities"]["web_search"] is True
    assert model.meta["capabilities"]["image_generation"] is True
    assert model.meta["capabilities"]["code_interpreter"] is True
    assert model.meta["capabilities"]["usage"] is True
    assert model.meta["capabilities"]["citations"] is True
    assert model.meta["capabilities"]["status_updates"] is True
    assert model.meta["capabilities"]["builtin_tools"] is True

    # Verify default capabilities
    assert model.meta["default_capabilities"]["web_search"] is True
    assert model.meta["default_capabilities"]["image_generation"] is True
    assert model.meta["default_capabilities"]["code_interpreter"] is True
    db.disconnect()
