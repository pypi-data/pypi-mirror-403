"""Data models for Open WebUI Bootstrap configuration and database entities."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class DatabaseConfig(BaseModel):
    """Database configuration model."""

    type: str = Field(..., description="Database type (sqlite, postgresql, etc.)")
    database_location: str = Field(
        ..., description="Path to database file or connection string"
    )


class UserConfig(BaseModel):
    """User configuration model."""

    name: str = Field(..., description="User's display name")
    email: str = Field(..., description="User's email address (used for login)")
    role: str = Field(..., description="User's role (Admin, User, etc.)")


class GroupConfig(BaseModel):
    """Group configuration model."""

    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    permissions: list[str] = Field(
        default_factory=list, description="List of permissions"
    )
    members: list[str] = Field(
        default_factory=list, description="List of member email addresses"
    )


class UISettingsConfig(BaseModel):
    """UI configuration model."""

    enable_signup: bool = Field(True, description="Enable user signup")
    default_locale: str | None = Field(None, description="Default locale for UI")
    default_models: list[str] | None = Field(
        None, description="List of default model IDs"
    )


class PermissionSystemConfig(BaseModel):
    """User permission system configuration."""

    workspace: dict[str, bool] = Field(
        default_factory=lambda: {
            "models": True,
            "knowledge": True,
            "prompts": True,
            "tools": True,
            "models_import": False,
            "models_export": False,
            "prompts_import": False,
            "prompts_export": False,
            "tools_import": False,
            "tools_export": False,
        },
        description="Workspace access permissions",
    )

    chat: dict[str, bool] = Field(
        default_factory=lambda: {
            "controls": True,
            "valves": True,
            "system_prompt": True,
            "params": True,
            "file_upload": True,
            "delete": True,
            "delete_message": True,
            "continue_response": True,
            "regenerate_response": True,
            "rate_response": True,
            "edit": True,
            "share": True,
            "export": True,
            "stt": True,
            "tts": True,
            "call": True,
            "multiple_models": True,
            "temporary": True,
            "temporary_enforced": False,
        },
        description="Chat feature permissions",
    )

    features: dict[str, bool] = Field(
        default_factory=lambda: {
            "api_keys": False,
            "notes": True,
            "folders": True,
            "channels": True,
            "direct_tool_servers": False,
            "web_search": True,
            "image_generation": True,
            "code_interpreter": True,
            "memories": True,
        },
        description="Feature access permissions",
    )

    sharing: dict[str, bool] = Field(
        default_factory=lambda: {
            "models": False,
            "public_models": False,
            "knowledge": False,
            "public_knowledge": False,
            "prompts": False,
            "public_prompts": False,
            "tools": False,
            "public_tools": False,
            "notes": False,
            "public_notes": False,
        },
        description="Sharing permissions",
    )

    settings: dict[str, bool] = Field(
        default_factory=lambda: {
            "interface": True,
        },
        description="Settings interface permissions",
    )


class ImageGenerationConfig(BaseModel):
    """Image generation configuration."""

    enable: bool = Field(True, description="Enable image generation")
    engine: str = Field(
        "openai", description="Image generation engine (openai, mistral, comfyui)"
    )
    model: str | None = Field(None, description="Default image generation model")

    # OpenAI/Mistral configuration
    openai: dict[str, str | int] | None = Field(
        None, description="OpenAI/Mistral API configuration"
    )

    # ComfyUI configuration
    comfyui: dict[str, str | dict] | None = Field(
        None, description="ComfyUI server configuration"
    )


class ConnectionConfig(BaseModel):
    """Connection configuration model."""

    type: str = Field(..., description="Connection type (openai, ollama, azure, etc.)")
    url: str = Field(..., description="Connection URL")
    bearer: str | None = Field(None, description="Bearer token for authentication")
    extra_headers: dict[str, str] | None = Field(None, description="Extra HTTP headers")
    model_prefix_id: str | None = Field(None, description="Prefix for model IDs")
    model_ids: list[str] = Field(default_factory=list, description="List of model IDs")
    tags: list[str] | None = Field(None, description="Tags for categorization")

    # Extended connection settings
    enable: bool = Field(True, description="Enable this connection")
    base_urls: list[str] | None = Field(
        None, description="List of base URLs for this connection type"
    )
    api_keys: list[str] | None = Field(
        None, description="List of API keys for this connection"
    )


class ModelConfig(BaseModel):
    """Model configuration model."""

    prompt_path: str = Field(..., description="Path to system prompts directory")
    icon_path: str = Field(..., description="Path to model icons directory")
    model_setup: dict[str, dict[str, str]] = Field(
        default_factory=dict,
        description="Per-model configuration (model_id -> settings)",
    )


class OpenWebUIConfig(BaseModel):
    """Main configuration model for Open WebUI Bootstrap."""

    database: DatabaseConfig = Field(..., description="Database configuration")
    users: list[UserConfig] = Field(
        default_factory=list, description="User configurations"
    )
    groups: list[GroupConfig] = Field(
        default_factory=list, description="Group configurations"
    )
    connections: ConnectionConfig | list[ConnectionConfig] = Field(
        ..., description="Connection configuration (single or list)"
    )
    models: ModelConfig = Field(..., description="Model configuration")

    # New configuration sections
    ui_settings: UISettingsConfig = Field(
        default_factory=UISettingsConfig, description="UI configuration settings"
    )

    permissions: PermissionSystemConfig = Field(
        default_factory=PermissionSystemConfig,
        description="User permission system configuration",
    )

    image_generation: ImageGenerationConfig = Field(
        default_factory=ImageGenerationConfig,
        description="Image generation configuration",
    )

    @field_validator("users")
    def validate_users(cls, users):
        """Validate that user emails are unique."""
        emails = [user.email for user in users]
        if len(emails) != len(set(emails)):
            raise ValueError("User emails must be unique")
        return users

    @field_validator("groups")
    def validate_groups(cls, groups):
        """Validate that group names are unique."""
        names = [group.name for group in groups]
        if len(names) != len(set(names)):
            raise ValueError("Group names must be unique")
        return groups

    @field_validator("connections")
    def validate_connections(cls, connections):
        """Validate and normalize connections to always be a list."""
        if isinstance(connections, ConnectionConfig):
            # Convert single connection to list
            return [connections]
        elif isinstance(connections, list):
            # Validate all items in list are ConnectionConfig
            for conn in connections:
                if not isinstance(conn, ConnectionConfig):
                    raise ValueError(
                        f"All connection items must be ConnectionConfig instances, got {type(conn)}"
                    )
            return connections
        else:
            raise ValueError(
                f"Connections must be either ConnectionConfig or list[ConnectionConfig], got {type(connections)}"
            )


# Database Entity Models (matching Open WebUI database schema)


class AuthEntity(BaseModel):
    """Auth table entity."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    email: str = Field(..., description="User's email")
    password: str = Field(..., description="Hashed password")
    active: bool = Field(True, description="Account status")


class UserEntity(BaseModel):
    """User table entity."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    username: str | None = Field(None, description="User's username")
    name: str = Field(..., description="User's name")
    email: str = Field(..., description="User's email")
    role: str = Field(..., description="User's role")
    profile_image_url: str | None = Field(None, description="Profile image URL")
    profile_banner_image_url: str | None = Field(
        None, description="Profile banner image URL"
    )
    bio: str | None = Field(None, description="User's biography")
    gender: str | None = Field(None, description="User's gender")
    date_of_birth: str | None = Field(None, description="User's date of birth")
    timezone: str | None = Field(None, description="User's timezone")
    presence_state: str | None = Field(None, description="User's presence state")
    status_emoji: str | None = Field(None, description="Status emoji")
    status_message: str | None = Field(None, description="Custom status message")
    status_expires_at: int | None = Field(
        None, description="Status expiration timestamp"
    )
    last_active_at: int = Field(0, description="Last activity timestamp")
    updated_at: int = Field(0, description="Last update timestamp")
    created_at: int = Field(0, description="Creation timestamp")
    settings: dict | None = Field(None, description="User preferences")
    info: dict | None = Field(None, description="Additional user info")
    oauth: dict | None = Field(None, description="Complete OAuth data")
    permissions: dict | None = Field(
        None, description="User-specific permission overrides"
    )


class GroupEntity(BaseModel):
    """Group table entity."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    user_id: UUID = Field(..., description="Group owner/creator ID")
    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    data: dict | None = Field(None, description="Additional group data")
    meta: dict | None = Field(None, description="Group metadata")
    permissions: dict | None = Field(
        None, description="Group-level permissions (applied to all members)"
    )
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Last update timestamp")


class GroupMemberEntity(BaseModel):
    """Group member table entity."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    group_id: UUID = Field(..., description="Group ID")
    user_id: UUID = Field(..., description="User ID")
    created_at: int | None = Field(None, description="Creation timestamp")
    updated_at: int | None = Field(None, description="Last update timestamp")


class ModelEntity(BaseModel):
    """Model entity representing a model configuration."""

    id: str = Field(..., description="Model identifier")
    user_id: UUID | None = Field(None, description="User ID who owns the model")
    base_model_id: str | None = Field(None, description="Base model identifier")
    name: str = Field(..., description="Model name")
    params: dict = Field(..., description="Model parameters")
    meta: dict = Field(..., description="Model metadata")
    access_control: dict | None = Field(None, description="Access control settings")
    is_active: bool = Field(True, description="Whether the model is active")
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Last update timestamp")
