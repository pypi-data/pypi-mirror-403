"""Abstract base class for database interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models import (
    AuthEntity,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
    UserEntity,
)


class DatabaseInterface(ABC):
    """Abstract base class for database interfaces."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the database."""
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        pass

    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass

    # User operations
    @abstractmethod
    def upsert_user(self, user: UserEntity) -> None:
        """Upsert a user into the database."""
        pass

    @abstractmethod
    def upsert_auth(self, auth: AuthEntity) -> None:
        """Upsert authentication data into the database."""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserEntity | None:
        """Get a user by email address."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> UserEntity | None:
        """Get a user by ID."""
        pass

    @abstractmethod
    def get_auth_by_email(self, email: str) -> AuthEntity | None:
        """Get authentication data by email address."""
        pass

    # Group operations
    @abstractmethod
    def upsert_group(self, group: GroupEntity) -> None:
        """Upsert a group into the database."""
        pass

    @abstractmethod
    def upsert_group_member(self, group_member: GroupMemberEntity) -> None:
        """Upsert a group member into the database."""
        pass

    @abstractmethod
    def get_group_by_name(self, name: str) -> GroupEntity | None:
        """Get a group by name."""
        pass

    @abstractmethod
    def get_user_by_email_for_group(self, email: str) -> UUID | None:
        """Get user ID by email for group membership."""
        pass

    @abstractmethod
    def get_group_by_id(self, group_id: UUID) -> GroupEntity | None:
        """Get a group by ID."""
        pass

    @abstractmethod
    def get_group_members_for_user(self, user_id: UUID) -> list[GroupMemberEntity]:
        """Get all group memberships for a user."""
        pass

    # Model operations
    @abstractmethod
    def upsert_model(self, model: ModelEntity) -> None:
        """Upsert a model into the database."""
        pass

    @abstractmethod
    def get_model_by_id(self, model_id: str) -> ModelEntity | None:
        """Get a model by ID."""
        pass

    # Config operations
    @abstractmethod
    def upsert_config(self, config_data: dict) -> None:
        """Upsert configuration data into the config table."""
        pass

    @abstractmethod
    def get_config(self) -> dict | None:
        """Get current configuration from the config table."""
        pass

    # Reset operations
    @abstractmethod
    def clear_table(self, table_name: str) -> None:
        """Clear all data from a specific table."""
        pass

    @abstractmethod
    def clear_managed_tables(self) -> None:
        """Clear all managed tables (users, groups, models, etc.)."""
        pass

    # Utility methods
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        pass

    @abstractmethod
    def get_managed_tables(self) -> list[str]:
        """Get list of tables managed by this tool."""
        pass
