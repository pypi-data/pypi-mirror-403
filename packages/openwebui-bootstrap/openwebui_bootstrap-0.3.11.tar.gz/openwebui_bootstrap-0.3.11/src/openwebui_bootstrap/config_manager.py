"""Configuration manager for Open WebUI Bootstrap."""

import hashlib
import time
from uuid import UUID, uuid4

import yaml
from pydantic import ValidationError

from .database.base import DatabaseInterface
from .exceptions import (
    ConfigurationFileError,
    ConfigurationValidationError,
    DatabaseCorruptionError,
    DatabaseReplacementError,
    DatabaseValidationError,
    ResetError,
    UpsertError,
)
from .logging_config import get_logger
from .models import (
    AuthEntity,
    ConnectionConfig,
    GroupConfig,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
    OpenWebUIConfig,
    UserConfig,
    UserEntity,
)

logger = get_logger(__name__)


class ConfigManager:
    """Configuration manager for Open WebUI Bootstrap."""

    def __init__(self, database: DatabaseInterface):
        """Initialize the configuration manager.

        Args:
            database: Database interface instance
        """
        self.database = database
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run mode.

        Args:
            dry_run: Whether to run in dry run mode
        """
        self.dry_run = dry_run
        logger.info(f"Dry run mode {'enabled' if dry_run else 'disabled'}")

    def load_config(self, config_path: str) -> OpenWebUIConfig:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Parsed and validated configuration

        Raises:
            ConfigurationFileError: If configuration file cannot be read or parsed
            ConfigurationValidationError: If configuration is invalid
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                raise ConfigurationFileError("Configuration file is empty")

            return OpenWebUIConfig(**config_data)
        except yaml.YAMLError as e:
            raise ConfigurationFileError(f"Failed to parse YAML configuration: {e}")
        except ValidationError as e:
            raise ConfigurationValidationError(f"Configuration validation failed: {e}")
        except Exception as e:
            raise ConfigurationFileError(f"Failed to load configuration: {e}")

    def apply_config(self, config: OpenWebUIConfig, reset_active: bool = False) -> None:
        """Apply configuration to the database with validation and fallback logic.

        Args:
            config: Configuration to apply
            reset_active: Whether reset option is active

        Raises:
            DatabaseError: If database operations fail
            DryRunError: If dry run mode is enabled
        """
        if self.dry_run:
            logger.info(
                "Dry run mode: would apply configuration but not making changes"
            )
            return

        try:
            # First, validate and repair database if needed
            logger.info("Starting database validation before applying configuration")
            self.database.validate_and_repair_database(reset_active)
            logger.info("Database validation completed successfully")

            # Connect to database
            self.database.connect()

            # Begin transaction for atomic operation
            self.database.begin_transaction()

            # Apply configuration in order: users -> groups -> models -> new configs
            self._apply_users(config)
            self._apply_groups(config)
            self._apply_models(config)
            self._apply_connections(config)
            self._apply_ui_settings(config)
            self._apply_permissions(config)
            self._apply_image_generation(config)

            # Commit transaction
            self.database.commit_transaction()

            logger.info("Configuration applied successfully")

        except Exception as e:
            # Rollback on error
            if self.database.connection:
                self.database.rollback_transaction()
            raise UpsertError(f"Failed to apply configuration: {e}")
        finally:
            # Disconnect from database
            if self.database.connection:
                self.database.disconnect()

    def reset_database(self) -> None:
        """Reset the database by clearing all managed tables.

        Raises:
            DatabaseError: If database operations fail
            DryRunError: If dry run mode is enabled
        """
        if self.dry_run:
            logger.info("Dry run mode: would reset database but not making changes")
            return

        try:
            # Connect to database
            self.database.connect()

            # Clear all managed tables
            self.database.clear_managed_tables()

            logger.info("Database reset successfully")

        except Exception as e:
            raise ResetError(f"Failed to reset database: {e}")
        finally:
            # Disconnect from database
            if self.database.connection:
                self.database.disconnect()

    def _apply_users(self, config: OpenWebUIConfig) -> None:
        """Apply user configuration to the database.

        Args:
            config: Configuration containing users
        """
        logger.info(f"Applying {len(config.users)} user configurations")

        for user_config in config.users:
            # Create user entity
            user_entity = self._create_user_entity(user_config)

            # Upsert user
            self.database.upsert_user(user_entity)

            # Create auth entity
            auth_entity = self._create_auth_entity(user_config, user_entity.id)

            # Upsert auth
            self.database.upsert_auth(auth_entity)

            logger.debug(f"Applied user configuration for {user_config.email}")

    def _create_user_entity(self, user_config: UserConfig) -> UserEntity:
        """Create a user entity from user configuration.

        Args:
            user_config: User configuration

        Returns:
            User entity ready for database insertion
        """
        return UserEntity(
            id=uuid4(),
            username=user_config.email.split("@")[0],  # Use email prefix as username
            name=user_config.name,
            email=user_config.email,
            role=user_config.role,
            profile_image_url="",  # Empty string instead of None to avoid NOT NULL constraint
            bio="",
            gender="",
            date_of_birth="",
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
            settings=None,
            info=None,
        )

    def _create_auth_entity(self, user_config: UserConfig, user_id: UUID) -> AuthEntity:
        """Create an auth entity from user configuration.

        Args:
            user_config: User configuration
            user_id: User ID to associate with auth

        Returns:
            Auth entity ready for database insertion
        """
        # Generate a default password (in real usage, this would be properly hashed)
        default_password = hashlib.sha256(user_config.email.encode()).hexdigest()

        return AuthEntity(
            id=user_id,
            email=user_config.email,
            password=default_password,
            active=True,
        )

    def _apply_groups(self, config: OpenWebUIConfig) -> None:
        """Apply group configuration to the database.

        Args:
            config: Configuration containing groups
        """
        logger.info(f"Applying {len(config.groups)} group configurations")

        for group_config in config.groups:
            # Create group entity
            group_entity = self._create_group_entity(group_config)

            # Upsert group
            self.database.upsert_group(group_entity)

            # Apply group members
            self._apply_group_members(group_config, group_entity.id)

            logger.debug(f"Applied group configuration for {group_config.name}")

    def _create_group_entity(self, group_config: GroupConfig) -> GroupEntity:
        """Create a group entity from group configuration.

        Args:
            group_config: Group configuration

        Returns:
            Group entity ready for database insertion

        Raises:
            UpsertError: If admin user cannot be found for group ownership
        """
        # Find admin user to use as group owner
        # This ensures foreign key constraints are satisfied
        if self.dry_run:
            # In dry run mode, use a placeholder UUID for group owner
            # This allows testing without requiring database connection
            logger.debug("Dry run mode: using placeholder UUID for group owner")
            owner_id = uuid4()
        else:
            try:
                # Find admin user by role instead of email for better reliability
                if hasattr(self.database, "connection") and self.database.connection:
                    cursor = self.database.connection.cursor()
                    # Query for users with Admin role
                    cursor.execute(
                        "SELECT id FROM user WHERE role = ? LIMIT 1", ("Admin",)
                    )
                    row = cursor.fetchone()
                    if row:
                        owner_id = UUID(row[0])
                        logger.debug("Using admin user (by role) as group owner")
                    else:
                        # Fallback: try to find any user to be the owner
                        # This handles cases where no admin user exists
                        cursor.execute("SELECT id FROM user LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            owner_id = UUID(row[0])
                            logger.warning(
                                "No admin user found, using first available user as group owner"
                            )
                        else:
                            # No users exist - this shouldn't happen as users are created before groups
                            logger.error(
                                "No users found in database to assign as group owner"
                            )
                            raise UpsertError(
                                "No users available to assign as group owner"
                            )
                else:
                    logger.error(
                        "Database connection not available to find group owner"
                    )
                    raise UpsertError("Database connection not available")

            except Exception as e:
                logger.error(f"Failed to find group owner: {e}")
                raise UpsertError(f"Failed to determine group owner: {e}")

        return GroupEntity(
            id=uuid4(),
            user_id=owner_id,
            name=group_config.name,
            description=group_config.description,
            data=None,
            meta=None,
            permissions=self._convert_permissions(group_config.permissions),
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

    def _convert_permissions(self, permissions: list[str]) -> dict[str, bool]:
        """Convert list of permissions to dictionary format.

        Args:
            permissions: List of permission strings

        Returns:
            Dictionary of permissions with boolean values
        """
        return dict.fromkeys(permissions, True)

    def _apply_group_members(self, group_config: GroupConfig, group_id: UUID) -> None:
        """Apply group members to the database.

        Args:
            group_config: Group configuration
            group_id: Group ID to associate members with
        """
        for member_email in group_config.members:
            # Get user ID by email
            user_id = self.database.get_user_by_email_for_group(member_email)

            if not user_id:
                logger.warning(
                    f"User {member_email} not found, skipping group membership"
                )
                continue

            # Create group member entity
            group_member_entity = GroupMemberEntity(
                id=uuid4(),
                group_id=group_id,
                user_id=user_id,
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )

            # Upsert group member
            self.database.upsert_group_member(group_member_entity)

            logger.debug(
                f"Applied group membership for {member_email} in group "
                f"{group_config.name}"
            )

    def _apply_models(self, config: OpenWebUIConfig) -> None:
        """Apply model configuration to the database.

        Args:
            config: Configuration containing models
        """
        logger.info(
            f"Applying model configuration with "
            f"{len(config.models.model_setup)} model setups"
        )

        # Apply each model setup
        for model_id, model_settings in config.models.model_setup.items():
            model_entity = self._create_model_entity(model_id, model_settings, config)
            self.database.upsert_model(model_entity)
            logger.debug(f"Applied model configuration for {model_id}")

    def _apply_ui_settings(self, config: OpenWebUIConfig) -> None:
        """Apply UI settings configuration to the database.

        Args:
            config: Configuration containing UI settings
        """
        logger.info("Applying UI settings configuration")

        # Get existing config or create new
        try:
            existing_config = self.database.get_config() or {}
        except Exception:
            # Config table doesn't exist yet, start with empty config
            existing_config = {}

        # Update with UI settings
        existing_config["ui"] = {
            "enable_signup": config.ui_settings.enable_signup,
            "default_locale": config.ui_settings.default_locale,
            "default_models": config.ui_settings.default_models or [],
        }

        self.database.upsert_config(existing_config)
        logger.debug("Applied UI settings configuration")

    def _apply_permissions(self, config: OpenWebUIConfig) -> None:
        """Apply permission system configuration to the database.

        Args:
            config: Configuration containing permissions
        """
        logger.info("Applying permission system configuration")

        # Get existing config or create new
        try:
            existing_config = self.database.get_config() or {}
        except Exception:
            # Config table doesn't exist yet, start with empty config
            existing_config = {}

        # Update with permissions
        existing_config["user"] = {
            "permissions": {
                "workspace": config.permissions.workspace,
                "chat": config.permissions.chat,
                "features": config.permissions.features,
                "sharing": config.permissions.sharing,
                "settings": config.permissions.settings,
            }
        }

        self.database.upsert_config(existing_config)
        logger.debug("Applied permission system configuration")

    def _apply_image_generation(self, config: OpenWebUIConfig) -> None:
        """Apply image generation configuration to the database.

        Args:
            config: Configuration containing image generation settings
        """
        logger.info("Applying image generation configuration")

        # Get existing config or create new
        try:
            existing_config = self.database.get_config() or {}
        except Exception:
            # Config table doesn't exist yet, start with empty config
            existing_config = {}

        # Update with image generation settings
        existing_config["image_generation"] = {
            "enable": config.image_generation.enable,
            "engine": config.image_generation.engine,
            "model": config.image_generation.model,
            "openai": config.image_generation.openai or {},
            "comfyui": config.image_generation.comfyui or {},
        }

        self.database.upsert_config(existing_config)
        logger.debug("Applied image generation configuration")

    def _create_model_entity(
        self, model_id: str, model_settings: dict[str, str], config: OpenWebUIConfig
    ) -> ModelEntity:
        """Create a model entity from model configuration.

        Args:
            model_id: Model identifier
            model_settings: Model-specific settings
            config: Full configuration for context

        Returns:
            Model entity ready for database insertion
        """
        # Parse model settings
        context_size = model_settings.get("context_size", "32768")
        system_prompt = model_settings.get("system_prompt")
        icon = model_settings.get("icon")

        # Parse capabilities from model settings
        capabilities = self._parse_capabilities(
            model_settings.get("capabilities", "").split(",")
            if isinstance(model_settings.get("capabilities"), str)
            else model_settings.get("capabilities", [])
        )
        default_capabilities = self._parse_capabilities(
            model_settings.get("default_capabilities", "").split(",")
            if isinstance(model_settings.get("default_capabilities"), str)
            else model_settings.get("default_capabilities", [])
        )

        # Get the first user ID from the config to use as model owner
        # This ensures user_id is not None for databases with NOT NULL constraint
        first_user_id = None

        if self.dry_run:
            # In dry run mode, use a placeholder UUID for model owner
            logger.debug("Dry run mode: using placeholder UUID for model owner")
            first_user_id = uuid4()
        else:
            try:
                # Try to find an admin user by role first (similar to group creation)
                if hasattr(self.database, "connection") and self.database.connection:
                    cursor = self.database.connection.cursor()
                    # Query for users with Admin role
                    cursor.execute(
                        "SELECT id FROM user WHERE role = ? LIMIT 1", ("Admin",)
                    )
                    row = cursor.fetchone()
                    if row:
                        first_user_id = UUID(row[0])
                        logger.debug("Using admin user (by role) as model owner")
                    else:
                        # Fallback: try to find any user to be the owner
                        cursor.execute("SELECT id FROM user LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            first_user_id = UUID(row[0])
                            logger.debug("Using first available user as model owner")
                        else:
                            # No users exist - use placeholder UUID
                            first_user_id = uuid4()
                            logger.warning(
                                "No users found, using placeholder UUID as model owner"
                            )
                else:
                    # No database connection available - use placeholder UUID
                    first_user_id = uuid4()
                    logger.debug(
                        "No database connection, using placeholder UUID as model owner"
                    )

            except Exception as e:
                logger.error(f"Failed to find model owner: {e}")
                # Fallback to placeholder UUID on error
                first_user_id = uuid4()

        return ModelEntity(
            id=model_id,
            user_id=first_user_id,  # Use first user as owner if available
            base_model_id=None,
            name=model_id,
            params={
                "context_size": int(context_size),
                "system_prompt": system_prompt,
                "icon": icon,
            },
            meta={
                "prompt_path": config.models.prompt_path,
                "icon_path": config.models.icon_path,
                "capabilities": capabilities,
                "default_capabilities": default_capabilities,
            },
            access_control=None,
            is_active=True,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

    def _apply_connections(self, config: OpenWebUIConfig) -> None:
        """Apply connection configuration to the database.

        Args:
            config: Configuration containing connections
        """
        logger.info(f"Applying {len(config.connections)} connection configurations")

        # Get existing config or create new
        try:
            existing_config = self.database.get_config() or {}
        except Exception:
            # Config table doesn't exist yet, start with empty config
            existing_config = {}

        # Convert connections to list format (validator ensures this)
        connections_list = config.connections
        if isinstance(connections_list, ConnectionConfig):
            connections_list = [connections_list]

        # Store connections in config
        existing_config["connections"] = []
        for conn in connections_list:
            conn_data = {
                "type": conn.type,
                "url": conn.url,
                "bearer": conn.bearer,
                "enable": conn.enable,
                "model_prefix_id": conn.model_prefix_id,
                "model_ids": conn.model_ids,
                "tags": conn.tags,
                "extra_headers": conn.extra_headers,
                "base_urls": conn.base_urls,
                "api_keys": conn.api_keys,
            }
            existing_config["connections"].append(conn_data)

            logger.debug(
                f"Applied connection configuration for {conn.type} at {conn.url}"
            )

        self.database.upsert_config(existing_config)

    def _parse_capabilities(self, capability_list: list[str]) -> dict[str, bool]:
        """Parse capability list and map to Open WebUI capability names.

        Args:
            capability_list: List of capability strings

        Returns:
            Dictionary of capabilities with boolean values
        """
        # Mapping from bootstrap capability names to Open WebUI capability names
        capability_mapping = {
            "image-recognition": "vision",
            "file-upload": "file_upload",
            "file-context": "file_context",
            "websearch": "web_search",
            "image-generation": "image_generation",
            "code-interpreter": "code_interpreter",
            "usage-statistics": "usage",
            "citations": "citations",
            "status-updates": "status_updates",
            "builtin-tools": "builtin_tools",
        }

        capabilities = {}
        for capability in capability_list:
            if capability in capability_mapping:
                capabilities[capability_mapping[capability]] = True
            else:
                logger.warning(f"Unknown capability: {capability}")

        return capabilities
