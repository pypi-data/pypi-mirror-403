"""Comprehensive tests for RBAC (Role-Based Access Control) functionality."""

import pytest
from uuid import uuid4
from openwebui_bootstrap.models import (
    UserEntity,
    GroupEntity,
    GroupMemberEntity,
    PermissionSystemConfig,
)
from openwebui_bootstrap.permission_service import PermissionService
from openwebui_bootstrap.database.sqlite import SQLiteDatabase
from openwebui_bootstrap.exceptions import DatabaseError


@pytest.fixture
def sqlite_database(temp_db_path):
    """Create a SQLite database instance for testing using the proper fixture."""
    db = SQLiteDatabase(temp_db_path)
    db.connect()
    yield db
    db.disconnect()


@pytest.fixture
def permission_service(sqlite_database):
    """Create a permission service with a test database."""
    return PermissionService(sqlite_database)


def test_permission_service_initialization(permission_service):
    """Test that permission service initializes correctly."""
    assert permission_service is not None
    assert permission_service.database is not None


def test_get_base_permissions_for_roles(permission_service):
    """Test base permissions for different user roles."""
    # Test admin role
    admin_permissions = permission_service._get_base_permissions_for_role("admin")
    assert admin_permissions.workspace["models"] is True
    assert admin_permissions.chat["system_prompt"] is True
    assert admin_permissions.features["api_keys"] is True

    # Test user role
    user_permissions = permission_service._get_base_permissions_for_role("user")
    assert user_permissions.workspace["models"] is True
    assert user_permissions.chat["system_prompt"] is True
    assert user_permissions.features["api_keys"] is False

    # Test pending role
    pending_permissions = permission_service._get_base_permissions_for_role("pending")
    assert pending_permissions.workspace["models"] is True
    assert pending_permissions.workspace["knowledge"] is False
    assert pending_permissions.chat["system_prompt"] is False
    assert pending_permissions.chat["file_upload"] is False

    # Test unknown role
    unknown_permissions = permission_service._get_base_permissions_for_role("unknown")
    assert unknown_permissions.workspace["models"] is False
    assert unknown_permissions.chat["controls"] is False


def test_permission_merging(permission_service):
    """Test permission merging logic."""
    base_permissions = PermissionSystemConfig()
    override_permissions = {
        "workspace": {"models": False, "knowledge": True},
        "chat": {"system_prompt": True},
    }

    merged = permission_service._merge_permissions(
        base_permissions, override_permissions
    )

    # Check that base permissions are preserved where not overridden
    assert merged.workspace["prompts"] is True  # From base
    assert merged.chat["controls"] is True  # From base

    # Check that overrides are applied
    assert merged.workspace["models"] is False  # Overridden
    assert merged.workspace["knowledge"] is True  # Overridden
    assert merged.chat["system_prompt"] is True  # Overridden


def test_deep_permission_merging(permission_service):
    """Test deep merging of nested permission structures."""
    base = {
        "workspace": {"models": True, "knowledge": True, "prompts": True},
        "chat": {"controls": True, "system_prompt": False},
    }

    override = {
        "workspace": {"models": False, "tools": False},
        "features": {"api_keys": True},
    }

    result = permission_service._deep_merge_dicts(base, override)

    # Check merged structure
    assert result["workspace"]["models"] is False  # Overridden
    assert result["workspace"]["knowledge"] is True  # From base
    assert result["workspace"]["prompts"] is True  # From base
    assert result["workspace"]["tools"] is False  # Added by override
    assert result["chat"]["controls"] is True  # From base
    assert result["chat"]["system_prompt"] is False  # From base
    assert result["features"]["api_keys"] is True  # Added by override


def test_has_permission_method(permission_service):
    """Test the has_permission method."""
    # Create a test user
    user = UserEntity(
        id=uuid4(),
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    # Test default permissions for user role
    assert permission_service.has_permission(user, "workspace.models") is True
    assert permission_service.has_permission(user, "workspace.knowledge") is True
    assert permission_service.has_permission(user, "chat.system_prompt") is True
    assert permission_service.has_permission(user, "features.api_keys") is False

    # Test non-existent permission path
    assert (
        permission_service.has_permission(user, "nonexistent.path", default=False)
        is False
    )
    assert (
        permission_service.has_permission(user, "nonexistent.path", default=True)
        is True
    )


def test_user_permission_overrides(permission_service):
    """Test user-specific permission overrides."""
    user = UserEntity(
        id=uuid4(),
        username="testuser",
        name="Test User",
        email="test@example.com",
        role="pending",  # Start with restricted role
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions={
            "workspace": {"knowledge": True, "tools": True},
            "chat": {"system_prompt": True, "file_upload": True},
        },
    )

    # Test that user overrides take precedence over role-based permissions
    effective_permissions = permission_service.get_effective_permissions(user)

    # User overrides should apply (overriding pending role restrictions)
    assert effective_permissions.workspace["models"] is True  # Pending allows models
    assert effective_permissions.workspace["knowledge"] is True  # User override
    assert effective_permissions.workspace["tools"] is True  # User override
    assert effective_permissions.chat["system_prompt"] is True  # User override
    assert effective_permissions.chat["file_upload"] is True  # User override


def test_group_permission_inheritance(sqlite_database, permission_service):
    """Test permission inheritance from groups."""
    # Create test data
    user_id = uuid4()
    group_id = uuid4()

    # Create a user
    user = UserEntity(
        id=user_id,
        username="groupuser",
        name="Group User",
        email="groupuser@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    # Create a group with specific permissions
    group = GroupEntity(
        id=group_id,
        user_id=user_id,
        name="test_group",
        description="Test Group",
        data=None,
        meta=None,
        permissions={
            "workspace": {"models_import": True, "models_export": True},
            "features": {"api_keys": True, "web_search": False},
        },
        created_at=0,
        updated_at=0,
    )

    # Create group membership
    group_member = GroupMemberEntity(
        id=uuid4(), group_id=group_id, user_id=user_id, created_at=0, updated_at=0
    )

    # Save to database
    sqlite_database.upsert_user(user)
    sqlite_database.upsert_group(group)
    sqlite_database.upsert_group_member(group_member)

    # Test permission inheritance
    effective_permissions = permission_service.get_effective_permissions(user)

    # Should have base user permissions
    assert effective_permissions.workspace["models"] is True
    assert effective_permissions.chat["controls"] is True

    # Should inherit group permissions
    assert effective_permissions.workspace["models_import"] is True  # From group
    assert effective_permissions.workspace["models_export"] is True  # From group
    assert effective_permissions.features["api_keys"] is True  # From group
    assert (
        effective_permissions.features["web_search"] is False
    )  # From group (overrides default True)


def test_multiple_group_permission_merging(sqlite_database, permission_service):
    """Test permission merging from multiple groups."""
    # Create test data
    user_id = uuid4()
    group1_id = uuid4()
    group2_id = uuid4()

    # Create a user
    user = UserEntity(
        id=user_id,
        username="multigroupuser",
        name="Multi Group User",
        email="multigroup@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    # Create first group
    group1 = GroupEntity(
        id=group1_id,
        user_id=user_id,
        name="group1",
        description="First Group",
        data=None,
        meta=None,
        permissions={
            "workspace": {"models_import": True},
            "features": {"api_keys": True},
        },
        created_at=0,
        updated_at=0,
    )

    # Create second group (later groups override earlier ones)
    group2 = GroupEntity(
        id=group2_id,
        user_id=user_id,
        name="group2",
        description="Second Group",
        data=None,
        meta=None,
        permissions={
            "workspace": {"models_export": True},
            "features": {"api_keys": False},  # This should override group1
        },
        created_at=0,
        updated_at=0,
    )

    # Create group memberships
    member1 = GroupMemberEntity(
        id=uuid4(), group_id=group1_id, user_id=user_id, created_at=0, updated_at=0
    )

    member2 = GroupMemberEntity(
        id=uuid4(), group_id=group2_id, user_id=user_id, created_at=0, updated_at=0
    )

    # Save to database
    sqlite_database.upsert_user(user)
    sqlite_database.upsert_group(group1)
    sqlite_database.upsert_group(group2)
    sqlite_database.upsert_group_member(member1)
    sqlite_database.upsert_group_member(member2)

    # Test permission merging
    effective_permissions = permission_service.get_effective_permissions(user)

    # Should have permissions from both groups
    assert effective_permissions.workspace["models_import"] is True  # From group1
    assert effective_permissions.workspace["models_export"] is True  # From group2

    # Later group should override earlier group
    assert (
        effective_permissions.features["api_keys"] is False
    )  # group2 overrides group1


def test_permission_service_database_operations(sqlite_database, permission_service):
    """Test permission service database operations."""
    # Create test user
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        username="dbtestuser",
        name="DB Test User",
        email="dbtest@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    # Save user to database
    sqlite_database.upsert_user(user)

    # Test setting user permissions
    test_permissions = {
        "workspace": {"knowledge": False},
        "features": {"web_search": False},
    }

    result = permission_service.set_user_permissions(user_id, test_permissions)
    assert result is True

    # Retrieve user and check permissions
    retrieved_user = sqlite_database.get_user_by_email("dbtest@example.com")
    assert retrieved_user is not None
    assert retrieved_user.permissions == test_permissions

    # Test setting group permissions
    group_id = uuid4()
    group = GroupEntity(
        id=group_id,
        user_id=user_id,
        name="permission_test_group",
        description="Permission Test Group",
        data=None,
        meta=None,
        permissions={
            "workspace": {"models_export": True},
            "chat": {"file_upload": False},
        },
        created_at=0,
        updated_at=0,
    )

    sqlite_database.upsert_group(group)

    result = permission_service.set_group_permissions(
        group_id, {"features": {"api_keys": True}}
    )
    assert result is True

    # Check group permissions were updated
    updated_group = sqlite_database.get_group_by_id(group_id)
    assert updated_group is not None
    assert updated_group.permissions["features"]["api_keys"] is True


def test_permission_service_error_handling(permission_service):
    """Test permission service error handling."""
    # Test with non-existent user
    result = permission_service.set_user_permissions(uuid4(), {"test": "permission"})
    assert result is False

    # Test with non-existent group
    result = permission_service.set_group_permissions(uuid4(), {"test": "permission"})
    assert result is False


def test_admin_role_permissions(permission_service):
    """Test that admin role has all permissions by default."""
    admin_user = UserEntity(
        id=uuid4(),
        username="admin",
        name="Admin User",
        email="admin@example.com",
        role="admin",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    effective_permissions = permission_service.get_effective_permissions(admin_user)

    # All workspace permissions should be True
    for perm, value in effective_permissions.workspace.items():
        assert value is True, f"Admin should have {perm} permission"

    # All chat permissions should be True
    for perm, value in effective_permissions.chat.items():
        assert value is True, f"Admin should have {perm} permission"

    # All features should be True
    for perm, value in effective_permissions.features.items():
        assert value is True, f"Admin should have {perm} feature"


def test_permission_path_navigation(permission_service):
    """Test navigation through permission paths."""
    # Create a user with specific permissions
    user = UserEntity(
        id=uuid4(),
        username="pathuser",
        name="Path Test User",
        email="pathuser@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions={
            "workspace": {"models": False, "knowledge": True, "prompts": False},
            "features": {"api_keys": True, "web_search": False},
        },
    )

    # Test various permission paths
    assert permission_service.has_permission(user, "workspace.models") is False
    assert permission_service.has_permission(user, "workspace.knowledge") is True
    assert permission_service.has_permission(user, "workspace.prompts") is False
    assert permission_service.has_permission(user, "features.api_keys") is True
    assert permission_service.has_permission(user, "features.web_search") is False

    # Test that user permissions override role permissions
    assert (
        permission_service.has_permission(user, "workspace.models") is False
    )  # User override
    assert (
        permission_service.has_permission(user, "workspace.tools") is True
    )  # Role default


def test_empty_permission_structures(permission_service):
    """Test handling of empty or None permission structures."""
    # User with no permissions
    user = UserEntity(
        id=uuid4(),
        username="emptyuser",
        name="Empty Permissions User",
        email="empty@example.com",
        role="user",
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
        updated_at=0,
        created_at=0,
        api_key=None,
        settings=None,
        info=None,
        oauth=None,
        oauth_sub=None,
        permissions=None,
    )

    # Should get role-based permissions
    effective_permissions = permission_service.get_effective_permissions(user)
    assert effective_permissions.workspace["models"] is True  # Default for user role

    # Test with empty permission override
    user.permissions = {}
    effective_permissions = permission_service.get_effective_permissions(user)
    assert effective_permissions.workspace["models"] is True  # Still role default

    # Test permission checking with empty structures
    assert permission_service.has_permission(user, "workspace.models") is True
    assert permission_service.has_permission(user, "nonexistent.path") is False
