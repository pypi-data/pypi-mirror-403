"""Comprehensive test suite for SQLite database operations to achieve 90%+ coverage."""

import pytest
import time
from uuid import uuid4, UUID

from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.models import (
    UserEntity,
    AuthEntity,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
)
from openwebui_bootstrap.exceptions import (
    DatabaseOperationError,
    DatabaseTransactionError,
)


class TestSQLiteComprehensive:
    """Comprehensive SQLite database tests."""

    @pytest.fixture
    def db(self, temp_db_path: str):
        """Create a SQLite database instance for testing."""
        db = SQLiteDatabase(temp_db_path)
        db.connect()
        yield db
        db.disconnect()

    def test_connection_operations(self, db: SQLiteDatabase):
        """Test database connection and disconnection."""
        # Verify connection is established
        assert db.connection is not None
        assert db.cursor is not None

        # Test disconnect
        db.disconnect()
        assert db.connection is None
        assert db.cursor is None

        # Reconnect for other tests
        db.connect()

    def test_transaction_operations(self, db: SQLiteDatabase):
        """Test transaction operations."""
        # Test begin transaction
        db.begin_transaction()

        # Test commit
        db.commit_transaction()

        # Test rollback
        db.begin_transaction()
        db.rollback_transaction()

        # Test transaction errors
        db.disconnect()
        with pytest.raises(DatabaseTransactionError):
            db.begin_transaction()
        with pytest.raises(DatabaseTransactionError):
            db.commit_transaction()
        with pytest.raises(DatabaseTransactionError):
            db.rollback_transaction()
        db.connect()

    def test_user_operations(self, db: SQLiteDatabase):
        """Test user CRUD operations."""
        # Create test user
        user_id = uuid4()
        user = UserEntity(
            id=user_id,
            username="testuser",
            name="Test User",
            email="test@example.com",
            role="Admin",
            profile_image_url=None,
            bio="Test bio",
            gender="male",
            date_of_birth="1990-01-01",
            timezone="UTC",
            presence_state="online",
            status_emoji="👋",
            status_message="Hello",
            status_expires_at=0,
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
            api_key="test-key",
            settings={"theme": "dark"},
            info={"location": "Test"},
            oauth={"provider": "github"},
            oauth_sub="12345",
            permissions={"admin": True},
        )

        # Test upsert (insert)
        db.upsert_user(user)

        # Test get by email
        retrieved_user = db.get_user_by_email("test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.name == "Test User"
        assert retrieved_user.settings["theme"] == "dark"
        assert retrieved_user.permissions["admin"] is True

        # Test get by ID
        retrieved_user = db.get_user_by_id(user_id)
        assert retrieved_user is not None
        assert retrieved_user.id == user_id

        # Test update (upsert again with different data)
        user.name = "Updated Name"
        user.settings = {"theme": "light"}
        db.upsert_user(user)

        retrieved_user = db.get_user_by_email("test@example.com")
        assert retrieved_user.name == "Updated Name"
        assert retrieved_user.settings["theme"] == "light"

        # Test get non-existent user
        assert db.get_user_by_email("nonexistent@example.com") is None
        assert db.get_user_by_id(uuid4()) is None

    def test_auth_operations(self, db: SQLiteDatabase):
        """Test authentication operations."""
        # Create test auth
        auth_id = uuid4()
        auth = AuthEntity(
            id=auth_id,
            email="test@example.com",
            password="hashed_password_123",
            active=True,
        )

        # Test upsert
        db.upsert_auth(auth)

        # Test get by email
        retrieved_auth = db.get_auth_by_email("test@example.com")
        assert retrieved_auth is not None
        assert retrieved_auth.email == "test@example.com"
        assert retrieved_auth.password == "hashed_password_123"
        assert retrieved_auth.active is True

        # Test update
        auth.active = False
        db.upsert_auth(auth)

        retrieved_auth = db.get_auth_by_email("test@example.com")
        assert retrieved_auth.active is False

        # Test get non-existent auth
        assert db.get_auth_by_email("nonexistent@example.com") is None

    def test_group_operations(self, db: SQLiteDatabase):
        """Test group operations."""
        # First create a user for group ownership
        user_id = uuid4()
        user = UserEntity(
            id=user_id,
            username="groupowner",
            name="Group Owner",
            email="owner@example.com",
            role="Admin",
            profile_image_url=None,
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
        )
        db.upsert_user(user)

        # Create test group
        group_id = uuid4()
        group = GroupEntity(
            id=group_id,
            user_id=user_id,
            name="test_group",
            description="Test group description",
            data={"key": "value"},
            meta={"version": "1.0"},
            permissions={"read": True, "write": True},
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        # Test upsert group
        db.upsert_group(group)

        # Test get by name
        retrieved_group = db.get_group_by_name("test_group")
        assert retrieved_group is not None
        assert retrieved_group.name == "test_group"
        assert retrieved_group.description == "Test group description"
        assert retrieved_group.data["key"] == "value"
        assert "read" in retrieved_group.permissions

        # Test get by ID
        retrieved_group = db.get_group_by_id(group_id)
        assert retrieved_group is not None
        assert retrieved_group.id == group_id

        # Test update
        group.description = "Updated description"
        db.upsert_group(group)

        retrieved_group = db.get_group_by_name("test_group")
        assert retrieved_group.description == "Updated description"

        # Test get non-existent group
        assert db.get_group_by_name("nonexistent") is None
        assert db.get_group_by_id(uuid4()) is None

    def test_group_member_operations(self, db: SQLiteDatabase):
        """Test group member operations."""
        # Create users
        user1_id = uuid4()
        user1 = UserEntity(
            id=user1_id,
            username="user1",
            name="User 1",
            email="user1@example.com",
            role="User",
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
        )
        db.upsert_user(user1)

        user2_id = uuid4()
        user2 = UserEntity(
            id=user2_id,
            username="user2",
            name="User 2",
            email="user2@example.com",
            role="User",
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
        )
        db.upsert_user(user2)

        # Create group
        group_id = uuid4()
        group = GroupEntity(
            id=group_id,
            user_id=user1_id,
            name="members_group",
            description="Group with members",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        db.upsert_group(group)

        # Create group members
        member1 = GroupMemberEntity(
            id=uuid4(),
            group_id=group_id,
            user_id=user1_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        member2 = GroupMemberEntity(
            id=uuid4(),
            group_id=group_id,
            user_id=user2_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        # Test upsert members
        db.upsert_group_member(member1)
        db.upsert_group_member(member2)

        # Test get members for user
        members = db.get_group_members_for_user(user1_id)
        assert len(members) == 1
        assert members[0].group_id == group_id

        members = db.get_group_members_for_user(user2_id)
        assert len(members) == 1
        assert members[0].group_id == group_id

        # Test get user by email for group
        user_id = db.get_user_by_email_for_group("user1@example.com")
        assert user_id == user1_id

        assert db.get_user_by_email_for_group("nonexistent@example.com") is None

    def test_model_operations(self, db: SQLiteDatabase):
        """Test model operations."""
        # Create test model
        model = ModelEntity(
            id="test-model-123",
            user_id=uuid4(),
            base_model_id="gpt-4",
            name="Test Model",
            params={"context_size": 4096, "temperature": 0.7},
            meta={
                "capabilities": {"vision": True, "web_search": False},
                "default_capabilities": {"web_search": True},
            },
            access_control={"public": True},
            is_active=True,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        # Test upsert
        db.upsert_model(model)

        # Test get by ID
        retrieved_model = db.get_model_by_id("test-model-123")
        assert retrieved_model is not None
        assert retrieved_model.id == "test-model-123"
        assert retrieved_model.name == "Test Model"
        assert retrieved_model.params["context_size"] == 4096
        assert retrieved_model.meta["capabilities"]["vision"] is True
        assert retrieved_model.access_control["public"] is True

        # Test update
        model.name = "Updated Model"
        model.params["context_size"] = 8192
        db.upsert_model(model)

        retrieved_model = db.get_model_by_id("test-model-123")
        assert retrieved_model.name == "Updated Model"
        assert retrieved_model.params["context_size"] == 8192

        # Test get non-existent model
        assert db.get_model_by_id("nonexistent-model") is None

    def test_config_operations(self, db: SQLiteDatabase):
        """Test configuration operations."""
        # Test get config from empty database (config table doesn't exist yet)
        try:
            config = db.get_config()
            assert config is None
        except DatabaseOperationError:
            # Config table doesn't exist, which is expected
            pass

        # Test upsert config (this will create the config table)
        test_config = {
            "ui": {"enable_signup": True, "default_locale": "en"},
            "user": {"permissions": {"workspace": {"models": True}}},
        }
        db.upsert_config(test_config)

        # Test get config after insertion
        config = db.get_config()
        assert config is not None
        assert "ui" in config
        assert config["ui"]["enable_signup"] is True
        assert config["ui"]["default_locale"] == "en"

        # Test update config
        updated_config = {
            "ui": {"enable_signup": False, "default_locale": "de"},
            "user": {"permissions": {"workspace": {"models": False}}},
        }
        db.upsert_config(updated_config)

        # Verify config was updated
        config = db.get_config()
        assert config["ui"]["enable_signup"] is False
        assert config["ui"]["default_locale"] == "de"
        assert config["user"]["permissions"]["workspace"]["models"] is False

    def test_table_operations(self, db: SQLiteDatabase):
        """Test table existence and management operations."""
        # Test table_exists for existing tables
        assert db.table_exists("user") is True
        assert db.table_exists("auth") is True
        assert db.table_exists("group") is True
        assert db.table_exists("model") is True

        # Config table doesn't exist until first upsert_config call
        # Create config table first
        db.upsert_config({"test": "data"})
        assert db.table_exists("config") is True

        # Test table_exists for non-existing table
        assert db.table_exists("nonexistent_table") is False

        # Test get_managed_tables
        managed_tables = db.get_managed_tables()
        assert isinstance(managed_tables, list)
        assert "user" in managed_tables
        assert "auth" in managed_tables
        assert "group" in managed_tables
        assert "model" in managed_tables
        assert "config" in managed_tables

    def test_clear_operations(self, db: SQLiteDatabase):
        """Test table clearing operations."""
        # First, insert test data
        user = UserEntity(
            id=uuid4(),
            username="todelete",
            name="To Delete",
            email="delete@example.com",
            role="User",
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
        )
        db.upsert_user(user)

        # Verify data exists
        assert db.get_user_by_email("delete@example.com") is not None

        # Test clear_table for managed table
        db.clear_table("user")

        # Verify data was cleared
        assert db.get_user_by_email("delete@example.com") is None

        # Test clear_table for non-managed table (should raise error)
        with pytest.raises(DatabaseOperationError):
            db.clear_table("nonexistent_table")

        # Test clear_managed_tables
        # Insert data again
        db.upsert_user(user)

        # Clear all managed tables
        db.clear_managed_tables()

        # Verify all data was cleared
        assert db.get_user_by_email("delete@example.com") is None

    def test_error_handling(self, db: SQLiteDatabase):
        """Test error handling scenarios."""
        # Test operations without connection
        db.disconnect()

        with pytest.raises(DatabaseOperationError):
            db.upsert_user(
                UserEntity(
                    id=uuid4(),
                    username="test",
                    name="Test",
                    email="test@example.com",
                    role="User",
                    last_active_at=0,
                    updated_at=int(time.time()),
                    created_at=int(time.time()),
                )
            )

        with pytest.raises(DatabaseOperationError):
            db.get_user_by_email("test@example.com")

        with pytest.raises(DatabaseOperationError):
            db.upsert_auth(
                AuthEntity(
                    id=uuid4(),
                    email="test@example.com",
                    password="pass",
                    active=True,
                )
            )

        with pytest.raises(DatabaseOperationError):
            db.get_auth_by_email("test@example.com")

        with pytest.raises(DatabaseOperationError):
            db.upsert_group(
                GroupEntity(
                    id=uuid4(),
                    user_id=uuid4(),
                    name="test",
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                )
            )

        with pytest.raises(DatabaseOperationError):
            db.get_group_by_name("test")

        with pytest.raises(DatabaseOperationError):
            db.upsert_model(
                ModelEntity(
                    id="test",
                    base_model_id="gpt-4",
                    name="Test",
                    params={},
                    meta={},
                    is_active=True,
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                )
            )

        with pytest.raises(DatabaseOperationError):
            db.get_model_by_id("test")

        with pytest.raises(DatabaseOperationError):
            db.get_config()

        with pytest.raises(DatabaseOperationError):
            db.table_exists("user")

        with pytest.raises(DatabaseOperationError):
            db.clear_table("user")

        # Reconnect for other tests
        db.connect()

    def test_edge_cases(self, db: SQLiteDatabase):
        """Test edge cases and special scenarios."""
        # Test user with None values
        user = UserEntity(
            id=uuid4(),
            username="minimal",
            name="Minimal User",
            email="minimal@example.com",
            role="User",
            profile_image_url=None,
            bio=None,
            gender=None,
            date_of_birth=None,
            timezone=None,
            presence_state=None,
            status_emoji=None,
            status_message=None,
            status_expires_at=None,
            last_active_at=0,
            updated_at=int(time.time()),
            created_at=int(time.time()),
            api_key=None,
            settings=None,
            info=None,
            oauth=None,
            oauth_sub=None,
            permissions=None,
        )
        db.upsert_user(user)

        retrieved = db.get_user_by_email("minimal@example.com")
        assert retrieved is not None
        assert retrieved.email == "minimal@example.com"

        # Test model with None user_id
        model = ModelEntity(
            id="minimal-model",
            user_id=None,
            base_model_id="gpt-3.5",
            name="Minimal Model",
            params={"context_size": 2048},
            meta={"capabilities": {}},
            is_active=True,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        db.upsert_model(model)

        retrieved = db.get_model_by_id("minimal-model")
        assert retrieved is not None
        assert retrieved.name == "Minimal Model"
        assert retrieved.user_id is None

        # Test group with None values
        group = GroupEntity(
            id=uuid4(),
            user_id=uuid4(),
            name="minimal_group",
            description=None,
            data=None,
            meta=None,
            permissions=None,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        db.upsert_group(group)

        retrieved = db.get_group_by_name("minimal_group")
        assert retrieved is not None
        assert retrieved.name == "minimal_group"
        assert retrieved.description is None
