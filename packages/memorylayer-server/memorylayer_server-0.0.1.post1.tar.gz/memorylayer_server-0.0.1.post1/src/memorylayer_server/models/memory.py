"""
Memory domain models for MemoryLayer.ai.

Defines cognitive types, domain subtypes, and core memory data structures.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryType(str, Enum):
    """Cognitive classification of memory (how memory is structured)."""

    EPISODIC = "episodic"  # Specific events/interactions
    SEMANTIC = "semantic"  # Facts, concepts, relationships
    PROCEDURAL = "procedural"  # How to do things
    WORKING = "working"  # Current task context (session-scoped)


class MemorySubtype(str, Enum):
    """Domain classification of memory (what the memory is about)."""

    # Developer-focused taxonomy inspired by Memory-Graph
    SOLUTION = "solution"  # Working fixes to problems
    PROBLEM = "problem"  # Issues encountered
    CODE_PATTERN = "code_pattern"  # Reusable patterns
    FIX = "fix"  # Bug fixes with context
    ERROR = "error"  # Error patterns and resolutions
    WORKFLOW = "workflow"  # Process knowledge
    PREFERENCE = "preference"  # User/project preferences
    DECISION = "decision"  # Architectural decisions


class RecallMode(str, Enum):
    """Retrieval strategy for memory queries."""

    RAG = "rag"  # Fast vector similarity search
    LLM = "llm"  # Deep semantic retrieval with query rewriting
    HYBRID = "hybrid"  # Combine both strategies


class SearchTolerance(str, Enum):
    """Search precision setting affecting fuzzy matching."""

    LOOSE = "loose"  # Fuzzy matching, broader results, lower relevance threshold
    MODERATE = "moderate"  # Balanced precision/recall (default)
    STRICT = "strict"  # Exact matching, high relevance threshold


class Memory(BaseModel):
    """Core memory entity with content, metadata, and lifecycle tracking."""

    model_config = {"from_attributes": True}

    # Identity
    id: str = Field(..., description="Unique memory identifier")
    workspace_id: str = Field(..., description="Workspace this memory belongs to")
    space_id: Optional[str] = Field(None, description="Optional memory space for logical grouping")
    user_id: Optional[str] = Field(None, description="Optional user scope")

    # Content
    content: str = Field(..., description="The memory content")
    content_hash: str = Field(..., description="SHA-256 hash for deduplication")

    # Classification
    type: MemoryType = Field(..., description="Cognitive type of memory")
    subtype: Optional[MemorySubtype] = Field(None, description="Domain-specific classification")
    importance: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Memory importance (0.0-1.0, affects retention/ranking)"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")

    # Vector embedding (optional - computed async or stored separately)
    embedding: Optional[list[float]] = Field(None, description="Vector embedding for similarity search")

    # Lifecycle & access tracking
    access_count: int = Field(0, ge=0, description="Number of times memory was accessed")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    decay_factor: float = Field(1.0, ge=0.0, le=1.0, description="Memory decay over time")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Memory content cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags (lowercase, no duplicates)."""
        return sorted(set(tag.lower().strip() for tag in v if tag.strip()))


class RememberInput(BaseModel):
    """Request model for creating a new memory."""

    content: str = Field(..., description="The memory content to store")
    type: Optional[MemoryType] = Field(None, description="Cognitive type (auto-classified if omitted)")
    subtype: Optional[MemorySubtype] = Field(None, description="Domain-specific classification")
    importance: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Memory importance (0.0-1.0)"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
    associations: list[str] = Field(default_factory=list, description="Memory IDs to associate with")

    # Optional overrides (usually auto-computed)
    space_id: Optional[str] = Field(None, description="Target memory space")
    user_id: Optional[str] = Field(None, description="User scope override")


class RecallInput(BaseModel):
    """Request model for querying memories."""

    query: str = Field(..., description="Natural language query or search text")

    # Filters
    types: list[MemoryType] = Field(default_factory=list, description="Filter by cognitive types")
    subtypes: list[MemorySubtype] = Field(default_factory=list, description="Filter by domain subtypes")
    tags: list[str] = Field(default_factory=list, description="Filter by tags (AND logic)")
    space_id: Optional[str] = Field(None, description="Filter by memory space")
    user_id: Optional[str] = Field(None, description="Filter by user")

    # Retrieval settings
    mode: RecallMode = Field(RecallMode.RAG, description="Retrieval strategy")
    tolerance: SearchTolerance = Field(SearchTolerance.MODERATE, description="Search precision")
    limit: int = Field(10, ge=1, le=100, description="Maximum memories to return")
    min_relevance: float = Field(0.5, ge=0.0, le=1.0, description="Minimum relevance score")

    # Graph traversal
    include_associations: bool = Field(False, description="Include linked memories")
    traverse_depth: int = Field(0, ge=0, le=5, description="Multi-hop graph traversal depth")

    # Time range filters
    created_after: Optional[datetime] = Field(None, description="Filter memories created after this time")
    created_before: Optional[datetime] = Field(None, description="Filter memories created before this time")

    # LLM mode options
    context: list[dict[str, str]] = Field(
        default_factory=list,
        description="Recent conversation context for query rewriting (LLM mode)"
    )
    max_tokens: Optional[int] = Field(None, description="Token budget for LLM reasoning")

    # Hybrid mode options
    rag_threshold: float = Field(
        0.8,
        ge=0.0,
        le=1.0,
        description="Use LLM if RAG confidence < threshold (hybrid mode)"
    )


class RecallResult(BaseModel):
    """Response model for memory recall queries."""

    memories: list[Memory] = Field(..., description="Retrieved memories")
    total_count: int = Field(..., description="Total matching memories (may exceed returned count)")
    query_tokens: int = Field(0, description="Tokens used in query processing")
    search_latency_ms: int = Field(0, description="Search latency in milliseconds")
    mode_used: RecallMode = Field(..., description="Actual retrieval mode used")

    # LLM mode metadata
    query_rewritten: Optional[str] = Field(None, description="Rewritten query (LLM mode)")
    sufficiency_reached: Optional[bool] = Field(None, description="Whether search stopped early (LLM mode)")


class ReflectInput(BaseModel):
    """Request model for synthesizing memories."""

    query: str = Field(..., description="What to reflect on")
    max_tokens: int = Field(500, ge=50, le=4000, description="Maximum tokens in reflection")
    include_sources: bool = Field(True, description="Include source memory references")
    depth: int = Field(2, ge=1, le=5, description="Association traversal depth")

    # Optional filters (same as RecallInput)
    types: list[MemoryType] = Field(default_factory=list)
    subtypes: list[MemorySubtype] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    space_id: Optional[str] = None
    user_id: Optional[str] = None


class ReflectResult(BaseModel):
    """Response model for memory reflection/synthesis."""

    reflection: str = Field(..., description="Synthesized reflection content")
    source_memories: list[str] = Field(default_factory=list, description="Source memory IDs")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in synthesis")
    tokens_processed: int = Field(0, description="Total tokens used")
