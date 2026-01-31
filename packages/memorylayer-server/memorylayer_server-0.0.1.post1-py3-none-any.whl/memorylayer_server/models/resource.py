"""
Resource models for MemoryLayer.ai three-layer memory hierarchy.

Resources are the raw data layer (conversations, documents, images, etc.)
that get extracted into discrete memory items.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ResourceType(str, Enum):
    """Type of raw resource to be processed."""

    CONVERSATION = "conversation"  # Chat/conversation JSON
    DOCUMENT = "document"  # Text/Markdown documents
    IMAGE = "image"  # PNG, JPG, etc.
    AUDIO = "audio"  # Audio files (transcribed)
    VIDEO = "video"  # Video files (frame sampling + transcript)
    PDF = "pdf"  # PDF documents (OCR + layout)


class Resource(BaseModel):
    """Raw data layer - original sources before extraction."""

    model_config = {"from_attributes": True}

    # Identity
    id: str = Field(..., description="Unique resource identifier")
    workspace_id: str = Field(..., description="Workspace boundary")

    # Content
    type: ResourceType = Field(..., description="Type of resource")
    content: Any = Field(..., description="Resource content (JSON, base64, text)")
    content_hash: str = Field(..., description="SHA-256 hash for deduplication")

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source metadata (filename, session_id, etc.)"
    )

    # Processing status
    processed: bool = Field(False, description="Whether resource has been extracted")
    extracted_items: list[str] = Field(
        default_factory=list,
        description="Memory IDs extracted from this resource"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: Any) -> Any:
        """Validate that content is present."""
        if v is None:
            raise ValueError("Resource content cannot be null")
        return v


class ExtractionOptions(BaseModel):
    """Options for resource-to-memory extraction."""

    extract_preferences: bool = Field(True, description="Extract user/project preferences")
    extract_decisions: bool = Field(True, description="Extract architectural decisions")
    extract_patterns: bool = Field(True, description="Extract code patterns and practices")
    extract_problems: bool = Field(True, description="Extract problems and issues")
    extract_solutions: bool = Field(True, description="Extract solutions and fixes")

    update_categories: bool = Field(True, description="Auto-update category summaries")
    detect_associations: bool = Field(True, description="Auto-detect relationships")

    min_importance: float = Field(0.3, ge=0.0, le=1.0, description="Minimum importance for extraction")


class MemorizeInput(BaseModel):
    """Request model for batch ingestion of resources."""

    resources: list[dict[str, Any]] = Field(
        ...,
        description="Resource objects with type, content, metadata"
    )
    extraction_options: ExtractionOptions = Field(
        default_factory=ExtractionOptions,
        description="Extraction configuration"
    )

    # Optional overrides
    space_id: Optional[str] = Field(None, description="Target memory space")
    user_id: Optional[str] = Field(None, description="User scope")


class ExtractedItem(BaseModel):
    """A memory item extracted from a resource."""

    id: str = Field(..., description="Memory ID")
    content: str = Field(..., description="Extracted memory content")
    type: str = Field(..., description="Cognitive type")
    subtype: Optional[str] = Field(None, description="Domain subtype")
    importance: float = Field(..., description="Assigned importance")
    source_resource: str = Field(..., description="Source resource ID")
    tags: list[str] = Field(default_factory=list, description="Auto-generated tags")


class MemorizeResult(BaseModel):
    """Response model for async resource processing."""

    task_id: str = Field(..., description="Async task identifier")
    status: str = Field(..., description="processing, completed, failed")
    resources_queued: int = Field(0, description="Number of resources queued")

    # Present when status=completed
    resources_created: Optional[int] = None
    items_extracted: Optional[int] = None
    categories_updated: Optional[list[str]] = None
    items: Optional[list[ExtractedItem]] = None

    # Webhook for status updates
    webhook_url: Optional[str] = None


class TraceResult(BaseModel):
    """Response model for tracing memory back to source."""

    memory: dict[str, Any] = Field(..., description="Memory details")
    source_resource: Optional[dict[str, Any]] = Field(None, description="Source resource details")
    category: Optional[dict[str, Any]] = Field(None, description="Parent category if applicable")

    # Full chain
    layer: str = Field(..., description="item or category")
    chain: list[str] = Field(..., description="Full chain from category -> item -> resource")
