"""
FastAPI authentication middleware.

Implements the Context Proxy pattern from Falcon3:
- Extracts API key from Authorization header
- Validates and parses tenant/workspace context
- Injects context into request state for downstream use
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel

from .api_keys import parse_api_key
from .rbac import Role


# Security scheme for Bearer token authentication
bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext(BaseModel):
    """
    Authentication context injected into requests.

    This implements the Context Proxy pattern - all downstream operations
    automatically have tenant/workspace/user context available.
    """

    tenant_id: str
    workspace_id: Optional[str] = None  # From X-Workspace-ID header
    user_id: Optional[str] = None  # From X-User-ID header
    api_key_id: str
    role: str = "developer"  # Default role

    class Config:
        """Pydantic configuration."""
        frozen = True  # Make immutable


async def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthContext:
    """
    Extract and validate authentication from request.

    Headers:
    - Authorization: Bearer ml_sk_...
    - X-Workspace-ID: ws_abc123 (optional)
    - X-User-ID: user_xyz (optional)

    Args:
        request: FastAPI request object
        credentials: Bearer token credentials

    Returns:
        AuthContext with tenant/workspace/user information

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        @app.get("/memories")
        async def get_memories(auth: AuthContext = Depends(get_auth_context)):
            # auth.tenant_id, auth.workspace_id available
            pass
    """
    # Check for credentials
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse API key
    api_key = credentials.credentials
    key_info = parse_api_key(api_key)

    if not key_info or not key_info.is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract optional headers
    workspace_id = request.headers.get("X-Workspace-ID")
    user_id = request.headers.get("X-User-ID")

    # TODO: In production, lookup user's role from database based on tenant_id
    # For now, default to developer role
    role = "developer"

    # TODO: In production, validate that API key has access to workspace
    # and that workspace exists

    return AuthContext(
        tenant_id=key_info.tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        api_key_id=key_info.key_id,
        role=role,
    )


async def require_auth(
    context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """
    Require valid authentication (raises 401 if missing).

    This is an alias for get_auth_context with clearer naming.

    Args:
        context: Authentication context from get_auth_context

    Returns:
        AuthContext if valid

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        @app.post("/memories")
        async def create_memory(
            auth: AuthContext = Depends(require_auth),
            memory: MemoryInput,
        ):
            # Guaranteed to have valid auth here
            pass
    """
    return context


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AuthContext]:
    """
    Optional authentication (returns None if not provided).

    Args:
        credentials: Optional bearer token credentials

    Returns:
        AuthContext if credentials provided and valid, None otherwise

    Example:
        @app.get("/public/memories")
        async def get_public_memories(
            auth: Optional[AuthContext] = Depends(optional_auth),
        ):
            if auth:
                # Filter by workspace
                workspace_id = auth.workspace_id
            else:
                # Public access
                workspace_id = None
    """
    if not credentials:
        return None

    try:
        # Parse API key
        api_key = credentials.credentials
        key_info = parse_api_key(api_key)

        if not key_info or not key_info.is_valid:
            return None

        # TODO: Lookup role from database in production
        role = "developer"

        return AuthContext(
            tenant_id=key_info.tenant_id,
            workspace_id=None,  # No default workspace for optional auth
            user_id=None,
            api_key_id=key_info.key_id,
            role=role,
        )
    except Exception:
        # If any error occurs, just return None for optional auth
        return None
