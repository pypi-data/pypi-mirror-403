"""
Workspace management API endpoints.

Endpoints:
- POST /v1/workspaces - Create workspace
- GET /v1/workspaces/{workspace_id} - Get workspace
- PUT /v1/workspaces/{workspace_id} - Update workspace
- POST /v1/workspaces/{workspace_id}/spaces - Create memory space
- GET /v1/workspaces/{workspace_id}/spaces - List memory spaces
"""
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status

from .schemas import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
    MemorySpaceCreateRequest,
    WorkspaceResponse,
    MemorySpaceResponse,
    MemorySpaceListResponse,
    ErrorResponse,
)
from memorylayer_server.services.workspace import get_workspace_service as _get_workspace_service, WorkspaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_workspace_service() -> WorkspaceService:
    """FastAPI dependency wrapper for workspace service."""
    return _get_workspace_service()


# Dependency to get tenant_id from auth context
async def get_tenant_id() -> str:
    """
    Get tenant ID from authentication context.

    In production, this would extract from JWT token or API key.
    For development, returns a default tenant ID.
    """
    # TODO: Implement actual auth
    return "default_tenant"


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_workspace(
        request: WorkspaceCreateRequest,
        tenant_id: str = Depends(get_tenant_id),
        workspace_service=Depends(get_workspace_service),
) -> WorkspaceResponse:
    """
    Create a new workspace.

    Workspaces provide tenant-level memory isolation.

    Args:
        request: Workspace creation request
        tenant_id: Tenant ID from auth context
        workspace_service: Workspace service instance

    Returns:
        Created workspace

    Raises:
        HTTPException: If workspace creation fails
    """
    try:
        # Generate workspace ID
        workspace_id = f"ws_{uuid4().hex[:16]}"

        logger.info(
            "Creating workspace: %s for tenant: %s, name: %s",
            workspace_id,
            tenant_id,
            request.name
        )

        # Create workspace
        from ...models.workspace import Workspace
        workspace = Workspace(
            id=workspace_id,
            tenant_id=tenant_id,
            name=request.name,
            settings=request.settings,
        )

        # Store workspace via workspace service
        workspace = await workspace_service.create_workspace(workspace)

        logger.info("Created workspace: %s", workspace_id)
        return WorkspaceResponse(workspace=workspace)

    except ValueError as e:
        logger.warning("Invalid workspace creation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create workspace: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workspace"
        )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Workspace not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_workspace(
        workspace_id: str,
        tenant_id: str = Depends(get_tenant_id),
        workspace_service=Depends(get_workspace_service),
) -> WorkspaceResponse:
    """
    Retrieve a workspace by ID.

    Args:
        workspace_id: Workspace identifier
        tenant_id: Tenant ID from auth context (for authorization)
        workspace_service: Workspace service instance

    Returns:
        Workspace object

    Raises:
        HTTPException: If workspace not found
    """
    try:
        logger.debug("Getting workspace: %s", workspace_id)

        # Get workspace via workspace service
        workspace = await workspace_service.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {workspace_id}"
            )
        # Verify tenant access
        if workspace.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        return WorkspaceResponse(workspace=workspace)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workspace %s: %s", workspace_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workspace"
        )


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Workspace not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_workspace(
        workspace_id: str,
        request: WorkspaceUpdateRequest,
        tenant_id: str = Depends(get_tenant_id),
        workspace_service=Depends(get_workspace_service),
) -> WorkspaceResponse:
    """
    Update an existing workspace.

    Args:
        workspace_id: Workspace identifier
        request: Workspace update request
        tenant_id: Tenant ID from auth context (for authorization)
        workspace_service: Workspace service instance

    Returns:
        Updated workspace

    Raises:
        HTTPException: If workspace not found or update fails
    """
    try:
        logger.info("Updating workspace: %s", workspace_id)

        # Get existing workspace
        workspace = await workspace_service.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {workspace_id}"
            )
        # Verify tenant access
        if workspace.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        # Update fields
        if request.name is not None:
            workspace = workspace.model_copy(update={"name": request.name})
        if request.settings is not None:
            workspace = workspace.model_copy(update={"settings": request.settings})
        workspace = await workspace_service.update_workspace(workspace)
        return WorkspaceResponse(workspace=workspace)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid workspace update request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update workspace %s: %s", workspace_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workspace"
        )


@router.post(
    "/{workspace_id}/spaces",
    response_model=MemorySpaceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Workspace not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_memory_space(
        workspace_id: str,
        request: MemorySpaceCreateRequest,
        tenant_id: str = Depends(get_tenant_id),
        workspace_service=Depends(get_workspace_service),
) -> MemorySpaceResponse:
    """
    Create a memory space within a workspace.

    Memory spaces provide logical grouping of memories (e.g., by project, topic).

    Args:
        workspace_id: Parent workspace identifier
        request: Memory space creation request
        tenant_id: Tenant ID from auth context (for authorization)
        workspace_service: Workspace service instance

    Returns:
        Created memory space

    Raises:
        HTTPException: If workspace not found or space creation fails
    """
    try:
        # Generate space ID
        space_id = f"space_{uuid4().hex[:16]}"

        logger.info(
            "Creating memory space: %s in workspace: %s, name: %s",
            space_id,
            workspace_id,
            request.name
        )

        # Verify workspace exists and tenant has access
        workspace = await workspace_service.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {workspace_id}"
            )
        if workspace.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )

        # Create memory space
        from ...models.workspace import MemorySpace
        space = MemorySpace(
            id=space_id,
            workspace_id=workspace_id,
            name=request.name,
            description=request.description,
            settings=request.settings,
        )

        # Store space via workspace service
        space = await workspace_service.create_memory_space(workspace_id, space)

        logger.info("Created memory space: %s", space_id)
        return MemorySpaceResponse(space=space)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid memory space creation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to create memory space in workspace %s: %s",
            workspace_id,
            e,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory space"
        )


@router.get(
    "/{workspace_id}/spaces",
    response_model=MemorySpaceListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Workspace not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_memory_spaces(
        workspace_id: str,
        tenant_id: str = Depends(get_tenant_id),
        workspace_service=Depends(get_workspace_service),
) -> MemorySpaceListResponse:
    """
    List all memory spaces in a workspace.

    Args:
        workspace_id: Workspace identifier
        tenant_id: Tenant ID from auth context (for authorization)
        workspace_service: Workspace service instance

    Returns:
        List of memory spaces

    Raises:
        HTTPException: If workspace not found or listing fails
    """
    try:
        logger.debug("Listing memory spaces for workspace: %s", workspace_id)

        # Verify workspace exists and tenant has access
        workspace = await workspace_service.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {workspace_id}"
            )
        if workspace.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )

        # List spaces via workspace service
        spaces = await workspace_service.list_memory_spaces(workspace_id)
        return MemorySpaceListResponse(
            spaces=spaces,
            total_count=len(spaces)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list memory spaces for workspace %s: %s",
            workspace_id,
            e,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list memory spaces"
        )
