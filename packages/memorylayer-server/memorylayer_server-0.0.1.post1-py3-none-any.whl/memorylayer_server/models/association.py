"""
Association and relationship models for MemoryLayer.ai semantic graph.

Defines 25+ relationship types organized by category for rich knowledge graphs.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RelationshipCategory(str, Enum):
    """High-level categories for relationship types."""

    CAUSAL = "causal"  # Cause and effect relationships
    SOLUTION = "solution"  # Problem-solving relationships
    CONTEXT = "context"  # Contextual and applicability
    LEARNING = "learning"  # Knowledge evolution
    SIMILARITY = "similarity"  # Similarity and relatedness
    WORKFLOW = "workflow"  # Process and dependencies
    QUALITY = "quality"  # Quality and preference


class RelationshipType(str, Enum):
    """Typed edges for semantic memory graph."""

    # Causal relationships
    CAUSES = "causes"  # A causes B
    TRIGGERS = "triggers"  # A triggers B
    LEADS_TO = "leads_to"  # A leads to B
    PREVENTS = "prevents"  # A prevents B

    # Solution relationships
    SOLVES = "solves"  # A solves B
    ADDRESSES = "addresses"  # A addresses B
    ALTERNATIVE_TO = "alternative_to"  # A is alternative to B
    IMPROVES = "improves"  # A improves B

    # Context relationships
    OCCURS_IN = "occurs_in"  # A occurs in context B
    APPLIES_TO = "applies_to"  # A applies to B
    WORKS_WITH = "works_with"  # A works with B
    REQUIRES = "requires"  # A requires B

    # Learning relationships
    BUILDS_ON = "builds_on"  # A builds on B
    CONTRADICTS = "contradicts"  # A contradicts B
    CONFIRMS = "confirms"  # A confirms B
    SUPERSEDES = "supersedes"  # A supersedes B

    # Similarity relationships
    SIMILAR_TO = "similar_to"  # A is similar to B
    VARIANT_OF = "variant_of"  # A is variant of B
    RELATED_TO = "related_to"  # A is related to B

    # Workflow relationships
    FOLLOWS = "follows"  # A follows B in sequence
    DEPENDS_ON = "depends_on"  # A depends on B
    ENABLES = "enables"  # A enables B
    BLOCKS = "blocks"  # A blocks B

    # Quality relationships
    EFFECTIVE_FOR = "effective_for"  # A is effective for B
    PREFERRED_OVER = "preferred_over"  # A is preferred over B
    DEPRECATED_BY = "deprecated_by"  # A is deprecated by B

    @classmethod
    def get_category(cls, relationship: "RelationshipType") -> RelationshipCategory:
        """Get the category for a relationship type."""
        category_map = {
            # Causal
            cls.CAUSES: RelationshipCategory.CAUSAL,
            cls.TRIGGERS: RelationshipCategory.CAUSAL,
            cls.LEADS_TO: RelationshipCategory.CAUSAL,
            cls.PREVENTS: RelationshipCategory.CAUSAL,
            # Solution
            cls.SOLVES: RelationshipCategory.SOLUTION,
            cls.ADDRESSES: RelationshipCategory.SOLUTION,
            cls.ALTERNATIVE_TO: RelationshipCategory.SOLUTION,
            cls.IMPROVES: RelationshipCategory.SOLUTION,
            # Context
            cls.OCCURS_IN: RelationshipCategory.CONTEXT,
            cls.APPLIES_TO: RelationshipCategory.CONTEXT,
            cls.WORKS_WITH: RelationshipCategory.CONTEXT,
            cls.REQUIRES: RelationshipCategory.CONTEXT,
            # Learning
            cls.BUILDS_ON: RelationshipCategory.LEARNING,
            cls.CONTRADICTS: RelationshipCategory.LEARNING,
            cls.CONFIRMS: RelationshipCategory.LEARNING,
            cls.SUPERSEDES: RelationshipCategory.LEARNING,
            # Similarity
            cls.SIMILAR_TO: RelationshipCategory.SIMILARITY,
            cls.VARIANT_OF: RelationshipCategory.SIMILARITY,
            cls.RELATED_TO: RelationshipCategory.SIMILARITY,
            # Workflow
            cls.FOLLOWS: RelationshipCategory.WORKFLOW,
            cls.DEPENDS_ON: RelationshipCategory.WORKFLOW,
            cls.ENABLES: RelationshipCategory.WORKFLOW,
            cls.BLOCKS: RelationshipCategory.WORKFLOW,
            # Quality
            cls.EFFECTIVE_FOR: RelationshipCategory.QUALITY,
            cls.PREFERRED_OVER: RelationshipCategory.QUALITY,
            cls.DEPRECATED_BY: RelationshipCategory.QUALITY,
        }
        return category_map[relationship]


class Association(BaseModel):
    """Typed edge in the semantic memory graph."""

    model_config = {"from_attributes": True}

    # Identity
    id: str = Field(..., description="Unique association identifier")
    workspace_id: str = Field(..., description="Workspace boundary")

    # Graph structure
    source_id: str = Field(..., description="Source memory ID")
    target_id: str = Field(..., description="Target memory ID")
    relationship: RelationshipType = Field(..., description="Typed relationship")

    # Edge metadata
    strength: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Relationship strength (0.0-1.0)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")

    @property
    def category(self) -> RelationshipCategory:
        """Get the category of this relationship."""
        return RelationshipType.get_category(self.relationship)


class AssociateInput(BaseModel):
    """Request model for creating an association between memories."""

    source_id: str = Field(..., description="Source memory ID")
    target_id: str = Field(..., description="Target memory ID")
    relationship: RelationshipType = Field(..., description="Relationship type")
    strength: float = Field(0.5, ge=0.0, le=1.0, description="Relationship strength")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class GraphQueryInput(BaseModel):
    """Request model for multi-hop graph traversal."""

    start_memory_id: str = Field(..., description="Starting memory for traversal")

    # Filters
    relationship_types: list[RelationshipType] = Field(
        default_factory=list,
        description="Filter by specific relationship types (empty = all)"
    )
    relationship_categories: list[RelationshipCategory] = Field(
        default_factory=list,
        description="Filter by relationship categories (empty = all)"
    )

    # Traversal settings
    max_depth: int = Field(3, ge=1, le=5, description="Maximum traversal depth")
    direction: str = Field(
        "both",
        pattern="^(outgoing|incoming|both)$",
        description="Traversal direction: outgoing, incoming, both"
    )
    min_strength: float = Field(0.0, ge=0.0, le=1.0, description="Minimum edge strength")

    # Result limits
    max_paths: int = Field(100, ge=1, le=1000, description="Maximum paths to return")
    max_nodes: int = Field(50, ge=1, le=500, description="Maximum nodes in result")


class GraphPath(BaseModel):
    """A path through the memory graph."""

    nodes: list[str] = Field(..., description="Memory IDs in path order")
    edges: list[Association] = Field(..., description="Associations connecting nodes")
    total_strength: float = Field(..., description="Product of all edge strengths")
    depth: int = Field(..., description="Path length")


class GraphQueryResult(BaseModel):
    """Response model for graph queries."""

    paths: list[GraphPath] = Field(..., description="All paths found")
    total_paths: int = Field(..., description="Total paths (may exceed returned count)")
    unique_nodes: list[str] = Field(..., description="All unique memory IDs visited")
    query_latency_ms: int = Field(0, description="Query latency in milliseconds")
