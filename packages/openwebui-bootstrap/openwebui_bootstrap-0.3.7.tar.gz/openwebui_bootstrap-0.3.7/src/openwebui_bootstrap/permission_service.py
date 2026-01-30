"""Permission service for RBAC (Role-Based Access Control) functionality."""

from uuid import UUID

from .database.base import DatabaseInterface
from .models import GroupEntity, GroupMemberEntity, PermissionSystemConfig, UserEntity


class PermissionService:
    """Service for managing and resolving user permissions based on RBAC."""

    def __init__(self, database: DatabaseInterface):
        """Initialize the permission service.

        Args:
            database: Database interface for accessing user and group data
        """
        self.database = database

    def get_effective_permissions(self, user: UserEntity) -> PermissionSystemConfig:
        """Get the effective permissions for a user by combining user-specific permissions
        with permissions from all groups the user belongs to.

        Args:
            user: The user entity to get permissions for

        Returns:
            PermissionSystemConfig with the effective permissions
        """
        # Start with default permissions based on user role
        base_permissions = self._get_base_permissions_for_role(user.role)

        # Get all groups the user belongs to
        user_groups = self._get_user_groups(user.id)

        # Merge group permissions (groups are applied in order, later
        # groups override earlier ones)
        effective_permissions = base_permissions
        for group in user_groups:
            if group.permissions:
                effective_permissions = self._merge_permissions(
                    effective_permissions, group.permissions
                )

        # Apply user-specific permission overrides
        # (user permissions take highest precedence)
        if user.permissions:
            effective_permissions = self._merge_permissions(
                effective_permissions, user.permissions
            )

        return effective_permissions

    def has_permission(
        self, user: UserEntity, permission_path: str, default: bool = False
    ) -> bool:
        """Check if a user has a specific permission.

        Args:
            user: The user entity to check
            permission_path: Dot-separated path to the permission
                    (e.g., 'workspace.models')
            default: Default value if permission is not explicitly set

        Returns:
            True if user has the permission, False otherwise
        """
        effective_permissions = self.get_effective_permissions(user)

        # Convert to dict for easier navigation
        permissions_dict = effective_permissions.model_dump()

        # Navigate through the permission structure
        permission_parts = permission_path.split(".")
        current_level = permissions_dict

        for part in permission_parts:
            if isinstance(current_level, dict) and part in current_level:
                current_level = current_level[part]
            else:
                return default

        # If we've navigated to a boolean value, return it
        if isinstance(current_level, bool):
            return current_level

        return default

    def _get_base_permissions_for_role(self, role: str) -> PermissionSystemConfig:
        """Get the base permissions for a user role.

        Args:
            role: The user role

        Returns:
            PermissionSystemConfig with base permissions for the role
        """
        # Define base permissions for each role
        if role.lower() == "admin":
            # Admins have all permissions by default
            return PermissionSystemConfig(
                workspace=dict.fromkeys(
                    PermissionSystemConfig().workspace.keys(), True
                ),
                chat=dict.fromkeys(PermissionSystemConfig().chat.keys(), True),
                features=dict.fromkeys(PermissionSystemConfig().features.keys(), True),
                sharing=dict.fromkeys(PermissionSystemConfig().sharing.keys(), True),
                settings=dict.fromkeys(PermissionSystemConfig().settings.keys(), True),
            )
        elif role.lower() == "user":
            # Regular users have default permissions
            return PermissionSystemConfig()
        elif role.lower() == "pending":
            # Pending users have restricted permissions
            return PermissionSystemConfig(
                workspace={
                    "models": True,
                    "knowledge": False,
                    "prompts": False,
                    "tools": False,
                    "models_import": False,
                    "models_export": False,
                    "prompts_import": False,
                    "prompts_export": False,
                    "tools_import": False,
                    "tools_export": False,
                },
                chat={
                    "controls": True,
                    "valves": True,
                    "system_prompt": False,
                    "params": True,
                    "file_upload": False,
                    "delete": True,
                    "delete_message": True,
                    "continue_response": True,
                    "regenerate_response": True,
                    "rate_response": True,
                    "edit": True,
                    "share": False,
                    "export": False,
                    "stt": True,
                    "tts": True,
                    "call": True,
                    "multiple_models": True,
                    "temporary": True,
                    "temporary_enforced": False,
                },
                features={
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
                sharing={
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
                settings={
                    "interface": True,
                },
            )
        else:
            # Unknown roles get minimal permissions
            return PermissionSystemConfig(
                workspace=dict.fromkeys(
                    PermissionSystemConfig().workspace.keys(), False
                ),
                chat=dict.fromkeys(PermissionSystemConfig().chat.keys(), False),
                features=dict.fromkeys(PermissionSystemConfig().features.keys(), False),
                sharing=dict.fromkeys(PermissionSystemConfig().sharing.keys(), False),
                settings=dict.fromkeys(PermissionSystemConfig().settings.keys(), False),
            )

    def _get_user_groups(self, user_id: UUID) -> list[GroupEntity]:
        """Get all groups that a user belongs to.

        Args:
            user_id: The user ID

        Returns:
            List of GroupEntity objects the user belongs to
        """
        # Query the database for group memberships
        try:
            # Get all group members for this user
            group_members = self.database.get_group_members_for_user(user_id)

            # Get group details for each membership
            groups = []
            for member in group_members:
                group = self.database.get_group_by_id(member.group_id)
                if group:
                    groups.append(group)

            return groups
        except Exception:
            # If database operations fail, return empty list
            return []

    def _merge_permissions(
        self, base_permissions: PermissionSystemConfig, override_permissions: dict
    ) -> PermissionSystemConfig:
        """Merge two permission sets, with override_permissions taking precedence.

        Args:
            base_permissions: Base permissions to start with
            override_permissions: Permissions to override base permissions

        Returns:
            Merged PermissionSystemConfig
        """
        # Convert to dict for easier manipulation
        base_dict = base_permissions.model_dump()
        override_dict = override_permissions

        # Recursively merge the permission dictionaries
        merged_dict = self._deep_merge_dicts(base_dict, override_dict)

        return PermissionSystemConfig(**merged_dict)

    def _deep_merge_dicts(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries, with override taking precedence.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Both are dictionaries, merge them recursively
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                # Override the value
                result[key] = value

        return result

    def get_groups_for_user(self, user_id: UUID) -> list[GroupEntity]:
        """Get all groups that a user belongs to (database implementation).

        Args:
            user_id: The user ID

        Returns:
            List of GroupEntity objects
        """
        # Query the database for group memberships
        try:
            # Get all group members for this user
            group_members = self.database.get_group_members_for_user(user_id)

            # Get group details for each membership
            groups = []
            for member in group_members:
                group = self.database.get_group_by_id(member.group_id)
                if group:
                    groups.append(group)

            return groups
        except Exception:
            # If database operations fail, return empty list
            return []

    def get_group_members_for_user(self, user_id: UUID) -> list[GroupMemberEntity]:
        """Get all group memberships for a user.

        Args:
            user_id: The user ID

        Returns:
            List of GroupMemberEntity objects
        """
        # This would be implemented in the database interface
        # For now, return empty list
        return []

    def set_user_permissions(self, user_id: UUID, permissions: dict) -> bool:
        """Set user-specific permission overrides.

        Args:
            user_id: The user ID
            permissions: Permission dictionary to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current user
            user = self.database.get_user_by_id(user_id)
            if not user:
                # Debug: User not found
                print(f"DEBUG: User with ID {user_id} not found in database")
                # Try to get user by email for debugging
                try:
                    all_users = self.database.get_user_by_email("dbtest@example.com")
                    print(f"DEBUG: Found user by email: {all_users is not None}")
                except:
                    print("DEBUG: Failed to get user by email")
                return False

            # Update permissions
            user.permissions = permissions

            # Save back to database
            self.database.upsert_user(user)

            # Commit the transaction
            if hasattr(self.database, "commit_transaction"):
                self.database.commit_transaction()

            return True
        except Exception as e:
            print(f"DEBUG: Exception in set_user_permissions: {e}")
            return False

    def set_group_permissions(self, group_id: UUID, permissions: dict) -> bool:
        """Set permissions for a group.

        Args:
            group_id: The group ID
            permissions: Permission dictionary to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current group
            group = self.database.get_group_by_id(group_id)
            if not group:
                return False

            # Update permissions
            group.permissions = permissions

            # Save back to database
            self.database.upsert_group(group)
            return True
        except Exception:
            return False
