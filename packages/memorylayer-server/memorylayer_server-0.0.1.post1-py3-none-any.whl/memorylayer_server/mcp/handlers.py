"""MCP tool handler implementations."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..models.memory import (
    Memory, MemoryType, MemorySubtype, RememberInput, RecallInput,
    RecallMode, ReflectInput
)
from ..models.association import AssociateInput, RelationshipType, GraphQueryInput
from ..services.memory import MemoryService
from ..services.association import AssociationService
from ..services.reflect import ReflectService

logger = logging.getLogger(__name__)


class MCPToolHandlers:
    """Handlers for MCP tool invocations."""

    def __init__(
        self,
        memory_service: MemoryService,
        association_service: AssociationService,
        reflect_service: Optional[Any] = None,
    ):
        self.memory_service = memory_service
        self.reflect_service = reflect_service
        self.association_service = association_service

    async def handle_memory_remember(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_remember tool invocation."""
        logger.info("Handling memory_remember: %s", arguments.get("content", "")[:50])

        # Parse arguments
        content = arguments.get("content")
        if not content:
            raise ValueError("content is required")

        # Parse optional type
        memory_type = None
        if "type" in arguments:
            memory_type = MemoryType(arguments["type"])

        # Parse optional subtype
        subtype = None
        if "subtype" in arguments:
            subtype = MemorySubtype(arguments["subtype"])

        # Create input
        input_data = RememberInput(
            content=content,
            type=memory_type,
            subtype=subtype,
            importance=arguments.get("importance", 0.5),
            tags=arguments.get("tags", []),
        )

        # Store memory
        memory = await self.memory_service.remember(workspace_id, input_data)

        return {
            "success": True,
            "memory_id": memory.id,
            "type": memory.type.value,
            "importance": memory.importance,
            "tags": memory.tags,
            "message": f"Stored memory {memory.id}"
        }

    async def handle_memory_recall(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_recall tool invocation."""
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required")

        logger.info("Handling memory_recall: %s", query[:50])

        # Parse types filter
        types = []
        if "types" in arguments:
            types = [MemoryType(t) for t in arguments["types"]]

        # Create recall input
        input_data = RecallInput(
            query=query,
            types=types,
            tags=arguments.get("tags", []),
            limit=arguments.get("limit", 10),
            min_relevance=arguments.get("min_relevance", 0.5),
            mode=RecallMode.RAG,  # Use fast RAG mode for MCP
        )

        # Recall memories
        result = await self.memory_service.recall(workspace_id, input_data)

        # Format response
        memories_data = []
        for memory in result.memories:
            memories_data.append({
                "id": memory.id,
                "content": memory.content,
                "type": memory.type.value,
                "subtype": memory.subtype.value if memory.subtype else None,
                "importance": memory.importance,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
                "access_count": memory.access_count,
            })

        return {
            "success": True,
            "memories": memories_data,
            "total_count": result.total_count,
            "search_latency_ms": result.search_latency_ms,
            "mode_used": result.mode_used.value,
        }

    async def handle_memory_reflect(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_reflect tool invocation."""
        if self.reflect_service is None:
            raise ValueError(
                "ReflectService not initialized. This is an internal error."
            )

        query = arguments.get("query")
        if not query:
            raise ValueError("query is required")

        logger.info("Handling memory_reflect: %s", query[:50])

        # Create reflect input
        input_data = ReflectInput(
            query=query,
            max_tokens=arguments.get("max_tokens", 500),
            include_sources=arguments.get("include_sources", True),
            depth=arguments.get("depth", 2),
        )

        # Generate reflection
        result = await self.reflect_service.reflect(workspace_id, input_data)

        return {
            "success": True,
            "reflection": result.reflection,
            "source_memories": result.source_memories if input_data.include_sources else [],
            "confidence": result.confidence,
            "tokens_processed": result.tokens_processed,
        }

    async def handle_memory_forget(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_forget tool invocation."""
        memory_id = arguments.get("memory_id")
        if not memory_id:
            raise ValueError("memory_id is required")

        logger.info("Handling memory_forget: %s", memory_id)

        reason = arguments.get("reason", "No reason provided")
        hard = arguments.get("hard", False)

        # Forget memory
        success = await self.memory_service.forget(
            workspace_id=workspace_id,
            memory_id=memory_id,
            hard=hard,
            reason=reason
        )

        return {
            "success": success,
            "memory_id": memory_id,
            "hard_delete": hard,
            "reason": reason,
            "message": f"Forgot memory {memory_id}" if success else f"Failed to forget memory {memory_id}"
        }

    async def handle_memory_associate(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_associate tool invocation."""
        source_id = arguments.get("source_id")
        target_id = arguments.get("target_id")
        relationship = arguments.get("relationship")

        if not all([source_id, target_id, relationship]):
            raise ValueError("source_id, target_id, and relationship are required")

        logger.info(
            "Handling memory_associate: %s -[%s]-> %s",
            source_id,
            relationship,
            target_id
        )

        # Parse relationship type
        relationship_type = RelationshipType(relationship)

        # Create association input
        input_data = AssociateInput(
            source_id=source_id,
            target_id=target_id,
            relationship=relationship_type,
            strength=arguments.get("strength", 0.8),
        )

        # Create association
        association = await self.association_service.associate(workspace_id, input_data)

        return {
            "success": True,
            "association_id": association.id,
            "source_id": association.source_id,
            "target_id": association.target_id,
            "relationship": association.relationship.value,
            "strength": association.strength,
            "message": f"Created association {association.id}"
        }

    async def handle_memory_briefing(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_briefing tool invocation."""
        logger.info("Handling memory_briefing for workspace: %s", workspace_id)

        lookback_hours = arguments.get("lookback_hours", 24)
        include_contradictions = arguments.get("include_contradictions", True)

        # Calculate time threshold
        threshold = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        # Recall recent memories
        recall_input = RecallInput(
            query="",  # Empty query for chronological retrieval
            limit=50,
            min_relevance=0.0,  # Get all recent memories
            created_after=threshold,
            mode=RecallMode.RAG,
        )

        result = await self.memory_service.recall(workspace_id, recall_input)

        # Get workspace statistics
        stats = await self.memory_service.storage.get_workspace_stats(workspace_id)

        # Find contradictions if requested
        contradictions = []
        if include_contradictions:
            try:
                contradiction_pairs = await self.association_service.find_contradictions(
                    workspace_id=workspace_id
                )
                contradictions = [
                    {"memory_a": pair[0], "memory_b": pair[1]}
                    for pair in contradiction_pairs
                ]
            except Exception as e:
                logger.warning("Failed to find contradictions: %s", e)

        # Build briefing
        briefing_parts = [
            f"# Session Briefing (Last {lookback_hours} hours)",
            "",
            f"## Recent Activity",
            f"- {len(result.memories)} new/updated memories",
            "",
        ]

        if result.memories:
            briefing_parts.append("## Recent Memories:")
            for memory in result.memories[:10]:  # Show top 10
                briefing_parts.append(
                    f"- [{memory.type.value}] {memory.content[:100]}..."
                )
            briefing_parts.append("")

        briefing_parts.extend([
            "## Workspace Statistics",
            f"- Total memories: {stats.get('total_memories', 0)}",
            f"- Total associations: {stats.get('total_associations', 0)}",
        ])

        if contradictions:
            briefing_parts.extend([
                "",
                f"## ⚠️ Contradictions Found: {len(contradictions)}",
                "- Review these memory conflicts:",
            ])
            for contradiction in contradictions[:5]:  # Show top 5
                briefing_parts.append(
                    f"  - {contradiction['memory_a']} <-> {contradiction['memory_b']}"
                )

        briefing_text = "\n".join(briefing_parts)

        return {
            "success": True,
            "briefing": briefing_text,
            "recent_memory_count": len(result.memories),
            "total_memories": stats.get("total_memories", 0),
            "total_associations": stats.get("total_associations", 0),
            "contradictions_found": len(contradictions),
        }

    async def handle_memory_statistics(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_statistics tool invocation."""
        logger.info("Handling memory_statistics for workspace: %s", workspace_id)

        include_breakdown = arguments.get("include_breakdown", True)

        # Get workspace statistics
        stats = await self.memory_service.storage.get_workspace_stats(workspace_id)

        result = {
            "success": True,
            "total_memories": stats.get("total_memories", 0),
            "total_associations": stats.get("total_associations", 0),
        }

        if include_breakdown:
            result["breakdown"] = {
                "by_type": stats.get("by_type", {}),
                "by_subtype": stats.get("by_subtype", {}),
            }

        return result

    async def handle_memory_graph_query(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_graph_query tool invocation."""
        start_memory_id = arguments.get("start_memory_id")
        if not start_memory_id:
            raise ValueError("start_memory_id is required")

        logger.info("Handling memory_graph_query from: %s", start_memory_id)

        # Parse relationship types
        relationship_types = None
        if "relationship_types" in arguments:
            relationship_types = [
                RelationshipType(rt) for rt in arguments["relationship_types"]
            ]

        # Create graph query input
        query_input = GraphQueryInput(
            start_memory_id=start_memory_id,
            relationship_types=relationship_types,
            max_depth=arguments.get("max_depth", 3),
            direction=arguments.get("direction", "both"),
            max_paths=arguments.get("max_paths", 50),
        )

        # Traverse graph
        result = await self.association_service.traverse(workspace_id, query_input)

        # Format paths
        paths_data = []
        for path in result.paths:
            paths_data.append({
                "nodes": path.nodes,
                "edges": [
                    {
                        "from": edge.source_id,
                        "to": edge.target_id,
                        "relationship": edge.relationship.value,
                        "strength": edge.strength,
                    }
                    for edge in path.edges
                ],
                "total_strength": path.total_strength,
            })

        return {
            "success": True,
            "paths": paths_data,
            "total_paths": result.total_paths,
            "unique_nodes": result.unique_nodes,
        }

    async def handle_memory_audit(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_audit tool invocation."""
        logger.info("Handling memory_audit for workspace: %s", workspace_id)

        memory_id = arguments.get("memory_id")
        auto_resolve = arguments.get("auto_resolve", False)

        # Find contradictions
        contradictions = await self.association_service.find_contradictions(
            workspace_id=workspace_id,
            memory_id=memory_id
        )

        contradiction_details = []
        for memory_a_id, memory_b_id in contradictions:
            # Get memory details
            memory_a = await self.memory_service.get(workspace_id, memory_a_id)
            memory_b = await self.memory_service.get(workspace_id, memory_b_id)

            if memory_a and memory_b:
                contradiction_details.append({
                    "memory_a": {
                        "id": memory_a.id,
                        "content": memory_a.content[:200],
                        "created_at": memory_a.created_at.isoformat(),
                    },
                    "memory_b": {
                        "id": memory_b.id,
                        "content": memory_b.content[:200],
                        "created_at": memory_b.created_at.isoformat(),
                    },
                    "resolved": False,
                })

                # Auto-resolve if requested (mark newer as preferred)
                if auto_resolve:
                    if memory_a.created_at > memory_b.created_at:
                        # Memory A is newer, mark as superseding B
                        await self.association_service.associate(
                            workspace_id,
                            AssociateInput(
                                source_id=memory_a.id,
                                target_id=memory_b.id,
                                relationship=RelationshipType.SUPERSEDES,
                                strength=0.9,
                            )
                        )
                    else:
                        # Memory B is newer
                        await self.association_service.associate(
                            workspace_id,
                            AssociateInput(
                                source_id=memory_b.id,
                                target_id=memory_a.id,
                                relationship=RelationshipType.SUPERSEDES,
                                strength=0.9,
                            )
                        )
                    contradiction_details[-1]["resolved"] = True

        return {
            "success": True,
            "contradictions_found": len(contradiction_details),
            "contradictions": contradiction_details,
            "auto_resolved": auto_resolve,
        }

    async def handle_memory_compress(
        self,
        workspace_id: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle memory_compress tool invocation."""
        logger.info("Handling memory_compress for workspace: %s", workspace_id)

        older_than_days = arguments.get("older_than_days", 90)
        min_access_count = arguments.get("min_access_count", 0)
        preserve_important = arguments.get("preserve_important", True)
        dry_run = arguments.get("dry_run", True)

        # Calculate time threshold
        threshold = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        # Find candidate memories
        recall_input = RecallInput(
            query="",
            limit=1000,  # Large limit to find many old memories
            min_relevance=0.0,
            created_before=threshold,
            mode=RecallMode.RAG,
        )

        result = await self.memory_service.recall(workspace_id, recall_input)

        # Filter candidates
        candidates = []
        for memory in result.memories:
            # Skip if accessed frequently
            if memory.access_count > min_access_count:
                continue

            # Skip if important and preserve_important is True
            if preserve_important and memory.importance > 0.7:
                continue

            candidates.append({
                "id": memory.id,
                "content": memory.content[:100],
                "type": memory.type.value,
                "importance": memory.importance,
                "access_count": memory.access_count,
                "created_at": memory.created_at.isoformat(),
            })

        message = f"Found {len(candidates)} memories eligible for compression"
        if dry_run:
            message += " (dry run - no memories were modified)"
        else:
            # In production, would implement actual compression logic
            message += " (compression not yet implemented)"
            logger.warning("Memory compression implementation pending")

        return {
            "success": True,
            "dry_run": dry_run,
            "candidates_found": len(candidates),
            "candidates": candidates[:20],  # Return sample
            "message": message,
        }
