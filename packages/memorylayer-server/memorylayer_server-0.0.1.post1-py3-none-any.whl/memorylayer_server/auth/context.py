"""
Memory Context Proxy - bound interface that auto-injects tenant/workspace/user.

This implements the Falcon3 Context Proxy pattern where bound interfaces
automatically inject context into all operations.
"""

from typing import Optional, Any, Dict, List
from types import TracebackType


class MemoryContext:
    """
    Bound context that auto-injects tenant/workspace/user into all operations.

    This provides a clean interface where developers don't have to manually
    pass tenant/workspace/user to every operation - the context automatically
    injects these values.

    Example:
        async with memory.bind(workspace="ws_123", user="user_456") as ctx:
            # All operations automatically scoped
            await ctx.remember("User prefers TypeScript")
            memories = await ctx.recall("programming preferences")

        # Or without async context manager:
        ctx = MemoryContext(workspace_id="ws_123", user_id="user_456")
        await ctx.remember("Important note")
    """

    def __init__(
        self,
        workspace_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        memory_service: Any = None,
    ):
        """
        Initialize memory context.

        Args:
            workspace_id: Workspace identifier (required)
            user_id: User identifier (optional)
            tenant_id: Tenant identifier (optional)
            memory_service: Memory service instance (injected by framework)
        """
        self._workspace_id = workspace_id
        self._user_id = user_id
        self._tenant_id = tenant_id
        self._service = memory_service

    @property
    def workspace_id(self) -> str:
        """Get workspace ID."""
        return self._workspace_id

    @property
    def user_id(self) -> Optional[str]:
        """Get user ID."""
        return self._user_id

    @property
    def tenant_id(self) -> Optional[str]:
        """Get tenant ID."""
        return self._tenant_id

    async def remember(
        self,
        content: str,
        type: str = "semantic",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Store a memory with auto-injected context.

        All workspace_id, user_id, tenant_id are automatically injected
        from the bound context.

        Args:
            content: Memory content
            type: Memory type (episodic, semantic, procedural, working)
            importance: Importance score 0.0-1.0
            tags: Optional tags
            metadata: Optional metadata
            **kwargs: Additional parameters

        Returns:
            Created memory object

        Example:
            >>> ctx = MemoryContext(workspace_id="ws_123", user_id="user_456")
            >>> memory = await ctx.remember("User prefers FastAPI")
            >>> print(memory["id"])
            mem_abc123
        """
        # NOTE: This will be implemented when we have the core memory module
        # For now, this is a placeholder showing the interface design

        if self._service is None:
            raise RuntimeError("Memory service not configured")

        # Auto-inject context
        return await self._service.remember(
            content=content,
            type=type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
            workspace_id=self._workspace_id,
            user_id=self._user_id,
            tenant_id=self._tenant_id,
            **kwargs,
        )

    async def recall(
        self,
        query: str,
        types: Optional[List[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Query memories with auto-injected context.

        Args:
            query: Natural language query
            types: Filter by memory types
            limit: Maximum results
            min_relevance: Minimum relevance score
            **kwargs: Additional parameters

        Returns:
            Recall result with memories list

        Example:
            >>> ctx = MemoryContext(workspace_id="ws_123")
            >>> result = await ctx.recall("programming preferences")
            >>> for memory in result["memories"]:
            ...     print(memory["content"])
        """
        if self._service is None:
            raise RuntimeError("Memory service not configured")

        # Auto-inject context
        return await self._service.recall(
            query=query,
            types=types,
            limit=limit,
            min_relevance=min_relevance,
            workspace_id=self._workspace_id,
            user_id=self._user_id,
            tenant_id=self._tenant_id,
            **kwargs,
        )

    async def reflect(
        self,
        query: str,
        max_tokens: int = 500,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Synthesize memories with auto-injected context.

        Args:
            query: What to reflect on
            max_tokens: Maximum tokens in reflection
            **kwargs: Additional parameters

        Returns:
            Reflection result with synthesized content
        """
        if self._service is None:
            raise RuntimeError("Memory service not configured")

        return await self._service.reflect(
            query=query,
            max_tokens=max_tokens,
            workspace_id=self._workspace_id,
            user_id=self._user_id,
            tenant_id=self._tenant_id,
            **kwargs,
        )

    async def forget(
        self,
        memory_id: str,
        reason: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Delete or decay a memory.

        Args:
            memory_id: Memory to forget
            reason: Optional reason for deletion
            **kwargs: Additional parameters

        Returns:
            Result of forget operation
        """
        if self._service is None:
            raise RuntimeError("Memory service not configured")

        return await self._service.forget(
            memory_id=memory_id,
            reason=reason,
            workspace_id=self._workspace_id,
            user_id=self._user_id,
            tenant_id=self._tenant_id,
            **kwargs,
        )

    async def __aenter__(self) -> "MemoryContext":
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Exit async context manager.

        Could be used for cleanup, flushing buffers, etc.
        """
        # No cleanup needed for now
        pass
