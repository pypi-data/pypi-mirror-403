# RBAC Documentation

## Overview

This documentation provides an in-depth explanation of the Role-Based Access Control (RBAC) implementation in the open-webui project. RBAC is a method for regulating access to computer or network resources based on the roles of individual users within an organization.

## Key Concepts

### Roles

Roles are predefined sets of permissions that can be assigned to users. Each role has a specific set of permissions that determine what actions a user can perform. The roles defined in the system are:

- **Admin**: Users with this role have full access to all features and permissions.
- **User**: Regular users with default permissions.
- **Pending**: Users with restricted permissions, typically used for new or unverified users.

### Permissions

Permissions are specific actions or access rights that can be granted or denied to users. Permissions are organized into categories such as `workspace`, `chat`, `features`, `sharing`, and `settings`. Each category contains a set of permissions that can be enabled or disabled.

### Groups

Groups are collections of users that share the same set of permissions. Groups can be used to manage permissions for multiple users simultaneously. Users can belong to multiple groups, and their effective permissions are a combination of their individual permissions and the permissions of all the groups they belong to.

## Permission Service

The `PermissionService` class is responsible for managing and resolving user permissions based on RBAC. It provides methods to get effective permissions for a user, check if a user has a specific permission, and merge permissions from different sources.

### Methods

- **`get_effective_permissions(user: UserEntity) -> PermissionSystemConfig`**: Gets the effective permissions for a user by combining user-specific permissions with permissions from all groups the user belongs to.
- **`has_permission(user: UserEntity, permission_path: str, default: bool = False) -> bool`**: Checks if a user has a specific permission.
- **`_get_base_permissions_for_role(role: str) -> PermissionSystemConfig`**: Gets the base permissions for a user role.
- **`_get_user_groups(user_id: UUID) -> list[GroupEntity]`**: Gets all groups that a user belongs to.
- **`_merge_permissions(base_permissions: PermissionSystemConfig, override_permissions: dict) -> PermissionSystemConfig`**: Merges two permission sets, with `override_permissions` taking precedence.
- **`_deep_merge_dicts(base: dict, override: dict) -> dict`**: Deep merges two dictionaries, with `override` taking precedence.
- **`get_groups_for_user(user_id: UUID) -> list[GroupEntity]`**: Gets all groups that a user belongs to (database implementation).
- **`get_group_members_for_user(user_id: UUID) -> list[GroupMemberEntity]`**: Gets all group memberships for a user.
- **`set_user_permissions(user_id: UUID, permissions: dict) -> bool`**: Sets user-specific permission overrides.
- **`set_group_permissions(group_id: UUID, permissions: dict) -> bool`**: Sets permissions for a group.

## Example Usage

### Getting Effective Permissions

```python
user = UserEntity(id=UUID('123e4567-e89b-12d3-a456-426614174000'), role='user')
permission_service = PermissionService(database)
effective_permissions = permission_service.get_effective_permissions(user)
```

### Checking a Specific Permission

```python
has_access = permission_service.has_permission(user, 'workspace.models')
```

### Setting User Permissions

```python
permission_service.set_user_permissions(user.id, {'workspace.models': True})
```

### Setting Group Permissions

```python
group_id = UUID('123e4567-e89b-12d3-a456-426614174001')
permission_service.set_group_permissions(group_id, {'workspace.models': True})
```

## Conclusion

The RBAC implementation in open-webui provides a flexible and powerful way to manage user permissions. By defining roles, permissions, and groups, you can easily control access to various features and resources within the application. The `PermissionService` class simplifies the process of managing and resolving permissions, making it easier to enforce security policies and ensure that users have the appropriate access rights.