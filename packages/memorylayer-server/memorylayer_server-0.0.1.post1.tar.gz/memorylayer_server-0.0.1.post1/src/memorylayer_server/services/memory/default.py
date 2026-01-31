"""
Memory Service - Core business logic for memory operations.

Operations:
- remember: Store new memory with automatic embedding and classification
- recall: Query memories with vector search and optional LLM enhancement
- forget: Soft or hard delete memories
- decay: Reduce memory importance over time
- get: Retrieve single memory by ID
"""
import hashlib
from datetime import datetime, timezone
from logging import Logger
from typing import Optional, Any
from uuid import uuid4

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from ...models import RememberInput, Memory, RecallInput, RecallResult, RecallMode, MemoryType, SearchTolerance

from ..storage import StorageBackend, EXT_STORAGE
from ..embedding import EmbeddingService, EXT_EMBEDDING_SERVICE

from .base import MemoryServicePluginBase


class MemoryService:
    """
    Core memory service implementing remember/recall/forget operations.

    This service coordinates between:
    - Storage backend (PostgreSQL or SQLite)
    - Embedding service (for vector generation)
    - Cache (for recent memories)
    """

    def __init__(
            self,
            storage: StorageBackend,
            embedding_service: EmbeddingService,
            cache: Optional[Any] = None
    ):
        self.storage = storage
        self.embedding = embedding_service
        self.cache = cache
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info("Initialized MemoryService")

    async def remember(
            self,
            workspace_id: str,
            input: RememberInput,
            user_id: Optional[str] = None,
    ) -> Memory:
        """
        Store a new memory.

        Steps:
        1. Generate content hash for deduplication
        2. Check for duplicates (return existing if found)
        3. Generate embedding
        4. Classify memory type if not provided
        5. Store in backend
        6. Create auto-associations with similar memories
        """
        self.logger.info(
            "Storing memory in workspace: %s, type: %s, content length: %s",
            workspace_id,
            input.type,
            len(input.content)
        )

        # 1. Generate content hash
        content_hash = self._generate_content_hash(input.content)

        # 2. Check for duplicates (search by hash)
        existing = await self.storage.get_memory_by_hash(workspace_id, content_hash)
        if existing:
            self.logger.info("Found duplicate memory: %s", existing.id)
            return existing

        # 3. Generate embedding
        start_time = datetime.now(timezone.utc)
        embedding = await self.embedding.embed(input.content)
        self.logger.debug(
            "Generated embedding in %s ms",
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )

        # 4. Classify memory type if not provided
        memory_type = input.type
        if memory_type is None:
            memory_type = await self._classify_memory_type(input.content)
            self.logger.debug("Auto-classified memory type: %s", memory_type)

        # 5. Create memory object with generated fields
        memory_id = self._generate_id("mem")
        memory_data = RememberInput(
            content=input.content,
            type=memory_type,
            subtype=input.subtype,
            importance=input.importance,
            tags=input.tags,
            metadata=input.metadata,
            associations=input.associations,
            space_id=input.space_id,
            user_id=user_id or input.user_id,
        )

        # Store in backend (backend will create Memory object)
        memory = await self.storage.create_memory(workspace_id, memory_data)

        # Update with embedding (if backend doesn't handle it)
        if memory.embedding is None:
            memory = await self.storage.update_memory(
                workspace_id,
                memory.id,
                embedding=embedding
            )

        self.logger.info("Stored memory: %s", memory.id)

        # 6. Create auto-associations with similar memories
        # Search for similar memories
        similar_memories = await self.storage.search_memories(
            workspace_id=workspace_id,
            query_embedding=embedding,
            limit=5,
            min_relevance=0.85,  # High threshold for auto-association
        )

        # Auto-associate if similar memories found
        if similar_memories:
            from memorylayer_server.services.association import AssociationService
            assoc_service = AssociationService(self.storage)

            for similar_memory, score in similar_memories:
                if similar_memory.id != memory.id:  # Don't self-associate
                    try:
                        await assoc_service.auto_associate(
                            workspace_id=workspace_id,
                            new_memory_id=memory.id,
                            similar_memories=[(similar_memory.id, score)],
                            threshold=0.85
                        )
                    except Exception as e:
                        self.logger.warning(
                            "Failed to auto-associate %s with %s: %s",
                            memory.id,
                            similar_memory.id,
                            e
                        )

        return memory

    async def recall(
            self,
            workspace_id: str,
            input: RecallInput,
            user_id: Optional[str] = None,
    ) -> RecallResult:
        """
        Query memories using vector similarity and optional filters.

        Modes:
        - RAG: Pure vector similarity (fast, ~30ms)
        - LLM: Query rewriting + tiered search (accurate, ~500ms)
        - HYBRID: RAG first, LLM if insufficient (balanced)
        """
        self.logger.info(
            "Recalling memories in workspace: %s, mode: %s, query: %s",
            workspace_id,
            input.mode,
            input.query[:50]
        )

        start_time = datetime.now(timezone.utc)

        # Determine effective tolerance threshold
        relevance_threshold = self._get_relevance_threshold(input.tolerance, input.min_relevance)

        # RAG mode: Pure vector similarity
        if input.mode == RecallMode.RAG:
            result = await self._recall_rag(
                workspace_id=workspace_id,
                input=input,
                relevance_threshold=relevance_threshold,
            )
            result.mode_used = RecallMode.RAG

        # LLM mode: Query rewriting + enhanced search
        elif input.mode == RecallMode.LLM:
            result = await self._recall_llm(
                workspace_id=workspace_id,
                input=input,
                relevance_threshold=relevance_threshold,
            )
            result.mode_used = RecallMode.LLM

        # HYBRID mode: Try RAG first, fall back to LLM if insufficient
        else:
            result = await self._recall_rag(
                workspace_id=workspace_id,
                input=input,
                relevance_threshold=relevance_threshold,
            )

            # Check if RAG results are sufficient
            if not result.memories or (result.memories and result.memories[0].importance < input.rag_threshold):
                self.logger.debug("RAG insufficient, trying LLM mode")
                result = await self._recall_llm(
                    workspace_id=workspace_id,
                    input=input,
                    relevance_threshold=relevance_threshold,
                )
                result.mode_used = RecallMode.LLM
            else:
                result.mode_used = RecallMode.RAG

        # Calculate latency
        latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        result.search_latency_ms = latency_ms

        self.logger.info(
            "Recalled %s memories in %s ms using %s mode",
            len(result.memories),
            latency_ms,
            result.mode_used
        )

        # Increment access counts
        for memory in result.memories:
            await self.increment_access(workspace_id, memory.id)

        return result

    async def _recall_rag(
            self,
            workspace_id: str,
            input: RecallInput,
            relevance_threshold: float,
    ) -> RecallResult:
        """Pure vector similarity search."""
        # Generate query embedding
        query_embedding = await self.embedding.embed(input.query)

        # Search memories
        results = await self.storage.search_memories(
            workspace_id=workspace_id,
            query_embedding=query_embedding,
            limit=input.limit,
            min_relevance=relevance_threshold,
            types=[t.value for t in input.types] if input.types else None,
            subtypes=[s.value for s in input.subtypes] if input.subtypes else None,
            tags=input.tags if input.tags else None,
        )

        # Extract memories (ignore scores for now)
        memories = [memory for memory, score in results]

        return RecallResult(
            memories=memories,
            total_count=len(memories),
            query_tokens=0,
            search_latency_ms=0,  # Will be set by caller
            mode_used=RecallMode.RAG,
        )

    async def _recall_llm(
            self,
            workspace_id: str,
            input: RecallInput,
            relevance_threshold: float,
    ) -> RecallResult:
        """
        LLM-enhanced retrieval with query rewriting.

        In production, this would:
        1. Use LLM to rewrite query for better semantic match
        2. Perform tiered search (exact -> semantic -> exploratory)
        3. Re-rank results using LLM

        For now, falls back to RAG with more lenient threshold.
        """
        self.logger.warning("LLM mode not fully implemented, using enhanced RAG")

        # TODO: Implement actual LLM query rewriting
        # For now, just use RAG with lower threshold
        result = await self._recall_rag(
            workspace_id=workspace_id,
            input=input,
            relevance_threshold=max(0.3, relevance_threshold - 0.2),  # More lenient
        )

        result.query_rewritten = input.query  # Would be rewritten in full implementation
        result.sufficiency_reached = len(result.memories) >= input.limit

        return result

    async def forget(
            self,
            workspace_id: str,
            memory_id: str,
            hard: bool = False,
            reason: Optional[str] = None,
    ) -> bool:
        """
        Delete or soft-delete a memory.

        Soft delete: Sets deleted_at timestamp
        Hard delete: Removes from database entirely
        """
        self.logger.info(
            "Forgetting memory: %s in workspace: %s, hard: %s",
            memory_id,
            workspace_id,
            hard
        )

        success = await self.storage.delete_memory(
            workspace_id=workspace_id,
            memory_id=memory_id,
            hard=hard
        )

        if success:
            self.logger.info("Memory forgotten: %s", memory_id)
        else:
            self.logger.warning("Failed to forget memory: %s", memory_id)

        return success

    async def decay(
            self,
            workspace_id: str,
            memory_id: str,
            decay_rate: float = 0.1,
    ) -> Optional[Memory]:
        """
        Reduce memory importance by decay_rate.

        Used for implementing memory decay over time.
        """
        self.logger.debug(
            "Decaying memory: %s by rate: %s",
            memory_id,
            decay_rate
        )

        # Get current memory
        memory = await self.storage.get_memory(workspace_id, memory_id)
        if not memory:
            self.logger.warning("Memory not found for decay: %s", memory_id)
            return None

        # Calculate new importance (apply decay directly)
        new_importance = max(0.0, memory.importance - decay_rate)

        # Update memory
        updated = await self.storage.update_memory(
            workspace_id=workspace_id,
            memory_id=memory_id,
            importance=new_importance
        )

        self.logger.debug(
            "Decayed memory: %s, new importance: %s",
            memory_id,
            new_importance
        )

        return updated

    async def get(
            self,
            workspace_id: str,
            memory_id: str,
    ) -> Optional[Memory]:
        """Get a single memory by ID."""
        self.logger.debug("Getting memory: %s", memory_id)
        return await self.storage.get_memory(workspace_id, memory_id)

    async def increment_access(
            self,
            workspace_id: str,
            memory_id: str,
    ) -> None:
        """Increment access count and update last_accessed_at."""
        try:
            memory = await self.storage.get_memory(workspace_id, memory_id)
            if memory:
                await self.storage.update_memory(
                    workspace_id=workspace_id,
                    memory_id=memory_id,
                    access_count=memory.access_count + 1,
                    last_accessed_at=datetime.now(timezone.utc)
                )
        except Exception as e:
            self.logger.warning("Failed to increment access for %s: %s", memory_id, e)

    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_id(self, prefix: str = "mem") -> str:
        """Generate unique memory ID."""
        return f"{prefix}_{uuid4().hex[:12]}"

    async def _classify_memory_type(self, content: str) -> MemoryType:
        """
        Auto-classify memory type based on content.

        Simple heuristic-based classification.
        In production, could use LLM for more accurate classification.
        """
        content_lower = content.lower()

        # Procedural: How-to, steps, instructions
        if any(keyword in content_lower for keyword in [
            "how to", "steps", "procedure", "process", "method", "workflow"
        ]):
            return MemoryType.PROCEDURAL

        # Episodic: Time-based, events, specific instances
        if any(keyword in content_lower for keyword in [
            "when", "yesterday", "today", "occurred", "happened", "at that time"
        ]):
            return MemoryType.EPISODIC

        # Working: Current context, temporary
        if any(keyword in content_lower for keyword in [
            "currently", "working on", "in progress", "now", "right now"
        ]):
            return MemoryType.WORKING

        # Default to semantic (facts, concepts)
        return MemoryType.SEMANTIC

    def _get_relevance_threshold(
            self,
            tolerance: SearchTolerance,
            min_relevance: float
    ) -> float:
        """
        Calculate effective relevance threshold based on tolerance setting.

        If min_relevance is explicitly set to <= 0.0, respect it (useful for testing).
        Otherwise, apply tolerance-based minimums.
        """
        # If explicitly set to 0.0 or negative, return it (testing mode allows all results)
        if min_relevance <= 0.0:
            return min_relevance

        # Base threshold from input
        threshold = min_relevance

        # Adjust based on tolerance
        if tolerance == SearchTolerance.STRICT:
            threshold = max(threshold, 0.8)
        elif tolerance == SearchTolerance.MODERATE:
            threshold = max(threshold, 0.6)
        elif tolerance == SearchTolerance.LOOSE:
            threshold = max(threshold, 0.4)

        return threshold


class DefaultMemoryServicePlugin(MemoryServicePluginBase):
    """Default memory service plugin."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> MemoryService:
        cache = None  # TODO: cache service should be a plugin with default resolving to None
        storage: StorageBackend = self.get_extension(EXT_STORAGE, v)
        embedding: EmbeddingService = self.get_extension(EXT_EMBEDDING_SERVICE, v)
        return MemoryService(
            storage=storage,
            embedding_service=embedding,
            cache=cache
        )
