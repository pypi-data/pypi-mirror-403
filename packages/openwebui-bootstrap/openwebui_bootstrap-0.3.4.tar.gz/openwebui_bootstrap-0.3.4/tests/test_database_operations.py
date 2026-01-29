"""Tests for database operations to improve coverage."""

import time
from uuid import uuid4

import pytest

from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import DatabaseError
from openwebui_bootstrap.models import (
    AuthEntity,
    GroupEntity,
    GroupMemberEntity,
    ModelEntity,
    UserEntity,
)


def test_database_transaction_management(sqlite_database: SQLiteDatabase) -> None:
    """Test database transaction management."""
    # Test begin transaction
    sqlite_database.begin_transaction()

    # Test commit transaction
    sqlite_database.commit_transaction()

    # Test rollback transaction
    sqlite_database.begin_transaction()
    sqlite_database.rollback_transaction()


def test_database_error_conditions(sqlite_database: SQLiteDatabase) -> None:
    """Test database error conditions."""
    # Test error when not connected
    sqlite_database.disconnect()

    with pytest.raises(DatabaseError):
        sqlite_database.begin_transaction()

    with pytest.raises(DatabaseError):
        sqlite_database.commit_transaction()

    with pytest.raises(DatabaseError):
        sqlite_database.rollback_transaction()

    with pytest.raises(DatabaseError):
        sqlite_database.upsert_user(
            UserEntity(
                id=uuid4(),
                username="test",
                name="Test",
                email="test@example.com",
                role="User",
            )
        )

    # Reconnect
    sqlite_database.connect()


def test_database_table_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test database table operations."""
    # Test table_exists for existing tables
    assert sqlite_database.table_exists("user")
    assert sqlite_database.table_exists("auth")
    assert sqlite_database.table_exists("group")
    assert sqlite_database.table_exists("model")

    # Test table_exists for non-existing table
    assert not sqlite_database.table_exists("nonexistent_table")

    # Test get_managed_tables
    managed_tables = sqlite_database.get_managed_tables()
    assert isinstance(managed_tables, list)
    assert len(managed_tables) > 0
    assert "user" in managed_tables
    assert "auth" in managed_tables


def test_database_clear_table_error_handling(sqlite_database: SQLiteDatabase) -> None:
    """Test database clear table error handling."""
    # Test clearing non-managed table
    with pytest.raises(DatabaseError):
        sqlite_database.clear_table("nonexistent_table")

    # Test clearing invalid table name
    with pytest.raises(DatabaseError):
        sqlite_database.clear_table("invalid_table_name")


def test_database_comprehensive_user_operations(
    sqlite_database: SQLiteDatabase,
) -> None:
    """Test comprehensive user operations."""
    # Create and insert a user
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="Admin",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )

    # Insert user
    sqlite_database.upsert_user(user)

    # Retrieve user
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user is not None
    assert retrieved_user.id == user_id
    assert retrieved_user.email == "test@example.com"

    # Update user
    user.name = "Updated User"
    user.role = "User"
    sqlite_database.upsert_user(user)

    # Retrieve updated user
    updated_user = sqlite_database.get_user_by_email("test@example.com")
    assert updated_user.name == "Updated User"
    assert updated_user.role == "User"

    # Test get_user_by_email_for_group
    user_id_result = sqlite_database.get_user_by_email_for_group("test@example.com")
    assert user_id_result == user_id

    # Test get_user_by_email_for_group with non-existent user
    assert (
        sqlite_database.get_user_by_email_for_group("nonexistent@example.com") is None
    )


def test_database_comprehensive_auth_operations(
    sqlite_database: SQLiteDatabase,
) -> None:
    """Test comprehensive auth operations."""
    # Create and insert auth
    auth_id = uuid4()
    auth = AuthEntity(
        id=auth_id,
        email="auth_test@example.com",
        password="hashed_password",
        active=True,
    )

    # Insert auth
    sqlite_database.upsert_auth(auth)

    # Retrieve auth
    retrieved_auth = sqlite_database.get_auth_by_email("auth_test@example.com")
    assert retrieved_auth is not None
    assert retrieved_auth.id == auth_id
    assert retrieved_auth.email == "auth_test@example.com"
    assert retrieved_auth.active is True

    # Update auth
    auth.active = False
    auth.password = "new_hashed_password"
    sqlite_database.upsert_auth(auth)

    # Retrieve updated auth
    updated_auth = sqlite_database.get_auth_by_email("auth_test@example.com")
    assert updated_auth.active is False
    assert updated_auth.password == "new_hashed_password"

    # Test get_auth_by_email with non-existent auth
    assert sqlite_database.get_auth_by_email("nonexistent@example.com") is None


def test_database_comprehensive_group_operations(
    sqlite_database: SQLiteDatabase,
) -> None:
    """Test comprehensive group operations."""
    # First create a user for group operations
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="group_test_user",
        name="Group Test User",
        email="group_test@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )
    sqlite_database.upsert_user(user)

    # Create and insert a group
    group_id = uuid4()
    group = GroupEntity(
        id=group_id,
        user_id=user_id,
        name="test_group",
        description="Test Group",
        data=None,
        meta=None,
        permissions={"import_models": True, "export_models": False},
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    # Insert group
    sqlite_database.upsert_group(group)

    # Retrieve group
    retrieved_group = sqlite_database.get_group_by_name("test_group")
    assert retrieved_group is not None
    assert retrieved_group.id == group_id
    assert retrieved_group.name == "test_group"
    assert retrieved_group.permissions["import_models"] is True

    # Update group
    group.description = "Updated Test Group"
    group.permissions["export_models"] = True
    sqlite_database.upsert_group(group)

    # Retrieve updated group
    updated_group = sqlite_database.get_group_by_name("test_group")
    assert updated_group.description == "Updated Test Group"
    assert updated_group.permissions["export_models"] is True

    # Test get_group_by_name with non-existent group
    assert sqlite_database.get_group_by_name("nonexistent_group") is None


def test_database_comprehensive_model_operations(
    sqlite_database: SQLiteDatabase,
) -> None:
    """Test comprehensive model operations."""
    # Create and insert a model
    model = ModelEntity(
        id="test_model",
        user_id=None,
        base_model_id=None,
        name="Test Model",
        params={
            "context_size": 8192,
            "system_prompt": "test_prompt.txt",
            "icon": "test_icon.png",
            "capabilities": ["image-recognition", "file-upload"],
            "default_capabilities": ["websearch"],
        },
        meta={"prompt_path": "/path/to/prompts", "icon_path": "/path/to/icons"},
        access_control=None,
        is_active=True,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    # Insert model
    sqlite_database.upsert_model(model)

    # Retrieve model
    retrieved_model = sqlite_database.get_model_by_id("test_model")
    assert retrieved_model is not None
    assert retrieved_model.id == "test_model"
    assert retrieved_model.name == "Test Model"
    assert retrieved_model.params["context_size"] == 8192

    # Update model
    model.name = "Updated Test Model"
    model.is_active = False
    model.params["context_size"] = 16384
    sqlite_database.upsert_model(model)

    # Retrieve updated model
    updated_model = sqlite_database.get_model_by_id("test_model")
    assert updated_model.name == "Updated Test Model"
    assert updated_model.is_active is False
    assert updated_model.params["context_size"] == 16384

    # Test get_model_by_id with non-existent model
    assert sqlite_database.get_model_by_id("nonexistent_model") is None


def test_database_group_member_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test group member operations."""
    # Create users and groups first
    user1_id = uuid4()
    user1 = UserEntity(
        id=user1_id,
        username="user1",
        name="User 1",
        email="user1@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )
    sqlite_database.upsert_user(user1)

    user2_id = uuid4()
    user2 = UserEntity(
        id=user2_id,
        username="user2",
        name="User 2",
        email="user2@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )
    sqlite_database.upsert_user(user2)

    group_id = uuid4()
    group = GroupEntity(
        id=group_id,
        user_id=user1_id,
        name="member_test_group",
        description="Group for member testing",
        data=None,
        meta=None,
        permissions={"import_models": True},
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    sqlite_database.upsert_group(group)

    # Create and insert group members
    member1 = GroupMemberEntity(
        id=uuid4(),
        group_id=group_id,
        user_id=user1_id,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    sqlite_database.upsert_group_member(member1)

    member2 = GroupMemberEntity(
        id=uuid4(),
        group_id=group_id,
        user_id=user2_id,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    sqlite_database.upsert_group_member(member2)

    # Verify group members were added (by checking user retrieval works)
    assert sqlite_database.get_user_by_email_for_group("user1@example.com") == user1_id
    assert sqlite_database.get_user_by_email_for_group("user2@example.com") == user2_id


def test_database_clear_operations(sqlite_database: SQLiteDatabase) -> None:
    """Test database clear operations."""
    # First insert some test data
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="clear_test",
        name="Clear Test User",
        email="clear_test@example.com",
        role="User",
        profile_image_url=None,
        bio=None,
        gender=None,
        date_of_birth=None,
        last_active_at=0,
        updated_at=int(time.time()),
        created_at=int(time.time()),
        settings=None,
        info=None,
    )
    sqlite_database.upsert_user(user)

    auth = AuthEntity(
        id=user_id,
        email="clear_test@example.com",
        password="test_password",
        active=True,
    )
    sqlite_database.upsert_auth(auth)

    # Verify data was inserted
    assert sqlite_database.get_user_by_email("clear_test@example.com") is not None
    assert sqlite_database.get_auth_by_email("clear_test@example.com") is not None

    # Clear individual tables
    sqlite_database.clear_table("user")
    assert sqlite_database.get_user_by_email("clear_test@example.com") is None

    sqlite_database.clear_table("auth")
    assert sqlite_database.get_auth_by_email("clear_test@example.com") is None

    # Test clear_managed_tables (should work without error on empty tables)
    sqlite_database.clear_managed_tables()
