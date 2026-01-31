"""
Memory CRUD and recall operations API endpoints.

Endpoints:
- POST /v1/memories - Store a memory
- GET /v1/memories/{memory_id} - Get single memory
- PUT /v1/memories/{memory_id} - Update memory
- DELETE /v1/memories/{memory_id} - Delete memory (soft delete)
- POST /v1/memories/recall - Query memories with mode (rag/llm/hybrid)
- POST /v1/memories/reflect - Synthesize memories
- POST /v1/memories/{memory_id}/decay - Decay importance
- GET /v1/memories/{memory_id}/trace - Trace memory provenance
- POST /v1/memories/batch - Batch operations (create, update, delete)
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status

from memorylayer_server.models.memory import RememberInput, RecallInput, ReflectInput, Memory
from memorylayer_server.services.memory import MemoryService
from memorylayer_server.services.reflect import ReflectService

from .schemas import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryRecallRequest,
    MemoryReflectRequest,
    MemoryDecayRequest,
    MemoryBatchRequest,
    MemoryResponse,
    MemoryListResponse,
    RecallResult,
    ReflectResult,
    ErrorResponse,
    TraceResponse,
    BatchOperationResponse,
    BatchOperationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["memories"])


# Dependency to get workspace_id from auth context
# TODO: Replace with actual auth dependency when auth is implemented
async def get_workspace_id() -> str:
    """
    Get workspace ID from authentication context.

    In production, this would extract from JWT token or API key.
    For development, returns a default workspace ID.
    """
    # TODO: Implement actual auth
    # from ..auth.context import get_current_workspace
    # return await get_current_workspace()
    return "default_workspace"


async def get_memory_service():
    """Get memory service instance for FastAPI dependency injection."""
    from ...services import get_memory_service as _get_memory_service
    return _get_memory_service()


async def get_reflect_service():
    """Get reflect service instance for FastAPI dependency injection."""
    from ...services import get_reflect_service as _get_reflect_service
    return _get_reflect_service()


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_memory(
        request: MemoryCreateRequest,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """
    Store a new memory with automatic embedding and classification.

    Args:
        request: Memory creation request
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Created memory with generated ID and embedding

    Raises:
        HTTPException: If memory creation fails
    """
    try:
        logger.info(
            "Creating memory in workspace: %s, content length: %d",
            workspace_id,
            len(request.content)
        )

        # Convert request to domain input
        remember_input = RememberInput(
            content=request.content,
            type=request.type,
            subtype=request.subtype,
            importance=request.importance,
            tags=request.tags,
            metadata=request.metadata,
            associations=request.associations,
            space_id=request.space_id,
        )

        # Store memory
        memory = await memory_service.remember(
            workspace_id=workspace_id,
            input=remember_input,
        )

        logger.info("Created memory: %s", memory.id)
        return MemoryResponse(memory=memory)

    except ValueError as e:
        logger.warning("Invalid memory creation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create memory: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory"
        )


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_memory(
        memory_id: str,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """
    Retrieve a single memory by ID.

    Args:
        memory_id: Memory identifier
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Memory object

    Raises:
        HTTPException: If memory not found
    """
    try:
        logger.debug("Getting memory: %s", memory_id)

        memory = await memory_service.get(
            workspace_id=workspace_id,
            memory_id=memory_id,
        )

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        return MemoryResponse(memory=memory)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory"
        )


@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_memory(
        memory_id: str,
        request: MemoryUpdateRequest,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """
    Update an existing memory.

    Args:
        memory_id: Memory identifier
        request: Memory update request
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Updated memory object

    Raises:
        HTTPException: If memory not found or update fails
    """
    try:
        logger.info("Updating memory: %s", memory_id)

        # Check if memory exists
        existing_memory = await memory_service.get(workspace_id, memory_id)
        if not existing_memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        # Build update kwargs from non-None fields
        update_kwargs = {}
        if request.content is not None:
            update_kwargs["content"] = request.content
        if request.type is not None:
            update_kwargs["type"] = request.type
        if request.subtype is not None:
            update_kwargs["subtype"] = request.subtype
        if request.importance is not None:
            update_kwargs["importance"] = request.importance
        if request.tags is not None:
            update_kwargs["tags"] = request.tags
        if request.metadata is not None:
            update_kwargs["metadata"] = request.metadata

        # Update memory via storage
        # Note: This assumes memory_service has access to storage.update_memory
        updated_memory = await memory_service.storage.update_memory(
            workspace_id=workspace_id,
            memory_id=memory_id,
            **update_kwargs
        )

        if not updated_memory:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update memory"
            )

        logger.info("Updated memory: %s", memory_id)
        return MemoryResponse(memory=updated_memory)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid memory update request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_memory(
        memory_id: str,
        hard: bool = False,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> None:
    """
    Delete a memory (soft delete by default).

    Args:
        memory_id: Memory identifier
        hard: If True, permanently delete; if False, soft delete
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Raises:
        HTTPException: If memory not found or deletion fails
    """
    try:
        logger.info("Deleting memory: %s (hard=%s)", memory_id, hard)

        success = await memory_service.forget(
            workspace_id=workspace_id,
            memory_id=memory_id,
            hard=hard,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        logger.info("Deleted memory: %s", memory_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )


@router.post(
    "/recall",
    response_model=RecallResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def recall_memories(
        request: MemoryRecallRequest,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> RecallResult:
    """
    Query memories using vector similarity and optional filters.

    Supports three retrieval modes:
    - RAG: Fast vector similarity search (~30ms)
    - LLM: Query rewriting + enhanced search (~500ms)
    - HYBRID: RAG first, LLM if insufficient (balanced)

    Args:
        request: Memory recall request with query and filters
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Recall result with matched memories and metadata

    Raises:
        HTTPException: If recall fails
    """
    try:
        logger.info(
            "Recalling memories in workspace: %s, mode: %s, query: %s",
            workspace_id,
            request.mode,
            request.query[:50]
        )

        # Convert request to domain input
        recall_input = RecallInput(
            query=request.query,
            types=request.types,
            subtypes=request.subtypes,
            tags=request.tags,
            space_id=request.space_id,
            mode=request.mode,
            tolerance=request.tolerance,
            limit=request.limit,
            min_relevance=request.min_relevance,
            include_associations=request.include_associations,
            traverse_depth=request.traverse_depth,
            created_after=request.created_after,
            created_before=request.created_before,
            context=request.context,
            max_tokens=request.max_tokens,
            rag_threshold=request.rag_threshold,
        )

        # Perform recall
        result = await memory_service.recall(
            workspace_id=workspace_id,
            input=recall_input,
        )

        logger.info(
            "Recalled %d memories in %d ms using %s mode",
            len(result.memories),
            result.search_latency_ms,
            result.mode_used
        )

        return result

    except ValueError as e:
        logger.warning("Invalid recall request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to recall memories: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recall memories"
        )


@router.post(
    "/reflect",
    response_model=ReflectResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def reflect_memories(
        request: MemoryReflectRequest,
        workspace_id: str = Depends(get_workspace_id),
        reflection_service: ReflectService = Depends(get_reflect_service),
) -> ReflectResult:
    """
    Synthesize memories into a coherent reflection.

    Args:
        request: Memory reflection request
        workspace_id: Workspace ID from auth context
        reflection_service: Reflection service instance

    Returns:
        Reflection result with synthesized content

    Raises:
        HTTPException: If reflection fails
    """
    try:
        logger.info(
            "Reflecting on memories in workspace: %s, query: %s",
            workspace_id,
            request.query[:50]
        )

        # Convert request to domain input
        reflect_input = ReflectInput(
            query=request.query,
            max_tokens=request.max_tokens,
            include_sources=request.include_sources,
            depth=request.depth,
            types=request.types,
            subtypes=request.subtypes,
            tags=request.tags,
            space_id=request.space_id,
        )

        # Perform reflection
        result = await reflection_service.reflect(
            workspace_id=workspace_id,
            input=reflect_input,
        )

        logger.info(
            "Reflected on %d source memories, generated %d tokens",
            len(result.source_memories),
            result.tokens_processed
        )

        return result

    except ValueError as e:
        logger.warning("Invalid reflect request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to reflect memories: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reflect memories"
        )


@router.post(
    "/{memory_id}/decay",
    response_model=MemoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def decay_memory(
        memory_id: str,
        request: MemoryDecayRequest,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """
    Reduce memory importance by decay rate.

    Args:
        memory_id: Memory identifier
        request: Decay request with rate
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Updated memory with decayed importance

    Raises:
        HTTPException: If memory not found or decay fails
    """
    try:
        logger.info("Decaying memory: %s by rate: %f", memory_id, request.decay_rate)

        updated_memory = await memory_service.decay(
            workspace_id=workspace_id,
            memory_id=memory_id,
            decay_rate=request.decay_rate,
        )

        if not updated_memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        logger.info("Decayed memory: %s", memory_id)
        return MemoryResponse(memory=updated_memory)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid decay request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to decay memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decay memory"
        )


@router.get(
    "/{memory_id}/trace",
    response_model=TraceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Memory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def trace_memory(
        memory_id: str,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> TraceResponse:
    """
    Trace memory provenance back to source.

    Returns information about the memory's origin:
    - Source resource (if any)
    - Category membership (if any)
    - Association chain

    Args:
        memory_id: Memory identifier
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Trace result with provenance information

    Raises:
        HTTPException: If memory not found or trace fails
    """
    try:
        logger.info("Tracing memory: %s", memory_id)

        # Get the memory
        memory = await memory_service.get(workspace_id, memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        # Get associations to understand the connection chain
        associations = await memory_service.storage.get_associations(
            workspace_id=workspace_id,
            memory_id=memory_id,
            direction="both"
        )

        # Build memory dict
        memory_dict = memory.model_dump()

        # Try to get source resource if it exists
        source_resource = None
        source_resource_id = memory.metadata.get("source_resource_id")
        if source_resource_id:
            resource = await memory_service.storage.get_resource(workspace_id, source_resource_id)
            if resource:
                source_resource = {
                    "id": resource.id,
                    "type": resource.type,
                    "created_at": resource.created_at.isoformat(),
                    "metadata": resource.metadata,
                }

        # Try to get category if it exists
        category = None
        category_name = memory.metadata.get("category")
        if category_name:
            # Category lookup would be done here
            # For now, just include the name
            category = {
                "name": category_name,
            }

        # Build association chain (list of association IDs)
        association_chain = [assoc.id for assoc in associations]

        # Determine layer
        layer = "category" if category else "item"

        # Build chain: category -> item -> resource
        chain = []
        if category:
            chain.append(f"category:{category['name']}")
        chain.append(f"memory:{memory.id}")
        if source_resource:
            chain.append(f"resource:{source_resource['id']}")

        # Build TraceResult
        from ...models.resource import TraceResult
        trace_result = TraceResult(
            memory=memory_dict,
            source_resource=source_resource,
            category=category,
            layer=layer,
            chain=chain,
        )

        logger.info("Traced memory: %s, chain length: %d", memory_id, len(chain))
        return TraceResponse(trace=trace_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trace memory %s: %s", memory_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trace memory"
        )


@router.post(
    "/batch",
    response_model=BatchOperationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def batch_operations(
        request: MemoryBatchRequest,
        workspace_id: str = Depends(get_workspace_id),
        memory_service: MemoryService = Depends(get_memory_service),
) -> BatchOperationResponse:
    """
    Perform multiple memory operations in a single request.

    Supported operation types:
    - create: Create a new memory
    - update: Update an existing memory
    - delete: Delete a memory

    Args:
        request: Batch request with list of operations
        workspace_id: Workspace ID from auth context
        memory_service: Memory service instance

    Returns:
        Results for each operation with success/error status

    Raises:
        HTTPException: If batch request is invalid
    """
    try:
        logger.info(
            "Processing batch operations in workspace: %s, count: %d",
            workspace_id,
            len(request.operations)
        )

        results = []
        successful = 0
        failed = 0

        for i, operation in enumerate(request.operations):
            op_type = operation.get("type")
            op_data = operation.get("data", {})

            logger.debug("Processing batch operation %d: %s", i, op_type)

            try:
                # CREATE operation
                if op_type == "create":
                    # Convert data to RememberInput
                    remember_input = RememberInput(
                        content=op_data.get("content"),
                        type=op_data.get("type"),
                        subtype=op_data.get("subtype"),
                        importance=op_data.get("importance", 0.5),
                        tags=op_data.get("tags", []),
                        metadata=op_data.get("metadata", {}),
                        associations=op_data.get("associations", []),
                        space_id=op_data.get("space_id"),
                    )

                    # Create memory
                    memory = await memory_service.remember(
                        workspace_id=workspace_id,
                        input=remember_input,
                    )

                    results.append(BatchOperationResult(
                        index=i,
                        type=op_type,
                        status="success",
                        memory_id=memory.id,
                    ))
                    successful += 1

                # UPDATE operation
                elif op_type == "update":
                    memory_id = op_data.get("memory_id")
                    if not memory_id:
                        raise ValueError("memory_id is required for update operation")

                    # Check if memory exists
                    existing = await memory_service.get(workspace_id, memory_id)
                    if not existing:
                        raise ValueError(f"Memory not found: {memory_id}")

                    # Build update kwargs
                    update_kwargs = {}
                    if "content" in op_data:
                        update_kwargs["content"] = op_data["content"]
                    if "type" in op_data:
                        update_kwargs["type"] = op_data["type"]
                    if "subtype" in op_data:
                        update_kwargs["subtype"] = op_data["subtype"]
                    if "importance" in op_data:
                        update_kwargs["importance"] = op_data["importance"]
                    if "tags" in op_data:
                        update_kwargs["tags"] = op_data["tags"]
                    if "metadata" in op_data:
                        update_kwargs["metadata"] = op_data["metadata"]

                    # Update memory
                    updated = await memory_service.storage.update_memory(
                        workspace_id=workspace_id,
                        memory_id=memory_id,
                        **update_kwargs
                    )

                    results.append(BatchOperationResult(
                        index=i,
                        type=op_type,
                        status="success",
                        memory_id=memory_id,
                    ))
                    successful += 1

                # DELETE operation
                elif op_type == "delete":
                    memory_id = op_data.get("memory_id")
                    if not memory_id:
                        raise ValueError("memory_id is required for delete operation")

                    hard = op_data.get("hard", False)

                    # Delete memory
                    success = await memory_service.forget(
                        workspace_id=workspace_id,
                        memory_id=memory_id,
                        hard=hard,
                    )

                    if not success:
                        raise ValueError(f"Memory not found: {memory_id}")

                    results.append(BatchOperationResult(
                        index=i,
                        type=op_type,
                        status="success",
                        memory_id=memory_id,
                    ))
                    successful += 1

                # Unknown operation type
                else:
                    raise ValueError(f"Unknown operation type: {op_type}")

            except Exception as e:
                logger.warning(
                    "Batch operation %d failed: %s - %s",
                    i,
                    op_type,
                    str(e)
                )
                results.append(BatchOperationResult(
                    index=i,
                    type=op_type or "unknown",
                    status="error",
                    error=str(e),
                ))
                failed += 1

        logger.info(
            "Completed batch operations: %d successful, %d failed",
            successful,
            failed
        )

        return BatchOperationResponse(
            total_operations=len(request.operations),
            successful=successful,
            failed=failed,
            results=results,
        )

    except ValueError as e:
        logger.warning("Invalid batch request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to process batch operations: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch operations"
        )
