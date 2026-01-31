"""
Association Service - Memory graph relationship operations.

Handles:
- Creating associations between memories
- Traversing relationship graph
- Finding causal chains
- Detecting contradictions
"""

from logging import Logger
from typing import Optional
from uuid import uuid4

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import AssociationServicePluginBase
from ..storage import StorageBackend, EXT_STORAGE
from ...models import AssociateInput, Association, RelationshipType, GraphQueryInput, GraphQueryResult, RelationshipCategory


class AssociationService:
    """Service for managing memory associations and graph operations."""

    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info("Initialized AssociationService")

    async def associate(
            self,
            workspace_id: str,
            input: AssociateInput,
    ) -> Association:
        """Create a relationship between two memories."""
        self.logger.info(
            "Creating association: %s -[%s]-> %s",
            input.source_id,
            input.relationship,
            input.target_id
        )

        # Validate that both memories exist
        source = await self.storage.get_memory(workspace_id, input.source_id)
        target = await self.storage.get_memory(workspace_id, input.target_id)

        if not source:
            raise ValueError(f"Source memory not found: {input.source_id}")
        if not target:
            raise ValueError(f"Target memory not found: {input.target_id}")

        # Prevent self-associations
        if input.source_id == input.target_id:
            raise ValueError("Cannot create self-association")

        # Create association
        association = await self.storage.create_association(workspace_id, input)

        self.logger.info("Created association: %s", association.id)
        return association

    async def get_related(
            self,
            workspace_id: str,
            memory_id: str,
            relationships: Optional[list[RelationshipType]] = None,
            direction: str = "both",
    ) -> list[Association]:
        """Get all associations for a memory."""
        self.logger.debug(
            "Getting related memories for: %s, direction: %s",
            memory_id,
            direction
        )

        # Validate direction
        if direction not in ["outgoing", "incoming", "both"]:
            raise ValueError(f"Invalid direction: {direction}")

        # Convert relationship types to strings
        relationship_strs = None
        if relationships:
            relationship_strs = [r.value for r in relationships]

        associations = await self.storage.get_associations(
            workspace_id=workspace_id,
            memory_id=memory_id,
            direction=direction,
            relationships=relationship_strs
        )

        self.logger.debug("Found %s associations for memory: %s", len(associations), memory_id)
        return associations

    async def traverse(
            self,
            workspace_id: str,
            input: GraphQueryInput,
    ) -> GraphQueryResult:
        """
        Multi-hop graph traversal.

        Example: Find what caused a problem:
        [Problem] <--CAUSED_BY-- [Error] <--TRIGGERED_BY-- [Change]
        """
        self.logger.info(
            "Traversing graph from: %s, max_depth: %s, direction: %s",
            input.start_memory_id,
            input.max_depth,
            input.direction
        )

        # Validate direction
        if input.direction not in ["outgoing", "incoming", "both"]:
            raise ValueError(f"Invalid direction: {input.direction}")

        # Convert relationship types to strings
        relationship_strs = None
        if input.relationship_types:
            relationship_strs = [r.value for r in input.relationship_types]

        # Perform traversal via storage backend
        result = await self.storage.traverse_graph(
            workspace_id=workspace_id,
            start_id=input.start_memory_id,
            max_depth=input.max_depth,
            relationships=relationship_strs,
            direction=input.direction
        )

        self.logger.info(
            "Graph traversal found %s paths, %s unique nodes",
            result.total_paths,
            len(result.unique_nodes)
        )

        return result

    async def find_contradictions(
            self,
            workspace_id: str,
            memory_id: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """
        Find memories that contradict each other.

        Returns list of (memory_id_a, memory_id_b) tuples.
        """
        self.logger.info("Finding contradictions in workspace: %s", workspace_id)

        contradictions = []

        if memory_id:
            # Find contradictions for specific memory
            associations = await self.storage.get_associations(
                workspace_id=workspace_id,
                memory_id=memory_id,
                direction="both",
                relationships=[RelationshipType.CONTRADICTS.value]
            )

            for assoc in associations:
                # Determine which is the other memory
                other_id = assoc.target_id if assoc.source_id == memory_id else assoc.source_id
                contradictions.append((memory_id, other_id))

        else:
            # Find all contradictions in workspace
            # This requires a more complex query - for now, we'll need to traverse all memories
            # In production, this would be optimized with a specialized storage query
            self.logger.warning("Finding all contradictions requires full workspace scan - expensive operation")

            # Get workspace stats to determine scope
            stats = await self.storage.get_workspace_stats(workspace_id)
            total_memories = stats.get("total_memories", 0)

            if total_memories > 1000:
                self.logger.warning("Workspace has %s memories - contradiction scan may be slow", total_memories)

            # This is a placeholder - in production, would use specialized query
            # For now, return empty list
            self.logger.warning("Full workspace contradiction scan not yet implemented")

        self.logger.info("Found %s contradictions", len(contradictions))
        return contradictions

    async def auto_associate(
            self,
            workspace_id: str,
            new_memory_id: str,
            similar_memories: list[tuple[str, float]],
            threshold: float = 0.85,
    ) -> list[Association]:
        """
        Automatically create SIMILAR_TO associations for highly similar memories.
        """
        self.logger.debug(
            "Auto-associating memory: %s with %s similar memories",
            new_memory_id,
            len(similar_memories)
        )

        associations = []

        for similar_id, similarity_score in similar_memories:
            # Skip if below threshold
            if similarity_score < threshold:
                continue

            # Skip self-associations
            if similar_id == new_memory_id:
                continue

            try:
                # Create SIMILAR_TO association with strength based on similarity
                assoc_input = AssociateInput(
                    source_id=new_memory_id,
                    target_id=similar_id,
                    relationship=RelationshipType.SIMILAR_TO,
                    strength=similarity_score,
                    metadata={"auto_generated": True, "similarity_score": similarity_score}
                )

                association = await self.storage.create_association(workspace_id, assoc_input)
                associations.append(association)

                self.logger.debug(
                    "Auto-associated %s -> %s (similarity: %.2f)",
                    new_memory_id,
                    similar_id,
                    similarity_score
                )

            except Exception as e:
                self.logger.warning(
                    "Failed to auto-associate %s with %s: %s",
                    new_memory_id,
                    similar_id,
                    e
                )

        self.logger.info("Created %s auto-associations for memory: %s", len(associations), new_memory_id)
        return associations

    def _generate_id(self, prefix: str = "assoc") -> str:
        """Generate unique association ID."""
        return f"{prefix}_{uuid4().hex[:12]}"

    async def get_causal_chain(
            self,
            workspace_id: str,
            effect_memory_id: str,
            max_depth: int = 5,
    ) -> GraphQueryResult:
        """
        Find causal chain leading to a specific memory.

        Traverses backwards through CAUSES, TRIGGERS, LEADS_TO relationships.
        """
        self.logger.info("Finding causal chain for memory: %s", effect_memory_id)

        # Define causal relationships
        causal_relationships = [
            RelationshipType.CAUSES,
            RelationshipType.TRIGGERS,
            RelationshipType.LEADS_TO,
        ]

        # Traverse incoming edges (what caused this)
        query = GraphQueryInput(
            start_memory_id=effect_memory_id,
            relationship_types=causal_relationships,
            max_depth=max_depth,
            direction="incoming",
            max_paths=50,
            max_nodes=100
        )

        result = await self.traverse(workspace_id, query)

        self.logger.info("Found causal chain with %s paths", len(result.paths))
        return result

    async def get_solutions_for_problem(
            self,
            workspace_id: str,
            problem_memory_id: str,
    ) -> list[str]:
        """
        Find all memories that solve or address a specific problem.

        Returns list of solution memory IDs.
        """
        self.logger.info("Finding solutions for problem: %s", problem_memory_id)

        # Get outgoing SOLVES and ADDRESSES relationships
        solution_relationships = [
            RelationshipType.SOLVES,
            RelationshipType.ADDRESSES,
        ]

        associations = await self.storage.get_associations(
            workspace_id=workspace_id,
            memory_id=problem_memory_id,
            direction="incoming",  # Things that solve this problem
            relationships=[r.value for r in solution_relationships]
        )

        solution_ids = [assoc.source_id for assoc in associations]

        self.logger.info("Found %s solutions for problem: %s", len(solution_ids), problem_memory_id)
        return solution_ids

    async def get_related_by_category(
            self,
            workspace_id: str,
            memory_id: str,
            category: RelationshipCategory,
            max_depth: int = 2,
    ) -> GraphQueryResult:
        """
        Find memories related by a specific relationship category.

        Example: Get all causal relationships (CAUSES, TRIGGERS, LEADS_TO, PREVENTS)
        """
        self.logger.info(
            "Finding memories related to %s by category: %s",
            memory_id,
            category
        )

        # Get all relationship types in this category
        relationship_types = []
        for rel_type in RelationshipType:
            if RelationshipType.get_category(rel_type) == category:
                relationship_types.append(rel_type)

        query = GraphQueryInput(
            start_memory_id=memory_id,
            relationship_types=relationship_types,
            max_depth=max_depth,
            direction="both",
            max_paths=100,
            max_nodes=200
        )

        result = await self.traverse(workspace_id, query)

        self.logger.info(
            "Found %s paths in category %s",
            len(result.paths),
            category
        )

        return result


class DefaultAssociationServicePlugin(AssociationServicePluginBase):
    """Default association service plugin."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> AssociationService:
        storage_backend: StorageBackend = self.get_extension(EXT_STORAGE, v)
        return AssociationService(
            storage=storage_backend
        )
