"""
Category models for MemoryLayer.ai three-layer hierarchy.

Categories are aggregated summaries (e.g., "preferences.md", "coding_standards.md")
that sit above discrete memory items.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Category(BaseModel):
    """Aggregated summary layer above discrete memory items."""

    model_config = {"from_attributes": True}

    # Identity
    id: str = Field(..., description="Unique category identifier")
    workspace_id: str = Field(..., description="Workspace boundary")
    name: str = Field(..., description="Category name (e.g., 'preferences', 'coding_standards')")

    # Content
    summary: str = Field(..., description="Aggregated summary content (LLM-generated)")

    # Links to items
    item_ids: list[str] = Field(
        default_factory=list,
        description="Memory IDs that contribute to this category"
    )

    # Timestamps
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last time category was updated"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip().lower()

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        """Validate that summary is not empty."""
        if not v or not v.strip():
            raise ValueError("Category summary cannot be empty")
        return v.strip()


class CategoryUpdate(BaseModel):
    """Request to update a category (triggered by new items)."""

    category_id: Optional[str] = Field(None, description="Existing category ID (if updating)")
    name: str = Field(..., description="Category name")
    new_item_ids: list[str] = Field(..., description="New memory IDs to incorporate")


class CategorySummary(BaseModel):
    """Lightweight category metadata for listings."""

    id: str
    name: str
    item_count: int
    last_updated: datetime
