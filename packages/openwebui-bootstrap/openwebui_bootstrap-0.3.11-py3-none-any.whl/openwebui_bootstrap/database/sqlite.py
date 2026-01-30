"""SQLite database implementation for Open WebUI Bootstrap."""

import json
import os
import shutil
import sqlite3
import time
from uuid import UUID

from openwebui_bootstrap.exceptions import (
    DatabaseConnectionError,
    DatabaseCorruptionError,
    DatabaseOperationError,
    DatabaseReplacementError,
    DatabaseTransactionError,
    DatabaseValidationError,
)
from openwebui_bootstrap.logging_config import get_logger
from openwebui_bootstrap.models import (
    AuthEntity,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
    UserEntity,
)
from openwebui_bootstrap.utils import get_resource_path
from .base import DatabaseInterface

logger = get_logger(__name__)


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of the database interface."""

    def __init__(self, database_path: str):
        """Initialize SQLite database connection.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.connection = None
        self.cursor = None

    def connect(self) -> None:
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.cursor = self.connection.cursor()
            # Enable foreign key constraints
            self.cursor.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def disconnect(self) -> None:
        """Disconnect from the SQLite database."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        if not self.connection:
            raise DatabaseTransactionError("Not connected to database")
        try:
            self.cursor.execute("BEGIN TRANSACTION")
        except sqlite3.Error as e:
            raise DatabaseTransactionError(f"Failed to begin transaction: {e}")

    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self.connection:
            raise DatabaseTransactionError("Not connected to database")
        try:
            self.connection.commit()
        except sqlite3.Error as e:
            raise DatabaseTransactionError(f"Failed to commit transaction: {e}")

    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self.connection:
            raise DatabaseTransactionError("Not connected to database")
        try:
            self.connection.rollback()
        except sqlite3.Error as e:
            raise DatabaseTransactionError(f"Failed to rollback transaction: {e}")

    # User operations
    def upsert_user(self, user: UserEntity) -> None:
        """Upsert a user into the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check if user exists
            logger.debug(f"Checking if user {user.email} exists")
            self.cursor.execute("SELECT id FROM user WHERE email = ?", (user.email,))
            existing_user = self.cursor.fetchone()
            logger.debug(f"User {user.email} exists: {existing_user is not None}")

            # Check which columns exist in the user table
            self.cursor.execute("PRAGMA table_info(user)")
            columns = [row[1] for row in self.cursor.fetchall()]
            logger.debug(f"User table columns: {columns}")

            if existing_user:
                # Build UPDATE query dynamically based on available columns
                updates = []
                params = []

                # Map of column names to user attributes
                column_map = {
                    "username": user.username,
                    "name": user.name,
                    "role": user.role,
                    "profile_image_url": user.profile_image_url,
                    "profile_banner_image_url": user.profile_banner_image_url,
                    "bio": user.bio,
                    "gender": user.gender,
                    "date_of_birth": user.date_of_birth,
                    "timezone": user.timezone,
                    "presence_state": user.presence_state,
                    "status_emoji": user.status_emoji,
                    "status_message": user.status_message,
                    "status_expires_at": user.status_expires_at,
                    "last_active_at": user.last_active_at,
                    "updated_at": int(time.time()),
                    "created_at": user.created_at,
                    "settings": json.dumps(user.settings) if user.settings else None,
                    "info": json.dumps(user.info) if user.info else None,
                    "oauth": json.dumps(user.oauth) if user.oauth else None,
                    "permissions": json.dumps(user.permissions)
                    if user.permissions
                    else None,
                }

                for col_name, col_value in column_map.items():
                    if col_name in columns:
                        updates.append(f"{col_name} = ?")
                        params.append(col_value)

                if updates:
                    query = f"UPDATE user SET {', '.join(updates)} WHERE email = ?"
                    params.append(user.email)
                    logger.debug(f"Executing UPDATE query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.warning(
                        f"No updatable columns found in user table for {user.email}"
                    )

            else:
                # Build INSERT query dynamically based on available columns
                insert_columns = []
                insert_values = []
                params = []

                # Map of column names to user attributes for INSERT
                insert_map = {
                    "id": str(user.id),
                    "username": user.username,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "profile_image_url": user.profile_image_url,
                    "profile_banner_image_url": user.profile_banner_image_url,
                    "bio": user.bio,
                    "gender": user.gender,
                    "date_of_birth": user.date_of_birth,
                    "timezone": user.timezone,
                    "presence_state": user.presence_state,
                    "status_emoji": user.status_emoji,
                    "status_message": user.status_message,
                    "status_expires_at": user.status_expires_at,
                    "last_active_at": user.last_active_at,
                    "updated_at": int(time.time()),
                    "created_at": int(time.time()),
                    "settings": json.dumps(user.settings) if user.settings else None,
                    "info": json.dumps(user.info) if user.info else None,
                    "oauth": json.dumps(user.oauth) if user.oauth else None,
                    "permissions": json.dumps(user.permissions)
                    if user.permissions
                    else None,
                }

                for col_name, col_value in insert_map.items():
                    if col_name in columns:
                        insert_columns.append(col_name)
                        insert_values.append("?")
                        params.append(col_value)

                if insert_columns:
                    columns = ", ".join(insert_columns)
                    values = ", ".join(insert_values)
                    query = f"INSERT INTO user ({columns}) VALUES ({values})"
                    logger.debug(f"Executing INSERT query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.error("No insertable columns found in user table")
                    raise DatabaseOperationError(
                        "No columns available for user insertion"
                    )

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise DatabaseOperationError(f"Failed to upsert user: {e}")

    def upsert_auth(self, auth: AuthEntity) -> None:
        """Upsert authentication data into the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check if auth exists
            self.cursor.execute("SELECT id FROM auth WHERE email = ?", (auth.email,))
            existing_auth = self.cursor.fetchone()

            if existing_auth:
                # Update existing auth
                self.cursor.execute(
                    """
                    UPDATE auth SET
                        password = ?,
                        active = ?
                    WHERE email = ?
                """,
                    (
                        auth.password,
                        auth.active,
                        auth.email,
                    ),
                )
            else:
                # Insert new auth
                self.cursor.execute(
                    """
                    INSERT INTO auth (id, email, password, active)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        str(auth.id),
                        auth.email,
                        auth.password,
                        auth.active,
                    ),
                )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to upsert auth: {e}")

    def get_user_by_email(self, email: str) -> UserEntity | None:
        """Get a user by email address."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT
                    id, username, name, email, role, profile_image_url, 
                    profile_banner_image_url, bio, gender, date_of_birth, timezone,
                    presence_state, status_emoji, status_message, status_expires_at,
                    last_active_at, updated_at, created_at, settings, info, oauth,
                    permissions
                FROM user WHERE email = ?
            """,
                (email,),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return UserEntity(
                id=UUID(row[0]),
                username=row[1],
                name=row[2],
                email=row[3],
                role=row[4],
                profile_image_url=row[5],
                profile_banner_image_url=row[6],
                bio=row[7],
                gender=row[8],
                date_of_birth=row[9],
                timezone=row[10],
                presence_state=row[11],
                status_emoji=row[12],
                status_message=row[13],
                status_expires_at=row[14],
                last_active_at=row[15],
                updated_at=row[16],
                created_at=row[17],
                settings=json.loads(row[18]) if row[18] else None,
                info=json.loads(row[19]) if row[19] else None,
                oauth=json.loads(row[20]) if row[20] else None,
                permissions=json.loads(row[21]) if row[21] else None,
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get user by email: {e}")

    def get_user_by_id(self, user_id: UUID) -> UserEntity | None:
        """Get a user by ID."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT
                    id, username, name, email, role, profile_image_url, 
                    profile_banner_image_url, bio, gender, date_of_birth, timezone,
                    presence_state, status_emoji, status_message, status_expires_at,
                    last_active_at, updated_at, created_at, settings, info, oauth,
                    permissions
                FROM user WHERE id = ?
            """,
                (str(user_id),),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return UserEntity(
                id=UUID(row[0]),
                username=row[1],
                name=row[2],
                email=row[3],
                role=row[4],
                profile_image_url=row[5],
                profile_banner_image_url=row[6],
                bio=row[7],
                gender=row[8],
                date_of_birth=row[9],
                timezone=row[10],
                presence_state=row[11],
                status_emoji=row[12],
                status_message=row[13],
                status_expires_at=row[14],
                last_active_at=row[15],
                updated_at=row[16],
                created_at=row[17],
                settings=json.loads(row[18]) if row[18] else None,
                info=json.loads(row[19]) if row[19] else None,
                oauth=json.loads(row[20]) if row[20] else None,
                permissions=json.loads(row[21]) if row[21] else None,
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get user by ID: {e}")

    def get_auth_by_email(self, email: str) -> AuthEntity | None:
        """Get authentication data by email address."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT id, email, password, active
                FROM auth WHERE email = ?
            """,
                (email,),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return AuthEntity(
                id=UUID(row[0]),
                email=row[1],
                password=row[2],
                active=bool(row[3]),
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get auth by email: {e}")

    # Group operations
    def upsert_group(self, group: GroupEntity) -> None:
        """Upsert a group into the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check if group exists
            self.cursor.execute("SELECT id FROM [group] WHERE name = ?", (group.name,))
            existing_group = self.cursor.fetchone()

            if existing_group:
                # Update existing group
                self.cursor.execute(
                    """
                    UPDATE [group] SET
                        user_id = ?,
                        description = ?,
                        data = ?,
                        meta = ?,
                        permissions = ?,
                        updated_at = ?
                    WHERE name = ?
                """,
                    (
                        str(group.user_id),
                        group.description,
                        json.dumps(group.data) if group.data else None,
                        json.dumps(group.meta) if group.meta else None,
                        json.dumps(group.permissions) if group.permissions else None,
                        int(time.time()),
                        group.name,
                    ),
                )
            else:
                # Insert new group
                self.cursor.execute(
                    """
                    INSERT INTO [group] (
                        id, user_id, name, description, data, meta, permissions,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(group.id),
                        str(group.user_id),
                        group.name,
                        group.description,
                        json.dumps(group.data) if group.data else None,
                        json.dumps(group.meta) if group.meta else None,
                        json.dumps(group.permissions) if group.permissions else None,
                        int(time.time()),
                        int(time.time()),
                    ),
                )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to upsert group: {e}")

    def upsert_group_member(self, group_member: GroupMemberEntity) -> None:
        """Upsert a group member into the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check if group member exists
            self.cursor.execute(
                """
                SELECT id FROM group_member
                WHERE group_id = ? AND user_id = ?
            """,
                (str(group_member.group_id), str(group_member.user_id)),
            )

            existing_member = self.cursor.fetchone()

            if existing_member:
                # Update existing group member
                self.cursor.execute(
                    """
                    UPDATE group_member SET
                        updated_at = ?
                    WHERE group_id = ? AND user_id = ?
                """,
                    (
                        int(time.time()),
                        str(group_member.group_id),
                        str(group_member.user_id),
                    ),
                )
            else:
                # Insert new group member
                self.cursor.execute(
                    """
                    INSERT INTO group_member (
                        id, group_id, user_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        str(group_member.id),
                        str(group_member.group_id),
                        str(group_member.user_id),
                        int(time.time()),
                        int(time.time()),
                    ),
                )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to upsert group member: {e}")

    def get_group_by_name(self, name: str) -> GroupEntity | None:
        """Get a group by name."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT
                    id, user_id, name, description, data, meta, permissions,
                    created_at, updated_at
                FROM [group] WHERE name = ?
            """,
                (name,),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return GroupEntity(
                id=UUID(row[0]),
                user_id=UUID(row[1]),
                name=row[2],
                description=row[3],
                data=json.loads(row[4]) if row[4] else None,
                meta=json.loads(row[5]) if row[5] else None,
                permissions=json.loads(row[6]) if row[6] else None,
                created_at=row[7],
                updated_at=row[8],
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get group by name: {e}")

    def get_group_by_id(self, group_id: UUID) -> GroupEntity | None:
        """Get a group by ID."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT
                    id, user_id, name, description, data, meta, permissions,
                    created_at, updated_at
                FROM [group] WHERE id = ?
            """,
                (str(group_id),),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return GroupEntity(
                id=UUID(row[0]),
                user_id=UUID(row[1]),
                name=row[2],
                description=row[3],
                data=json.loads(row[4]) if row[4] else None,
                meta=json.loads(row[5]) if row[5] else None,
                permissions=json.loads(row[6]) if row[6] else None,
                created_at=row[7],
                updated_at=row[8],
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get group by ID: {e}")

    def get_group_members_for_user(self, user_id: UUID) -> list[GroupMemberEntity]:
        """Get all group memberships for a user."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT id, group_id, user_id, created_at, updated_at
                FROM group_member WHERE user_id = ?
            """,
                (str(user_id),),
            )

            rows = self.cursor.fetchall()
            return [
                GroupMemberEntity(
                    id=UUID(row[0]),
                    group_id=UUID(row[1]),
                    user_id=UUID(row[2]),
                    created_at=row[3] if row[3] else None,
                    updated_at=row[4] if row[4] else None,
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get group members for user: {e}")

    def get_user_by_email_for_group(self, email: str) -> UUID | None:
        """Get user ID by email for group membership."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
            row = self.cursor.fetchone()
            return UUID(row[0]) if row else None
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get user ID by email: {e}")

    # Model operations
    def upsert_model(self, model: ModelEntity) -> None:
        """Upsert a model into the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check which columns exist in the model table
            self.cursor.execute("PRAGMA table_info(model)")
            columns = [row[1] for row in self.cursor.fetchall()]
            logger.debug(f"Model table columns: {columns}")

            # Check if model exists
            self.cursor.execute("SELECT id FROM model WHERE id = ?", (model.id,))
            existing_model = self.cursor.fetchone()

            if existing_model:
                # Build UPDATE query dynamically based on available columns
                updates = []
                params = []

                # Map of column names to model attributes
                column_map = {
                    "user_id": str(model.user_id) if model.user_id else None,
                    "base_model_id": model.base_model_id,
                    "name": model.name,
                    "params": json.dumps(model.params),
                    "meta": json.dumps(model.meta),
                    "access_control": json.dumps(model.access_control)
                    if model.access_control
                    else None,
                    "is_active": model.is_active,
                    "updated_at": int(time.time()),
                }

                for col_name, col_value in column_map.items():
                    if col_name in columns:
                        updates.append(f"{col_name} = ?")
                        params.append(col_value)

                if updates:
                    query = f"UPDATE model SET {', '.join(updates)} WHERE id = ?"
                    params.append(model.id)
                    logger.debug(f"Executing UPDATE query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.warning(
                        f"No updatable columns found in model table for {model.id}"
                    )

            else:
                # Build INSERT query dynamically based on available columns
                insert_columns = []
                insert_values = []
                params = []

                # Map of column names to model attributes for INSERT
                insert_map = {
                    "id": model.id,
                    "user_id": str(model.user_id) if model.user_id else None,
                    "base_model_id": model.base_model_id,
                    "name": model.name,
                    "params": json.dumps(model.params),
                    "meta": json.dumps(model.meta),
                    "access_control": json.dumps(model.access_control)
                    if model.access_control
                    else None,
                    "is_active": model.is_active,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }

                for col_name, col_value in insert_map.items():
                    if col_name in columns:
                        insert_columns.append(col_name)
                        insert_values.append("?")
                        params.append(col_value)

                if insert_columns:
                    columns = ", ".join(insert_columns)
                    values = ", ".join(insert_values)
                    query = f"INSERT INTO model ({columns}) VALUES ({values})"
                    logger.debug(f"Executing INSERT query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.error("No insertable columns found in model table")
                    raise DatabaseOperationError(
                        "No columns available for model insertion"
                    )

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise DatabaseOperationError(f"Failed to upsert model: {e}")

    def get_model_by_id(self, model_id: str) -> ModelEntity | None:
        """Get a model by ID."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT
                    id, user_id, base_model_id, name, params, meta,
                    access_control, is_active, created_at, updated_at
                FROM model WHERE id = ?
            """,
                (model_id,),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return ModelEntity(
                id=row[0],
                user_id=UUID(row[1]) if row[1] else None,
                base_model_id=row[2],
                name=row[3],
                params=json.loads(row[4]),
                meta=json.loads(row[5]),
                access_control=json.loads(row[6]) if row[6] else None,
                is_active=bool(row[7]),
                created_at=row[8],
                updated_at=row[9],
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get model by ID: {e}")

    # Reset operations
    def clear_table(self, table_name: str) -> None:
        """Clear all data from a specific table."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        if table_name not in self.get_managed_tables():
            raise DatabaseOperationError(
                f"Table {table_name} is not managed by this tool"
            )

        try:
            # Check if table exists before trying to clear it
            if not self.table_exists(table_name):
                return  # Table doesn't exist, nothing to clear

            # Handle reserved keywords by quoting table names
            if table_name == "group":
                self.cursor.execute("DELETE FROM [group]")
            else:
                self.cursor.execute(f"DELETE FROM {table_name}")
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to clear table {table_name}: {e}")

    def clear_managed_tables(self) -> None:
        """Clear all managed tables (users, groups, models, etc.)."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Clear all managed tables directly without nested transaction
            for table in self.get_managed_tables():
                self.clear_table(table)

        except Exception as e:
            raise DatabaseOperationError(f"Failed to clear managed tables: {e}")

    # Utility methods
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """,
                (table_name,),
            )
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            # If the database is corrupted or doesn't exist, consider table as
            # not existing
            logger.debug(f"Failed to check if table {table_name} exists: {e}")
            return False

    def get_managed_tables(self) -> list[str]:
        """Get list of tables managed by this tool."""
        return [
            "auth",
            "user",
            "group",
            "group_member",
            "model",
            "prompt",
            "tool",
            "config",
        ]

    # Config operations
    def upsert_config(self, config_data: dict) -> None:
        """Upsert configuration data into the config table."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            # Check if config table exists, create if not
            if not self.table_exists("config"):
                self._create_config_table()

            # Check if config entry exists
            self.cursor.execute("SELECT id FROM config WHERE id = 1")
            existing_config = self.cursor.fetchone()

            if existing_config:
                # Update existing config
                self.cursor.execute(
                    """
                    UPDATE config SET
                        data = ?,
                        version = version + 1,
                        updated_at = ?
                    WHERE id = 1
                """,
                    (
                        json.dumps(config_data),
                        int(time.time()),
                    ),
                )
            else:
                # Insert new config
                self.cursor.execute(
                    """
                    INSERT INTO config (id, data, version, created_at, updated_at)
                    VALUES (1, ?, 1, ?, ?)
                """,
                    (
                        json.dumps(config_data),
                        int(time.time()),
                        int(time.time()),
                    ),
                )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to upsert config: {e}")

    def get_config(self) -> dict | None:
        """Get current configuration from the config table."""
        if not self.connection:
            raise DatabaseOperationError("Not connected to database")

        try:
            self.cursor.execute(
                """
                SELECT data FROM config WHERE id = 1
            """,
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            return json.loads(row[0])
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get config: {e}")

    def _create_config_table(self) -> None:
        """Create the config table if it doesn't exist."""
        try:
            self.cursor.execute(
                """
                CREATE TABLE config (
                    id INTEGER PRIMARY KEY,
                    data JSON NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER
                )
            """
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to create config table: {e}")

    # Database validation and replacement methods
    def database_exists(self) -> bool:
        """Check if the database file exists."""
        return os.path.exists(self.database_path)

    def validate_database_structure(self) -> bool:
        """Validate that the database has the required structure.

        Returns:
            True if database structure is valid, False otherwise

        Raises:
            DatabaseValidationError: If database connection fails
        """
        if not self.database_exists():
            logger.debug(f"Database file does not exist: {self.database_path}")
            return False

        try:
            # Try to connect to the database
            self.connect()

            # Check if required tables exist
            # Only check for core tables that are essential for bootstrap operations
            required_tables = ["auth", "user", "group", "group_member", "model"]
            for table in required_tables:
                if not self.table_exists(table):
                    logger.debug(f"Required table missing: {table}")
                    return False

            logger.debug("Database structure validation passed")
            return True

        except sqlite3.Error as e:
            logger.debug(f"Database validation failed due to SQLite error: {e}")
            return False
        except Exception as e:
            logger.debug(f"Database validation failed: {e}")
            return False
        finally:
            if self.connection:
                self.disconnect()

    def is_database_corrupted(self) -> bool:
        """Check if the database is corrupted.

        Returns:
            True if database is corrupted, False otherwise

        Raises:
            DatabaseValidationError: If database validation fails
        """
        if not self.database_exists():
            logger.debug("Database file does not exist - considering as corrupted")
            return True

        try:
            # Try to connect to the database and perform a simple query
            # If connection or query fails, consider it corrupted
            test_conn = sqlite3.connect(self.database_path)
            cursor = test_conn.cursor()

            # Try to query sqlite_master to detect corruption
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            cursor.fetchone()

            test_conn.close()
            logger.debug("Database connection and query successful - not corrupted")
            return False

        except sqlite3.Error as e:
            logger.debug(f"Database query failed - considering as corrupted: {e}")
            return True
        except Exception as e:
            logger.debug(f"Unexpected error checking database corruption: {e}")
            return True

    def get_resource_database_path(self) -> str:
        """Get the path to the resource database file.

        Returns:
            Path to the resource database file

        Raises:
            DatabaseReplacementError: If resource database is not found
        """
        try:
            resource_db_path = get_resource_path("webui-0.7.2.db")
            logger.debug(f"Found resource database: {resource_db_path}")
            return resource_db_path
        except (FileNotFoundError, ImportError) as e:
            logger.error(f"Resource database not found: {e}")
            raise DatabaseReplacementError(f"Resource database not found: {e}") from e

    def replace_with_resource_database(self) -> None:
        """Replace the target database with the resource database.

        Raises:
            DatabaseReplacementError: If replacement fails
        """
        logger.info(
            f"Attempting to replace database {self.database_path} with resource database"  # noqa: E501
        )

        try:
            # Get resource database path
            resource_db_path = self.get_resource_database_path()

            # Ensure target directory exists
            target_dir = os.path.dirname(self.database_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                logger.debug(f"Created target directory: {target_dir}")

            # Copy resource database to target location (overwrite if exists)
            logger.info(
                f"Copying resource database from {resource_db_path} to {self.database_path}"  # noqa: E501
            )
            shutil.copy2(resource_db_path, self.database_path)

            logger.info("Successfully replaced database with resource database")

        except Exception as e:
            logger.error(f"Failed to replace database with resource database: {e}")
            raise DatabaseReplacementError(f"Failed to replace database: {e}")

    def validate_and_repair_database(self, reset_active: bool) -> None:
        """Validate database and repair if needed using resource database.

        Args:
            reset_active: Whether reset option is active

        Raises:
            DatabaseValidationError: If database is invalid and cannot be repaired
            DatabaseReplacementError: If database replacement fails
        """
        # Validate database path is not None
        if self.database_path is None:
            logger.error("Database path is None")
            raise DatabaseValidationError("Database path cannot be None")

        logger.info(
            f"Starting database validation and repair process for: {self.database_path}"
        )

        # Check if database exists
        if not self.database_exists():
            logger.warning("Database file does not exist")

            if reset_active:
                logger.info("Reset option is active - replacing with resource database")
                self.replace_with_resource_database()
                return
            else:
                logger.error(
                    "Database file does not exist and reset option is not active"
                )
                raise DatabaseValidationError("Database file does not exist")

        # Check if database is corrupted
        if self.is_database_corrupted():
            logger.warning("Database is corrupted")

            if reset_active:
                logger.info(
                    "Reset option is active - replacing corrupted database with resource database"  # noqa: E501
                )
                self.replace_with_resource_database()
                return
            else:
                logger.error("Database is corrupted and reset option is not active")
                raise DatabaseCorruptionError("Database is corrupted")

        # Validate database structure
        try:
            if not self.validate_database_structure():
                logger.warning("Database structure is invalid")

                if reset_active:
                    logger.info(
                        "Reset option is active - replacing database with invalid structure"  # noqa: E501
                    )
                    self.replace_with_resource_database()
                    return
                else:
                    logger.error(
                        "Database structure is invalid and reset option is not active"
                    )
                    raise DatabaseValidationError("Database structure is invalid")
        except DatabaseValidationError as e:
            logger.warning(f"Database validation failed: {e}")

            if reset_active:
                logger.info(
                    "Reset option is active - replacing database after validation failure"  # noqa: E501
                )
                self.replace_with_resource_database()
                return
            else:
                logger.error(
                    "Database validation failed and reset option is not active"
                )
                raise DatabaseValidationError(f"Database validation failed: {e}")

        logger.info("Database validation passed - no repair needed")
