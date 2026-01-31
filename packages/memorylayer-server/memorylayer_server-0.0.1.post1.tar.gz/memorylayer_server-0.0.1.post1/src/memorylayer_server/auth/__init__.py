"""
Authentication and API key handling module for MemoryLayer.ai.
"""

from .api_keys import (
    APIKeyInfo,
    generate_api_key,
    parse_api_key,
    validate_api_key,
    compute_checksum,
)
from .rbac import Role, Permission, has_permission, check_workspace_access
from .middleware import AuthContext, get_auth_context, require_auth, optional_auth
from .context import MemoryContext

__all__ = [
    # API Keys
    "APIKeyInfo",
    "generate_api_key",
    "parse_api_key",
    "validate_api_key",
    "compute_checksum",
    # RBAC
    "Role",
    "Permission",
    "has_permission",
    "check_workspace_access",
    # Middleware
    "AuthContext",
    "get_auth_context",
    "require_auth",
    "optional_auth",
    # Context
    "MemoryContext",
]
