"""
Memory graph operations API endpoints.

Endpoints:
- POST /v1/associations - Create association (source_id and target_id in body)
- POST /v1/memories/{memory_id}/associate - Link memories (source_id in URL)
- GET /v1/memories/{memory_id}/associations - Get associations
- POST /v1/memories/{memory_id}/traverse - Simple graph traversal from memory
- POST /v1/associations/traverse - Advanced graph traversal
"""
import logging

from fastapi import APIRouter, HTTPException, Depends, status

from memorylayer_server.models.association import AssociateInput, GraphQueryInput
from memorylayer_server.services.association import AssociationService
from .schemas import (
    AssociationCreateRequest,
    AssociationCreateFullRequest,
    AssociationListRequest,
    MemoryTraverseRequest,
    GraphTraverseRequest,
    AssociationResponse,
    AssociationListResponse,
    GraphQueryResult,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["associations"])


# Dependency to get workspace_id from auth context
async def get_workspace_id() -> str:
    """
    Get workspace ID from authentication context.

    In production, this would extract from JWT token or API key.
    For development, returns a default workspace ID.
    """
    # TODO: Implement actual auth
    return "default_workspace"


# Dependency to get association service
async def get_association_service() -> AssociationService:
    """Get association service instance from dependency injection."""
    from ...services import get_association_service as _get_association_service
    return _get_association_service()


@router.post(
    "/associations",
    response_model=AssociationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Source or target memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_association_full(
        request: AssociationCreateFullRequest,
        workspace_id: str = Depends(get_workspace_id),
        association_service: AssociationService = Depends(get_association_service),
) -> AssociationResponse:
    """
    Create a typed relationship between two memories.

    This endpoint takes both source_id and target_id in the request body.
    Alternative: POST /v1/memories/{memory_id}/associate with target_id in body.

    Args:
        request: Association creation request with source and target IDs
        workspace_id: Workspace ID from auth context
        association_service: Association service instance

    Returns:
        Created association

    Raises:
        HTTPException: If source/target not found or association fails
    """
    try:
        logger.info(
            "Creating association: %s -[%s]-> %s",
            request.source_id,
            request.relationship,
            request.target_id
        )

        # Convert request to domain input
        associate_input = AssociateInput(
            source_id=request.source_id,
            target_id=request.target_id,
            relationship=request.relationship,
            strength=request.strength,
            metadata=request.metadata,
        )

        # Create association
        association = await association_service.associate(
            workspace_id=workspace_id,
            input=associate_input,
        )

        logger.info("Created association: %s", association.id)
        return AssociationResponse(association=association)

    except ValueError as e:
        logger.warning("Invalid association request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error("Failed to create association: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create association"
        )


@router.post(
    "/memories/{memory_id}/associate",
    response_model=AssociationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Source or target memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_association(
        memory_id: str,
        request: AssociationCreateRequest,
        workspace_id: str = Depends(get_workspace_id),
        association_service: AssociationService = Depends(get_association_service),
) -> AssociationResponse:
    """
    Create a typed relationship between two memories.

    Args:
        memory_id: Source memory ID
        request: Association creation request
        workspace_id: Workspace ID from auth context
        association_service: Association service instance

    Returns:
        Created association

    Raises:
        HTTPException: If source/target not found or association fails
    """
    try:
        logger.info(
            "Creating association: %s -[%s]-> %s",
            memory_id,
            request.relationship,
            request.target_id
        )

        # Convert request to domain input
        associate_input = AssociateInput(
            source_id=memory_id,
            target_id=request.target_id,
            relationship=request.relationship,
            strength=request.strength,
            metadata=request.metadata,
        )

        # Create association
        association = await association_service.associate(
            workspace_id=workspace_id,
            input=associate_input,
        )

        logger.info("Created association: %s", association.id)
        return AssociationResponse(association=association)

    except ValueError as e:
        logger.warning("Invalid association request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error("Failed to create association: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create association"
        )


@router.get(
    "/memories/{memory_id}/associations",
    response_model=AssociationListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_associations(
        memory_id: str,
        relationships: str | None = None,
        direction: str = "both",
        workspace_id: str = Depends(get_workspace_id),
        association_service: AssociationService = Depends(get_association_service),
) -> AssociationListResponse:
    """
    Get all associations for a memory.

    Args:
        memory_id: Memory identifier
        relationships: Comma-separated list of relationship types to filter by
        direction: Association direction (outgoing, incoming, both)
        workspace_id: Workspace ID from auth context
        association_service: Association service instance

    Returns:
        List of associations

    Raises:
        HTTPException: If memory not found or query fails
    """
    try:
        logger.debug(
            "Getting associations for memory: %s, direction: %s",
            memory_id,
            direction
        )

        # Parse relationship types if provided
        relationship_types = None
        if relationships:
            from ...models.association import RelationshipType
            try:
                relationship_types = [
                    RelationshipType(rel.strip())
                    for rel in relationships.split(",")
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid relationship type: {e}"
                )

        # Get associations
        associations = await association_service.get_related(
            workspace_id=workspace_id,
            memory_id=memory_id,
            relationships=relationship_types,
            direction=direction,
        )

        logger.debug("Found %d associations for memory: %s", len(associations), memory_id)
        return AssociationListResponse(
            associations=associations,
            total_count=len(associations)
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid association query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to get associations for memory %s: %s",
            memory_id,
            e,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve associations"
        )


@router.post(
    "/memories/{memory_id}/traverse",
    response_model=GraphQueryResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Start memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def traverse_from_memory(
        memory_id: str,
        request: MemoryTraverseRequest,
        workspace_id: str = Depends(get_workspace_id),
        association_service: AssociationService = Depends(get_association_service),
) -> GraphQueryResult:
    """
    Traverse memory graph starting from a specific memory.

    This endpoint provides a simplified interface for graph traversal.
    For more advanced options (relationship categories, custom limits),
    use POST /v1/associations/traverse.

    Example use cases:
    - Find causal chains: What led to this memory?
    - Find solutions: What addresses this problem?
    - Find related concepts: What's connected to this idea?

    Args:
        memory_id: Starting memory for traversal
        request: Traverse request with filters and options
        workspace_id: Workspace ID from auth context
        association_service: Association service instance

    Returns:
        Graph query result with paths and nodes

    Raises:
        HTTPException: If start memory not found or traversal fails
    """
    try:
        logger.info(
            "Traversing graph from memory: %s, max_depth: %d, direction: %s",
            memory_id,
            request.max_depth,
            request.direction
        )

        # Convert relationship types to strings for storage layer
        relationship_strs = None
        if request.relationship_types:
            relationship_strs = [rel.value for rel in request.relationship_types]

        # Perform traversal via storage backend
        result = await association_service.storage.traverse_graph(
            workspace_id=workspace_id,
            start_id=memory_id,
            max_depth=request.max_depth,
            relationships=relationship_strs,
            direction=request.direction,
        )

        logger.info(
            "Graph traversal found %d paths, %d unique nodes",
            result.total_paths,
            len(result.unique_nodes)
        )

        return result

    except ValueError as e:
        logger.warning("Invalid graph traversal request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )
        logger.error("Failed to traverse graph from memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to traverse graph"
        )


@router.post(
    "/associations/traverse",
    response_model=GraphQueryResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Start memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def traverse_graph(
        request: GraphTraverseRequest,
        workspace_id: str = Depends(get_workspace_id),
        association_service: AssociationService = Depends(get_association_service),
) -> GraphQueryResult:
    """
    Perform multi-hop graph traversal from a starting memory with advanced options.

    This endpoint provides full control over graph traversal with request body configuration.
    For simpler queries, use POST /v1/memories/{memory_id}/traverse.

    Example use cases:
    - Find causal chains: What led to this problem?
    - Find solutions: What addresses this issue?
    - Find related concepts: What's connected to this idea?

    Args:
        request: Graph traversal request with full configuration
        workspace_id: Workspace ID from auth context
        association_service: Association service instance

    Returns:
        Graph query result with paths and nodes

    Raises:
        HTTPException: If start memory not found or traversal fails
    """
    try:
        logger.info(
            "Traversing graph from: %s, max_depth: %d, direction: %s",
            request.start_memory_id,
            request.max_depth,
            request.direction
        )

        # Convert request to domain input
        graph_query_input = GraphQueryInput(
            start_memory_id=request.start_memory_id,
            relationship_types=request.relationship_types,
            relationship_categories=request.relationship_categories,
            max_depth=request.max_depth,
            direction=request.direction,
            min_strength=request.min_strength,
            max_paths=request.max_paths,
            max_nodes=request.max_nodes,
        )

        # Perform traversal
        result = await association_service.traverse(
            workspace_id=workspace_id,
            input=graph_query_input,
        )

        logger.info(
            "Graph traversal found %d paths, %d unique nodes",
            result.total_paths,
            len(result.unique_nodes)
        )

        return result

    except ValueError as e:
        logger.warning("Invalid graph traversal request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error("Failed to traverse graph: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to traverse graph"
        )
