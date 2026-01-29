"""Pytest fixtures for Open WebUI Bootstrap tests."""

import os
import sqlite3
import tempfile
from collections.abc import Generator

import pytest

from openwebui_bootstrap.config_manager import ConfigManager
from openwebui_bootstrap.database.sqlite import SQLiteDatabase


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary SQLite database for testing."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    try:
        # Create the database and tables
        _create_test_database(db_path)
        yield db_path
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sqlite_database(temp_db_path: str) -> SQLiteDatabase:
    """Create a SQLite database instance for testing."""
    db = SQLiteDatabase(temp_db_path)
    db.connect()
    yield db
    db.disconnect()


@pytest.fixture
def config_manager(sqlite_database: SQLiteDatabase) -> ConfigManager:
    """Create a config manager instance for testing."""
    return ConfigManager(sqlite_database)


def _create_test_database(db_path: str) -> None:
    """Create test database with required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create auth table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth (
            id TEXT PRIMARY KEY,
            email TEXT,
            password TEXT,
            active BOOLEAN
        )
    """)

    # Create user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id TEXT PRIMARY KEY,
            username TEXT,
            name TEXT,
            email TEXT,
            role TEXT,
            profile_image_url TEXT,
            profile_banner_image_url TEXT,
            bio TEXT,
            gender TEXT,
            date_of_birth TEXT,
            timezone TEXT,
            presence_state TEXT,
            status_emoji TEXT,
            status_message TEXT,
            status_expires_at INTEGER,
            last_active_at INTEGER,
            updated_at INTEGER,
            created_at INTEGER,
            settings TEXT,
            info TEXT,
            oauth TEXT,
            permissions TEXT
        )
    """)

    # Create group table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS [group] (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            description TEXT,
            data TEXT,
            meta TEXT,
            permissions TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    # Create group_member table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_member (
            id TEXT PRIMARY KEY,
            group_id TEXT,
            user_id TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    # Create model table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            base_model_id TEXT,
            name TEXT,
            params TEXT,
            meta TEXT,
            access_control TEXT,
            is_active BOOLEAN,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    # Create prompt table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt (
            command TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            content TEXT,
            timestamp INTEGER,
            access_control TEXT
        )
    """)

    # Create tool table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            content TEXT,
            specs TEXT,
            meta TEXT,
            valves TEXT,
            access_control TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    conn.commit()
    conn.close()
