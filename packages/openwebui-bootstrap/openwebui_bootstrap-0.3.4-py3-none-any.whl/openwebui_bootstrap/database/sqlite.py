"""SQLite database implementation for Open WebUI Bootstrap."""

import json
import sqlite3
import time
from uuid import UUID

from ..exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTransactionError,
)
from ..logging_config import get_logger
from ..models import (
    AuthEntity,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
    UserEntity,
)
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
                    query = f"INSERT INTO user ({', '.join(insert_columns)}) VALUES ({', '.join(insert_values)})"
                    logger.debug(f"Executing INSERT query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.error(f"No insertable columns found in user table")
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
                    id, username, name, email, role, profile_image_url, profile_banner_image_url, bio,
                    gender, date_of_birth, timezone, presence_state, status_emoji, status_message, status_expires_at,
                    last_active_at, updated_at, created_at, settings, info, oauth, permissions
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
                    id, username, name, email, role, profile_image_url, profile_banner_image_url, bio,
                    gender, date_of_birth, timezone, presence_state, status_emoji, status_message, status_expires_at,
                    last_active_at, updated_at, created_at, settings, info, oauth, permissions
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
                    query = f"INSERT INTO model ({', '.join(insert_columns)}) VALUES ({', '.join(insert_values)})"
                    logger.debug(f"Executing INSERT query: {query}")
                    self.cursor.execute(query, params)
                else:
                    logger.error(f"No insertable columns found in model table")
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
            raise DatabaseOperationError(f"Failed to check if table exists: {e}")

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
