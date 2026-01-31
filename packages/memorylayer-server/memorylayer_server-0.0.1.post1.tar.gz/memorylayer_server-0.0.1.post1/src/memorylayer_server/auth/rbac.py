"""
Role-Based Access Control for workspaces.

Roles from spec section 11.2:
- admin: Full access (memories:*, workspaces:*, users:*)
- developer: Read/write memories, read workspaces
- reader: Read-only access

Permissions format: "resource:action" or "resource:action:scope"
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class Role(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    READER = "reader"


class Permission(BaseModel):
    """Permission rule."""

    resource: str  # memories, workspaces, users
    action: str  # read, write, delete, *
    scope: Optional[str] = None  # own, all, None (default)

    def matches(self, resource: str, action: str, scope: Optional[str] = None) -> bool:
        """
        Check if this permission matches the requested operation.

        Args:
            resource: Resource being accessed
            action: Action being performed
            scope: Scope of the action (own, all, None)

        Returns:
            True if permission grants access
        """
        # Check resource
        if self.resource != "*" and self.resource != resource:
            return False

        # Check action
        if self.action != "*" and self.action != action:
            return False

        # Check scope (if specified)
        if self.scope is not None and scope is not None:
            if self.scope != scope:
                return False

        return True


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, List[Permission]] = {
    Role.ADMIN: [
        # Full access to everything
        Permission(resource="*", action="*"),
    ],
    Role.DEVELOPER: [
        # Memories: full access
        Permission(resource="memories", action="read"),
        Permission(resource="memories", action="write"),
        Permission(resource="memories", action="delete", scope="own"),
        # Workspaces: read only
        Permission(resource="workspaces", action="read"),
        # Sessions: full access
        Permission(resource="sessions", action="*"),
    ],
    Role.READER: [
        # Memories: read only
        Permission(resource="memories", action="read"),
        # Workspaces: read only
        Permission(resource="workspaces", action="read"),
        # Sessions: read only
        Permission(resource="sessions", action="read"),
    ],
}


def has_permission(role: Role, resource: str, action: str, scope: Optional[str] = None) -> bool:
    """
    Check if a role has permission for a resource action.

    Args:
        role: User role
        resource: Resource being accessed (memories, workspaces, users, sessions)
        action: Action being performed (read, write, delete)
        scope: Optional scope (own, all)

    Returns:
        True if role has permission

    Example:
        >>> has_permission(Role.DEVELOPER, "memories", "write")
        True
        >>> has_permission(Role.READER, "memories", "write")
        False
        >>> has_permission(Role.DEVELOPER, "memories", "delete", "own")
        True
        >>> has_permission(Role.DEVELOPER, "memories", "delete", "all")
        False
    """
    permissions = ROLE_PERMISSIONS.get(role, [])

    for perm in permissions:
        if perm.matches(resource, action, scope):
            return True

    return False


async def check_workspace_access(
    user_id: str,
    workspace_id: str,
    required_role: Role = Role.READER,
) -> bool:
    """
    Check if user has required role in workspace.

    NOTE: This is a placeholder. In production, this would query the database
    to check workspace_permissions table.

    Args:
        user_id: User identifier
        workspace_id: Workspace identifier
        required_role: Minimum role required (default: READER)

    Returns:
        True if user has required access level

    Example:
        >>> await check_workspace_access("user_123", "ws_abc", Role.DEVELOPER)
        True
    """
    # TODO: Implement database lookup
    # For now, always grant access (will be implemented with database layer)
    #
    # In production:
    # 1. Query workspace_permissions table
    # 2. Get user's role in workspace
    # 3. Check if role >= required_role (ADMIN > DEVELOPER > READER)
    #
    # Example query:
    # SELECT role FROM workspace_permissions
    # WHERE workspace_id = $1 AND user_id = $2

    return True
