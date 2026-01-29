"""Tests for new configuration features in Open WebUI Bootstrap."""

import tempfile
import os
import pytest
from openwebui_bootstrap.models import (
    OpenWebUIConfig,
    UISettingsConfig,
    PermissionSystemConfig,
    ImageGenerationConfig,
    ConnectionConfig,
)
from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import ConfigurationValidationError
from pydantic import ValidationError


def test_ui_settings_config():
    """Test UI settings configuration model."""
    # Test default values
    ui_config = UISettingsConfig()
    assert ui_config.enable_signup is True
    assert ui_config.default_locale is None
    assert ui_config.default_models is None

    # Test custom values
    ui_config = UISettingsConfig(
        enable_signup=False, default_locale="de", default_models=["model1", "model2"]
    )
    assert ui_config.enable_signup is False
    assert ui_config.default_locale == "de"
    assert ui_config.default_models == ["model1", "model2"]


def test_permission_system_config():
    """Test permission system configuration model."""
    # Test default values
    perm_config = PermissionSystemConfig()
    assert perm_config.workspace["models"] is True
    assert perm_config.chat["controls"] is True
    assert perm_config.features["web_search"] is True
    assert perm_config.sharing["models"] is False
    assert perm_config.settings["interface"] is True


def test_image_generation_config():
    """Test image generation configuration model."""
    # Test default values
    img_config = ImageGenerationConfig()
    assert img_config.enable is True
    assert img_config.engine == "openai"
    assert img_config.model is None
    assert img_config.openai is None
    assert img_config.comfyui is None

    # Test custom values
    img_config = ImageGenerationConfig(
        enable=False,
        engine="comfyui",
        model="stable-diffusion-xl",
        openai={
            "api_base_url": "https://api.openai.com/v1",
            "api_key": "test-key",
            "size": "1024x1024",
        },
        comfyui={"base_url": "http://localhost:8188", "workflow": {"nodes": {}}},
    )
    assert img_config.enable is False
    assert img_config.engine == "comfyui"
    assert img_config.model == "stable-diffusion-xl"
    assert img_config.openai["api_base_url"] == "https://api.openai.com/v1"
    assert img_config.comfyui["base_url"] == "http://localhost:8188"


def test_connection_config_extended():
    """Test extended connection configuration."""
    # Test default values
    conn_config = ConnectionConfig(
        type="openai", url="https://api.openai.com/v1", bearer="test-token"
    )
    assert conn_config.enable is True
    assert conn_config.base_urls is None
    assert conn_config.api_keys is None

    # Test extended values
    conn_config = ConnectionConfig(
        type="openai",
        url="https://api.openai.com/v1",
        bearer="test-token",
        enable=True,
        base_urls=["https://api.openai.com/v1", "https://api.mistral.ai/v1"],
        api_keys=["key1", "key2"],
    )
    assert conn_config.enable is True
    assert conn_config.base_urls == [
        "https://api.openai.com/v1",
        "https://api.mistral.ai/v1",
    ]
    assert conn_config.api_keys == ["key1", "key2"]


def test_full_config_integration():
    """Test full configuration integration."""
    config_data = {
        "database": {"type": "sqlite", "database_location": "/tmp/test.db"},
        "users": [{"name": "Test User", "email": "test@example.com", "role": "Admin"}],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.openai.com/v1",
            "bearer": "test-token",
            "enable": True,
            "base_urls": ["https://api.openai.com/v1"],
            "api_keys": ["test-key"],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
        "ui_settings": {
            "enable_signup": False,
            "default_locale": "en",
            "default_models": ["gpt-4"],
        },
        "permissions": {
            "workspace": {"models": True, "knowledge": False},
            "chat": {"controls": True, "web_search": False},
            "features": {"image_generation": True},
            "sharing": {"models": False},
            "settings": {"interface": True},
        },
        "image_generation": {
            "enable": True,
            "engine": "openai",
            "model": "dall-e-3",
            "openai": {
                "api_base_url": "https://api.openai.com/v1",
                "size": "1024x1024",
            },
        },
    }

    # Test that the full config validates
    config = OpenWebUIConfig(**config_data)
    assert config.database.type == "sqlite"
    assert config.ui_settings.enable_signup is False
    assert config.permissions.workspace["knowledge"] is False
    assert config.image_generation.engine == "openai"


def test_config_manager_with_new_features():
    """Test config manager with new configuration features."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        # Create database and config manager
        database = SQLiteDatabase(db_path)
        config_manager = ConfigManager(database)

        # Create a test config with new features
        test_config = OpenWebUIConfig(
            database={"type": "sqlite", "database_location": db_path},
            users=[],
            groups=[],
            connections=ConnectionConfig(
                type="openai", url="https://api.openai.com/v1", bearer="test-token"
            ),
            models={
                "prompt_path": "/path/to/prompts",
                "icon_path": "/path/to/icons",
                "model_setup": {},
            },
            ui_settings=UISettingsConfig(enable_signup=False, default_locale="de"),
            permissions=PermissionSystemConfig(),
            image_generation=ImageGenerationConfig(enable=True, engine="comfyui"),
        )

        # Apply the config (this should work without errors)
        config_manager.set_dry_run(False)
        config_manager.apply_config(test_config)

        # Verify config was stored in database
        database.connect()
        config_data = database.get_config()
        database.disconnect()

        assert config_data is not None
        assert "ui" in config_data
        assert "user" in config_data
        assert "image_generation" in config_data
        assert config_data["ui"]["enable_signup"] is False
        assert config_data["ui"]["default_locale"] == "de"
        assert config_data["image_generation"]["engine"] == "comfyui"

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_config_validation_errors():
    """Test configuration validation errors."""
    # Test invalid permission structure
    with pytest.raises(ValidationError):
        PermissionSystemConfig(
            workspace="invalid"  # Should be dict
        )

    # Test invalid image generation configuration
    with pytest.raises(ValidationError):
        ImageGenerationConfig(
            enable="invalid"  # Should be boolean
        )


def test_yaml_config_loading():
    """Test loading configuration from YAML file."""
    config_yaml = """
database:
  type: sqlite
  database_location: /tmp/test.db

users: []

groups: []

connections:
  type: openai
  url: https://api.openai.com/v1
  bearer: test-token
  enable: true
  base_urls:
    - https://api.openai.com/v1
  api_keys:
    - test-key

models:
  prompt_path: /path/to/prompts
  icon_path: /path/to/icons
  model_setup: {}

ui_settings:
  enable_signup: false
  default_locale: en
  default_models:
    - gpt-4
    - gpt-3.5-turbo

permissions:
  workspace:
    models: true
    knowledge: false
  chat:
    controls: true
    web_search: true
  features:
    image_generation: true
    web_search: false
  sharing:
    models: false
  settings:
    interface: true

image_generation:
  enable: true
  engine: openai
  model: dall-e-3
  openai:
    api_base_url: https://api.openai.com/v1
    api_key: test-key
    size: 1024x1024
    steps: 50
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp_yaml:
        tmp_yaml.write(config_yaml)
        yaml_path = tmp_yaml.name

    try:
        config_manager = ConfigManager(SQLiteDatabase("/tmp/test.db"))
        config = config_manager.load_config(yaml_path)

        # Verify all sections are loaded correctly
        assert config.ui_settings.enable_signup is False
        assert config.ui_settings.default_locale == "en"
        assert len(config.ui_settings.default_models) == 2
        assert config.permissions.workspace["knowledge"] is False
        assert config.image_generation.engine == "openai"
        assert config.image_generation.openai["size"] == "1024x1024"

    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)
