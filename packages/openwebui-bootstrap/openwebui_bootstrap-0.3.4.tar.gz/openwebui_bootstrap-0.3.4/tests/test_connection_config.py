"""Tests for connection configuration handling in Open WebUI Bootstrap."""

import tempfile
import os
import pytest
import yaml
from openwebui_bootstrap.models import (
    OpenWebUIConfig,
    ConnectionConfig,
)
from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import ConfigurationValidationError


def test_single_connection_config():
    """Test single connection configuration."""
    # Test with single ConnectionConfig
    config_data = {
        "database": {"type": "sqlite", "database_location": "/tmp/test.db"},
        "users": [],
        "groups": [],
        "connections": {
            "type": "openai",
            "url": "https://api.openai.com/v1",
            "bearer": "test-token",
            "model_prefix_id": "openai",
            "model_ids": ["gpt-4", "gpt-3.5-turbo"],
            "tags": ["Online-Models"],
        },
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    }

    # Should validate successfully
    config = OpenWebUIConfig(**config_data)
    assert isinstance(config.connections, list)
    assert len(config.connections) == 1
    assert config.connections[0].type == "openai"
    assert config.connections[0].url == "https://api.openai.com/v1"


def test_multiple_connections_config():
    """Test multiple connection configuration (list format)."""
    config_data = {
        "database": {"type": "sqlite", "database_location": "/tmp/test.db"},
        "users": [],
        "groups": [],
        "connections": [
            {
                "type": "openai",
                "url": "https://api.openai.com/v1",
                "bearer": "test-token",
                "model_prefix_id": "openai",
                "model_ids": ["gpt-4"],
                "tags": ["Online-Models"],
            },
            {
                "type": "ollama",
                "url": "http://localhost:11434",
                "bearer": None,
                "model_prefix_id": "ollama",
                "model_ids": [],
                "tags": ["Local-Models"],
            },
        ],
        "models": {
            "prompt_path": "/path/to/prompts",
            "icon_path": "/path/to/icons",
            "model_setup": {},
        },
    }

    # Should validate successfully
    config = OpenWebUIConfig(**config_data)
    assert isinstance(config.connections, list)
    assert len(config.connections) == 2
    assert config.connections[0].type == "openai"
    assert config.connections[1].type == "ollama"


def test_connection_validation_errors():
    """Test connection configuration validation errors."""
    from pydantic import ValidationError

    # Test invalid connection type (not a dict or list)
    with pytest.raises(ValidationError) as exc_info:
        config_data = {
            "database": {"type": "sqlite", "database_location": "/tmp/test.db"},
            "users": [],
            "groups": [],
            "connections": "invalid-string",
            "models": {
                "prompt_path": "/path/to/prompts",
                "icon_path": "/path/to/icons",
                "model_setup": {},
            },
        }
        OpenWebUIConfig(**config_data)

    # Pydantic validates before our custom validator, so we get standard validation errors
    assert "Input should be a valid dictionary" in str(exc_info.value)
    assert "Input should be a valid list" in str(exc_info.value)

    # Test list with invalid items
    with pytest.raises(ValidationError) as exc_info:
        config_data = {
            "database": {"type": "sqlite", "database_location": "/tmp/test.db"},
            "users": [],
            "groups": [],
            "connections": [
                {
                    "type": "openai",
                    "url": "https://api.openai.com/v1",
                },
                "invalid-item",
            ],
            "models": {
                "prompt_path": "/path/to/prompts",
                "icon_path": "/path/to/icons",
                "model_setup": {},
            },
        }
        OpenWebUIConfig(**config_data)

    # Pydantic validates list items before our custom validator
    assert "Input should be a valid dictionary" in str(exc_info.value)
    assert "Input should be a valid dictionary or instance of ConnectionConfig" in str(
        exc_info.value
    )


def test_yaml_single_connection_loading():
    """Test loading YAML with single connection."""
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
  model_prefix_id: openai
  model_ids:
    - gpt-4
  tags:
    - Online-Models

models:
  prompt_path: /path/to/prompts
  icon_path: /path/to/icons
  model_setup: {}
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp_yaml:
        tmp_yaml.write(config_yaml)
        yaml_path = tmp_yaml.name

    try:
        config_manager = ConfigManager(SQLiteDatabase("/tmp/test.db"))
        config = config_manager.load_config(yaml_path)

        # Verify connection is loaded correctly
        assert isinstance(config.connections, list)
        assert len(config.connections) == 1
        assert config.connections[0].type == "openai"
        assert config.connections[0].url == "https://api.openai.com/v1"
        assert config.connections[0].model_ids == ["gpt-4"]
    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)


def test_yaml_multiple_connections_loading():
    """Test loading YAML with multiple connections."""
    config_yaml = """
database:
  type: sqlite
  database_location: /tmp/test.db

users: []

groups: []

connections:
  - type: openai
    url: https://api.openai.com/v1
    bearer: test-token
    model_prefix_id: openai
    model_ids:
      - gpt-4
    tags:
      - Online-Models

  - type: ollama
    url: http://localhost:11434
    bearer: null
    model_prefix_id: ollama
    model_ids: []
    tags:
      - Local-Models

models:
  prompt_path: /path/to/prompts
  icon_path: /path/to/icons
  model_setup: {}
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp_yaml:
        tmp_yaml.write(config_yaml)
        yaml_path = tmp_yaml.name

    try:
        config_manager = ConfigManager(SQLiteDatabase("/tmp/test.db"))
        config = config_manager.load_config(yaml_path)

        # Verify connections are loaded correctly
        assert isinstance(config.connections, list)
        assert len(config.connections) == 2
        assert config.connections[0].type == "openai"
        assert config.connections[0].url == "https://api.openai.com/v1"
        assert config.connections[1].type == "ollama"
        assert config.connections[1].url == "http://localhost:11434"
    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)


def test_connection_database_storage():
    """Test storing connections in database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        # Create database and config manager
        database = SQLiteDatabase(db_path)
        config_manager = ConfigManager(database)

        # Create a test config with multiple connections
        test_config = OpenWebUIConfig(
            database={"type": "sqlite", "database_location": db_path},
            users=[],
            groups=[],
            connections=[
                ConnectionConfig(
                    type="openai",
                    url="https://api.openai.com/v1",
                    bearer="test-token",
                    model_prefix_id="openai",
                    model_ids=["gpt-4"],
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
                "model_setup": {},
            },
        )

        # Apply the config
        config_manager.set_dry_run(False)
        config_manager.apply_config(test_config)

        # Verify config was stored in database
        database.connect()
        config_data = database.get_config()
        database.disconnect()

        assert config_data is not None
        assert "connections" in config_data
        assert len(config_data["connections"]) == 2
        assert config_data["connections"][0]["type"] == "openai"
        assert config_data["connections"][0]["url"] == "https://api.openai.com/v1"
        assert config_data["connections"][1]["type"] == "ollama"
        assert config_data["connections"][1]["url"] == "http://localhost:11434"

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_config_yaml_loading():
    """Test loading the user's actual configuration file."""
    config_yaml = """
database:
  type: sqlite
  database_location: /var/lib/docker/openwebui/_data/webui.db

users:
  - name: Peter Fuß-Kailuweit
    email: peter.fuss-kailuweit@gmx.de
    role: Admin
  - name: Schulung_Team_1
    email: schulung1@test.de
    role: User
  - name: Schulung_Team_2
    email: schulung2@test.de
    role: User

groups:
  - name: Schulung
    description: Training group with chat and function permissions
    permissions:
      - chat.controls
      - chat.file_upload
      - chat.edit
      - chat.delete
      - chat.continue_response
      - chat.regenerate_response
      - chat.rate_response
      - chat.stt
      - chat.tts
      - chat.multiple_models
      - chat.temporary
      - features.web_search
      - features.image_generation
      - features.code_interpreter
    members:
      - schulung1@test.de
      - schulung2@test.de

connections:
  - type: openai
    url: https://api.mistral.ai/v1
    bearer: 3X5HGXswma5L8fM7fMaO29zh9pzmyP3x
    extra_headers: null
    model_prefix_id: mistral
    model_ids:
      - ministral-3b-2512
    tags:
      - Online-Models

  - type: ollama
    url: http://ollama:11434
    bearer: null
    extra_headers: null
    model_prefix_id: ollama
    model_ids: []
    tags:
      - Local-Models

models:
  prompt_path: ./system_prompts
  icon_path: ./icons
  model_setup:
    mistral.ministral-3b-2512:
      context_size: "32768"
      system_prompt: ai-teacher.txt
      icon: mistral.png
      capabilities: "image-recognition,file-upload,file-context,websearch,image-generation,code-interpreter,usage-statistics,citations,status-updates,builtin-tools"
      default_capabilities: "websearch,image-generation,code-interpreter"

ui_settings:
  enable_signup: true
  default_locale: "de"
  default_models:
    - "mistral.ministral-3b-2512"

permissions:
  workspace:
    models: true
    knowledge: true
    prompts: true
    tools: true
    models_import: false
    models_export: false
    prompts_import: false
    prompts_export: false
    tools_import: false
    tools_export: false
  chat:
    controls: true
    valves: true
    system_prompt: true
    params: true
    file_upload: true
    delete: true
    delete_message: true
    continue_response: true
    regenerate_response: true
    rate_response: true
    edit: true
    share: true
    export: true
    stt: true
    tts: true
    call: true
    multiple_models: true
    temporary: true
    temporary_enforced: false
  features:
    api_keys: false
    notes: true
    folders: true
    channels: true
    direct_tool_servers: false
    web_search: true
    image_generation: true
    code_interpreter: true
    memories: true
  sharing:
    models: false
    public_models: false
    knowledge: false
    public_knowledge: false
    prompts: false
    public_prompts: false
    tools: false
    public_tools: false
    notes: false
    public_notes: false
  settings:
    interface: true

image_generation:
  enable: true
  engine: "openai"
  model: "dall-e-3"
  openai:
    api_base_url: "https://api.openai.com/v1"
    api_key: "your-api-key-here"
    size: "1024x1024"
    steps: 50
  comfyui:
    base_url: "http://localhost:8188"
    api_key: "your-comfyui-api-key"
    workflow: "{}"
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
        assert len(config.users) == 3
        assert len(config.groups) == 1
        assert isinstance(config.connections, list)
        assert len(config.connections) == 2
        assert config.connections[0].type == "openai"
        assert config.connections[1].type == "ollama"
        assert len(config.models.model_setup) == 1
        assert config.ui_settings.enable_signup is True
        assert config.permissions.features["web_search"] is True
        assert config.image_generation.enable is True

    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)
