"""MCP server implementation for MemoryLayer.ai."""

import asyncio
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..services.memory import MemoryService
from ..services.association import AssociationService
from ..services.reflect import ReflectService
from ..services.embedding import EmbeddingService
from ..services.storage import StorageBackend
from .tools import CORE_TOOLS, EXTENDED_TOOLS
from .handlers import MCPToolHandlers

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP server for MemoryLayer.ai.

    Can run as:
    - Embedded server (within FastAPI process)
    - Standalone server (stdio transport)
    """

    def __init__(
            self,
            storage: StorageBackend,
            embedding_service: EmbeddingService,
            workspace_id: str = "default",
            tool_profile: str = "core",
    ):
        """
        Initialize MCP server.

        Args:
            storage: Storage backend instance
            embedding_service: Embedding service instance
            workspace_id: Default workspace ID for memory operations
            tool_profile: Tool profile ('core' or 'extended')
        """
        self.storage = storage
        self.embedding_service = embedding_service
        self.workspace_id = workspace_id
        self.tool_profile = tool_profile

        # Initialize services
        self.memory_service = MemoryService(storage, embedding_service)
        self.association_service = AssociationService(storage)
        self.reflect_service = ReflectService(storage, self.memory_service)

        # Initialize handlers
        self.handlers = MCPToolHandlers(
            memory_service=self.memory_service,
            reflect_service=self.reflect_service,
            association_service=self.association_service,
        )

        # Create MCP server instance
        self.server = Server("memorylayer")

        # Register handlers
        self._register_handlers()

        logger.info(
            "Initialized MCPServer (workspace=%s, profile=%s)",
            workspace_id,
            tool_profile
        )

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools based on profile."""
            tools = []

            # Always include core tools
            for tool_def in CORE_TOOLS:
                tools.append(
                    Tool(
                        name=tool_def["name"],
                        description=tool_def["description"],
                        inputSchema=tool_def["inputSchema"],
                    )
                )

            # Include extended tools if profile is 'extended'
            if self.tool_profile == "extended":
                for tool_def in EXTENDED_TOOLS:
                    tools.append(
                        Tool(
                            name=tool_def["name"],
                            description=tool_def["description"],
                            inputSchema=tool_def["inputSchema"],
                        )
                    )

            logger.debug("Listed %s tools (profile=%s)", len(tools), self.tool_profile)
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool invocation."""
            logger.info("Tool invoked: %s", name)

            try:
                # Route to appropriate handler
                handler_method = f"handle_{name}"
                if not hasattr(self.handlers, handler_method):
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    return [TextContent(type="text", text=error_msg)]

                handler = getattr(self.handlers, handler_method)

                # Call handler with workspace_id and arguments
                result = await handler(self.workspace_id, arguments)

                # Format result as text content
                import json
                result_text = json.dumps(result, indent=2)

                return [TextContent(type="text", text=result_text)]

            except ValueError as e:
                # Validation error
                error_msg = f"Validation error: {str(e)}"
                logger.warning(error_msg)
                return [TextContent(type="text", text=error_msg)]

            except Exception as e:
                # Unexpected error
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=error_msg)]

    async def run_stdio(self) -> None:
        """Run server with stdio transport (for standalone mode)."""
        logger.info("Starting MCP server on stdio transport")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    def get_manifest(self) -> dict[str, Any]:
        """
        Generate server manifest for MCP client configuration.

        Returns manifest dict that clients can use to configure connection.
        """
        manifest = {
            "name": "memorylayer",
            "version": "0.1.0",
            "description": "MemoryLayer.ai - Memory infrastructure for LLM-powered agents",
            "homepage": "https://memorylayer.ai",
            "capabilities": {
                "tools": {
                    "core": [tool["name"] for tool in CORE_TOOLS],
                },
            },
            "configuration": {
                "workspace_id": self.workspace_id,
                "tool_profile": self.tool_profile,
            },
        }

        # Add extended tools to manifest if enabled
        if self.tool_profile == "extended":
            manifest["capabilities"]["tools"]["extended"] = [
                tool["name"] for tool in EXTENDED_TOOLS
            ]

        return manifest


async def create_server(
        storage: StorageBackend,
        embedding_service: EmbeddingService,
        workspace_id: str = "default",
        tool_profile: Optional[str] = None,
) -> MCPServer:
    """
    Factory function to create and initialize MCP server.

    Args:
        storage: Storage backend instance
        embedding_service: Embedding service instance
        workspace_id: Default workspace ID
        tool_profile: Tool profile override (defaults to 'core')

    Returns:
        Initialized MCPServer instance
    """
    # Use provided tool_profile or default to 'core'
    profile = tool_profile or "core"

    # Validate profile
    if profile not in ["core", "extended"]:
        logger.warning(
            "Invalid tool profile '%s', defaulting to 'core'",
            profile
        )
        profile = "core"

    # Create server
    server = MCPServer(
        storage=storage,
        embedding_service=embedding_service,
        workspace_id=workspace_id,
        tool_profile=profile,
    )

    return server


def run_standalone(
        workspace_id: str = "default",
        tool_profile: Optional[str] = None,
) -> None:
    """
    Run MCP server as standalone process with stdio transport.

    This is the entry point for running MemoryLayer as an MCP server.

    Usage:
        python -m memorylayer_server.mcp.server

    Environment variables:
        MEMORYLAYER_EMBEDDING_PROVIDER: mock, openai, local, qwen3-vl, colpali, vllm
        MEMORYLAYER_STORAGE_BACKEND: sqlite (default)
    """
    import sys
    from scitrera_app_framework import init_framework

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,  # MCP uses stdout for protocol, stderr for logs
    )

    async def _run():
        # Initialize framework and services via plugin pattern
        v = init_framework('memorylayer-server')

        # Import services to trigger plugin registration
        from ..services import get_storage_backend, get_embedding_service

        # Get services via plugin pattern
        storage = get_storage_backend(v)
        await storage.connect()

        try:
            embedding_service = get_embedding_service(v)

            # Create and run server
            server = await create_server(
                storage=storage,
                embedding_service=embedding_service,
                workspace_id=workspace_id,
                tool_profile=tool_profile,
            )

            logger.info("MCP server manifest: %s", server.get_manifest())

            await server.run_stdio()

        finally:
            await storage.disconnect()

    # Run async event loop
    asyncio.run(_run())


def run_mcp_server() -> None:
    """
    Entry point for CLI to start MCP server.

    Wrapper around run_standalone with default settings.
    """
    run_standalone(workspace_id="default", tool_profile=None)


if __name__ == "__main__":
    """Entry point for standalone MCP server."""
    import sys

    # Parse command line arguments
    workspace_id = "default"
    tool_profile = None

    if len(sys.argv) > 1:
        workspace_id = sys.argv[1]
    if len(sys.argv) > 2:
        tool_profile = sys.argv[2]

    run_standalone(workspace_id=workspace_id, tool_profile=tool_profile)
