"""
API request/response schemas for MemoryLayer.ai endpoints.

These schemas define the HTTP API interface separate from core domain models.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from memorylayer_server.models.memory import (
    MemoryType, MemorySubtype, RecallMode, SearchTolerance,
    Memory, RecallResult, ReflectResult
)
from memorylayer_server.models.association import (
    RelationshipType, RelationshipCategory,
    Association, GraphQueryResult, GraphPath
)
from memorylayer_server.models.session import Session, SessionBriefing
from memorylayer_server.models.workspace import Workspace, MemorySpace
from memorylayer_server.models.resource import TraceResult


# Memory API Schemas
class MemoryCreateRequest(BaseModel):
    """Request schema for creating a memory."""

    content: str = Field(..., description="Memory content to store", min_length=1)
    type: Optional[MemoryType] = Field(None, description="Cognitive type (auto-classified if omitted)")
    subtype: Optional[MemorySubtype] = Field(None, description="Domain-specific classification")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Memory importance (0.0-1.0)")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
    associations: list[str] = Field(default_factory=list, description="Memory IDs to associate with")
    space_id: Optional[str] = Field(None, description="Target memory space")


class MemoryUpdateRequest(BaseModel):
    """Request schema for updating a memory."""

    content: Optional[str] = Field(None, description="Updated content", min_length=1)
    type: Optional[MemoryType] = Field(None, description="Updated cognitive type")
    subtype: Optional[MemorySubtype] = Field(None, description="Updated domain classification")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated importance")
    tags: Optional[list[str]] = Field(None, description="Updated tags")
    metadata: Optional[dict[str, Any]] = Field(None, description="Updated metadata")


class MemoryRecallRequest(BaseModel):
    """Request schema for querying memories."""

    query: str = Field(..., description="Natural language query", min_length=1)
    types: list[MemoryType] = Field(default_factory=list, description="Filter by cognitive types")
    subtypes: list[MemorySubtype] = Field(default_factory=list, description="Filter by domain subtypes")
    tags: list[str] = Field(default_factory=list, description="Filter by tags (AND logic)")
    space_id: Optional[str] = Field(None, description="Filter by memory space")
    mode: RecallMode = Field(RecallMode.RAG, description="Retrieval strategy")
    tolerance: SearchTolerance = Field(SearchTolerance.MODERATE, description="Search precision")
    limit: int = Field(10, ge=1, le=100, description="Maximum memories to return")
    min_relevance: float = Field(0.5, ge=0.0, le=1.0, description="Minimum relevance score")
    include_associations: bool = Field(False, description="Include linked memories")
    traverse_depth: int = Field(0, ge=0, le=5, description="Multi-hop graph traversal depth")
    created_after: Optional[datetime] = Field(None, description="Filter memories created after this time")
    created_before: Optional[datetime] = Field(None, description="Filter memories created before this time")
    context: list[dict[str, str]] = Field(default_factory=list, description="Recent conversation context")
    max_tokens: Optional[int] = Field(None, description="Token budget for LLM reasoning")
    rag_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Use LLM if RAG confidence < threshold")


class MemoryReflectRequest(BaseModel):
    """Request schema for synthesizing memories."""

    query: str = Field(..., description="What to reflect on", min_length=1)
    max_tokens: int = Field(500, ge=50, le=4000, description="Maximum tokens in reflection")
    include_sources: bool = Field(True, description="Include source memory references")
    depth: int = Field(2, ge=1, le=5, description="Association traversal depth")
    types: list[MemoryType] = Field(default_factory=list, description="Filter by types")
    subtypes: list[MemorySubtype] = Field(default_factory=list, description="Filter by subtypes")
    tags: list[str] = Field(default_factory=list, description="Filter by tags")
    space_id: Optional[str] = Field(None, description="Filter by memory space")


class MemoryDecayRequest(BaseModel):
    """Request schema for decaying a memory."""

    decay_rate: float = Field(0.1, ge=0.0, le=1.0, description="Decay rate to apply")


class MemoryBatchRequest(BaseModel):
    """Request schema for batch memory operations."""

    operations: list[dict[str, Any]] = Field(
        ...,
        description="List of operations with 'type' and 'data' fields"
    )


class MemoryResponse(BaseModel):
    """Response schema for single memory."""

    memory: Memory


class MemoryListResponse(BaseModel):
    """Response schema for memory list."""

    memories: list[Memory]
    total_count: int


class TraceResponse(BaseModel):
    """Response schema for memory trace."""

    trace: TraceResult


class BatchOperationResult(BaseModel):
    """Result of a single batch operation."""

    index: int = Field(..., description="Operation index in batch")
    type: str = Field(..., description="Operation type")
    status: str = Field(..., description="success or error")
    memory_id: Optional[str] = Field(None, description="Memory ID for create/update operations")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchOperationResponse(BaseModel):
    """Response schema for batch operations."""

    total_operations: int = Field(..., description="Total operations in batch")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: list[BatchOperationResult] = Field(..., description="Results for each operation")


# Association API Schemas
class AssociationCreateRequest(BaseModel):
    """Request schema for creating an association (source from URL path)."""

    target_id: str = Field(..., description="Target memory ID")
    relationship: RelationshipType = Field(..., description="Relationship type")
    strength: float = Field(0.5, ge=0.0, le=1.0, description="Relationship strength")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class AssociationCreateFullRequest(BaseModel):
    """Request schema for creating an association with both source and target in body."""

    source_id: str = Field(..., description="Source memory ID")
    target_id: str = Field(..., description="Target memory ID")
    relationship: RelationshipType = Field(..., description="Relationship type")
    strength: float = Field(0.5, ge=0.0, le=1.0, description="Relationship strength")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class AssociationListRequest(BaseModel):
    """Request schema for listing associations."""

    relationships: Optional[list[RelationshipType]] = Field(
        None,
        description="Filter by relationship types"
    )
    direction: str = Field(
        "both",
        pattern="^(outgoing|incoming|both)$",
        description="Association direction"
    )


class MemoryTraverseRequest(BaseModel):
    """Request schema for traversing from a specific memory."""

    max_depth: int = Field(2, ge=1, le=5, description="Maximum traversal depth")
    relationship_types: list[RelationshipType] = Field(
        default_factory=list,
        description="Filter by specific relationship types (empty = all)"
    )
    direction: str = Field(
        "both",
        pattern="^(outgoing|incoming|both)$",
        description="Traversal direction: outgoing, incoming, both"
    )
    min_strength: float = Field(0.0, ge=0.0, le=1.0, description="Minimum edge strength")


class GraphTraverseRequest(BaseModel):
    """Request schema for graph traversal."""

    start_memory_id: str = Field(..., description="Starting memory for traversal")
    relationship_types: list[RelationshipType] = Field(
        default_factory=list,
        description="Filter by specific relationship types"
    )
    relationship_categories: list[RelationshipCategory] = Field(
        default_factory=list,
        description="Filter by relationship categories"
    )
    max_depth: int = Field(3, ge=1, le=5, description="Maximum traversal depth")
    direction: str = Field(
        "both",
        pattern="^(outgoing|incoming|both)$",
        description="Traversal direction"
    )
    min_strength: float = Field(0.0, ge=0.0, le=1.0, description="Minimum edge strength")
    max_paths: int = Field(100, ge=1, le=1000, description="Maximum paths to return")
    max_nodes: int = Field(50, ge=1, le=500, description="Maximum nodes in result")


class AssociationResponse(BaseModel):
    """Response schema for single association."""

    association: Association


class AssociationListResponse(BaseModel):
    """Response schema for association list."""

    associations: list[Association]
    total_count: int


# Session API Schemas
class SessionCreateRequest(BaseModel):
    """Request schema for creating a session."""

    session_id: Optional[str] = Field(None, description="Client-provided session ID (generated if omitted)")
    ttl_seconds: int = Field(3600, ge=60, le=86400, description="Session TTL in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class SessionContextSetRequest(BaseModel):
    """Request schema for setting session context."""

    key: str = Field(..., description="Context key", min_length=1)
    value: Any = Field(..., description="Context value (JSON-serializable)")
    ttl_seconds: Optional[int] = Field(None, description="Optional TTL override")


class SessionResponse(BaseModel):
    """Response schema for single session."""

    session: Session


class SessionContextResponse(BaseModel):
    """Response schema for session context."""

    key: str
    value: Any
    created_at: datetime
    updated_at: datetime


class SessionBriefingResponse(BaseModel):
    """Response schema for session briefing."""

    briefing: SessionBriefing


# Workspace API Schemas
class WorkspaceCreateRequest(BaseModel):
    """Request schema for creating a workspace."""

    name: str = Field(..., description="Workspace name", min_length=1)
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Workspace-level settings"
    )


class WorkspaceUpdateRequest(BaseModel):
    """Request schema for updating a workspace."""

    name: Optional[str] = Field(None, description="Updated workspace name", min_length=1)
    settings: Optional[dict[str, Any]] = Field(None, description="Updated settings")


class MemorySpaceCreateRequest(BaseModel):
    """Request schema for creating a memory space."""

    name: str = Field(..., description="Space name", min_length=1)
    description: Optional[str] = Field(None, description="Space description")
    settings: dict[str, Any] = Field(default_factory=dict, description="Space-level settings")


class WorkspaceResponse(BaseModel):
    """Response schema for single workspace."""

    workspace: Workspace


class MemorySpaceResponse(BaseModel):
    """Response schema for single memory space."""

    space: MemorySpace


class MemorySpaceListResponse(BaseModel):
    """Response schema for memory space list."""

    spaces: list[MemorySpace]
    total_count: int


# Error Responses
class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
