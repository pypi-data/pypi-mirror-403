"""Example usage of MemoryLayer MCP server."""

import asyncio
import json
import logging

from ..config import EmbeddingProviderType
from ..services.embedding_service import EmbeddingService
from memorylayer_server.services.storage.sqlite import SQLiteStorageBackend
from .server import create_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_usage():
    """Demonstrate MCP server usage with in-memory SQLite."""
    logger.info("=== MemoryLayer MCP Server Example ===")

    # Create in-memory SQLite backend for testing
    storage = SQLiteStorageBackend("sqlite+aiosqlite:///:memory:")
    await storage.connect()

    # Create simple local embedding service
    embedding_service = EmbeddingService.create(
        provider_type=EmbeddingProviderType.LOCAL,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu"
    )

    # Create MCP server
    server = await create_server(
        storage=storage,
        embedding_service=embedding_service,
        workspace_id="example_workspace",
        tool_profile="extended"
    )

    logger.info("MCP Server initialized")
    logger.info("Manifest: %s", json.dumps(server.get_manifest(), indent=2))

    # Example 1: Store a memory
    logger.info("\n--- Example 1: Store Memory ---")
    remember_args = {
        "content": "PostgreSQL is the preferred database for this project",
        "type": "semantic",
        "subtype": "Preference",
        "importance": 0.8,
        "tags": ["database", "preferences"]
    }
    result = await server.handlers.handle_memory_remember("example_workspace", remember_args)
    logger.info("Result: %s", json.dumps(result, indent=2))
    memory_id_1 = result["memory_id"]

    # Example 2: Store another memory
    logger.info("\n--- Example 2: Store Another Memory ---")
    remember_args_2 = {
        "content": "Use connection pooling with max 20 connections",
        "type": "procedural",
        "subtype": "CodePattern",
        "importance": 0.7,
        "tags": ["database", "performance"]
    }
    result = await server.handlers.handle_memory_remember("example_workspace", remember_args_2)
    logger.info("Result: %s", json.dumps(result, indent=2))
    memory_id_2 = result["memory_id"]

    # Example 3: Recall memories
    logger.info("\n--- Example 3: Recall Memories ---")
    recall_args = {
        "query": "What are the database recommendations?",
        "limit": 10,
        "min_relevance": 0.3
    }
    result = await server.handlers.handle_memory_recall("example_workspace", recall_args)
    logger.info("Found %d memories", len(result["memories"]))
    for memory in result["memories"]:
        logger.info("  - [%s] %s", memory["type"], memory["content"][:60])

    # Example 4: Create association
    logger.info("\n--- Example 4: Create Association ---")
    associate_args = {
        "source_id": memory_id_2,
        "target_id": memory_id_1,
        "relationship": "APPLIES_TO",
        "strength": 0.8
    }
    result = await server.handlers.handle_memory_associate("example_workspace", associate_args)
    logger.info("Result: %s", json.dumps(result, indent=2))

    # Example 5: Reflect on memories
    logger.info("\n--- Example 5: Memory Reflection ---")
    reflect_args = {
        "query": "What database practices should we follow?",
        "max_tokens": 300,
        "include_sources": True,
        "depth": 2
    }
    result = await server.handlers.handle_memory_reflect("example_workspace", reflect_args)
    logger.info("Reflection: %s", result["reflection"])
    logger.info("Sources: %s", result["source_memories"])
    logger.info("Confidence: %.2f", result["confidence"])

    # Example 6: Session briefing
    logger.info("\n--- Example 6: Session Briefing ---")
    briefing_args = {
        "lookback_hours": 24,
        "include_contradictions": True
    }
    result = await server.handlers.handle_memory_briefing("example_workspace", briefing_args)
    logger.info("Briefing:\n%s", result["briefing"])

    # Example 7: Statistics
    logger.info("\n--- Example 7: Memory Statistics ---")
    stats_args = {"include_breakdown": True}
    result = await server.handlers.handle_memory_statistics("example_workspace", stats_args)
    logger.info("Statistics: %s", json.dumps(result, indent=2))

    # Example 8: Graph query
    logger.info("\n--- Example 8: Graph Query ---")
    graph_args = {
        "start_memory_id": memory_id_2,
        "max_depth": 2,
        "direction": "both"
    }
    result = await server.handlers.handle_memory_graph_query("example_workspace", graph_args)
    logger.info("Found %d paths", result["total_paths"])
    logger.info("Unique nodes: %s", result["unique_nodes"])

    # Example 9: Memory audit
    logger.info("\n--- Example 9: Memory Audit ---")
    audit_args = {
        "auto_resolve": False
    }
    result = await server.handlers.handle_memory_audit("example_workspace", audit_args)
    logger.info("Contradictions found: %d", result["contradictions_found"])

    # Example 10: Forget memory
    logger.info("\n--- Example 10: Forget Memory ---")
    forget_args = {
        "memory_id": memory_id_1,
        "reason": "Outdated preference",
        "hard": False
    }
    result = await server.handlers.handle_memory_forget("example_workspace", forget_args)
    logger.info("Result: %s", json.dumps(result, indent=2))

    # Cleanup
    await storage.disconnect()
    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(example_usage())
