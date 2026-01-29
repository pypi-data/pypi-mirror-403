"""Additional tests to improve coverage for database base module."""

import pytest

from openwebui_bootstrap.database.sqlite import SQLiteDatabase


def test_database_table_operations(sqlite_database: SQLiteDatabase):
    """Test database table operations."""
    # Test table_exists for existing tables
    assert sqlite_database.table_exists("user") is True
    assert sqlite_database.table_exists("auth") is True
    assert sqlite_database.table_exists("group") is True
    assert sqlite_database.table_exists("model") is True

    # Test table_exists for non-existing table
    assert sqlite_database.table_exists("nonexistent_table") is False

    # Test get_managed_tables
    managed_tables = sqlite_database.get_managed_tables()
    assert isinstance(managed_tables, list)
    assert "user" in managed_tables
    assert "auth" in managed_tables
    assert "group" in managed_tables
    assert "model" in managed_tables

    # Test clear_table for managed table
    # First, insert a test user
    import time
    from uuid import uuid4

    from openwebui_bootstrap.models import UserEntity

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
        api_key=None,
        settings=None,
        info=None,
        oauth_sub=None,
    )
    sqlite_database.upsert_user(user)

    # Verify user was inserted
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user is not None

    # Clear the user table
    sqlite_database.clear_table("user")

    # Verify user was deleted
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user is None

    # Test clear_managed_tables
    # Insert test data again
    sqlite_database.upsert_user(user)

    # Clear all managed tables
    sqlite_database.clear_managed_tables()

    # Verify all data was cleared
    retrieved_user = sqlite_database.get_user_by_email("test@example.com")
    assert retrieved_user is None
