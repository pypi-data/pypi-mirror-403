"""
Reflect Service - Memory synthesis and summarization.

Uses LLM to:
- Synthesize multiple memories into coherent summary
- Generate category summaries
- Answer complex queries requiring reasoning
"""
from datetime import datetime, timezone
from logging import Logger
from typing import Optional, Any

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import ReflectServicePluginBase
from ..storage import StorageBackend, EXT_STORAGE
from ..memory import MemoryService, EXT_MEMORY_SERVICE
from ..llm import LLMService, EXT_LLM_SERVICE, LLMNotConfiguredError
from ...models import ReflectInput, ReflectResult, RecallInput, RecallMode


class ReflectService:
    """Service for LLM-powered memory synthesis."""

    def __init__(
            self,
            storage: StorageBackend,
            memory_service: MemoryService,
            llm_service: Optional[LLMService] = None,
    ):
        self.storage = storage
        self.memory_service = memory_service
        self.llm = llm_service
        self.logger = get_logger(name=self.__class__.__name__)
        if llm_service:
            self.logger.info("Initialized ReflectService with LLM service (model: %s)", llm_service.default_model)
        else:
            self.logger.info("Initialized ReflectService without LLM service")

    async def reflect(
            self,
            workspace_id: str,
            input: ReflectInput,
    ) -> ReflectResult:
        """
        Synthesize memories matching query into coherent reflection.

        Steps:
        1. Recall relevant memories
        2. Gather associated memories (depth=input.depth)
        3. Send to LLM with synthesis prompt
        4. Return reflection with source references
        """
        self.logger.info(
            "Generating reflection in workspace: %s, query: %s",
            workspace_id,
            input.query[:50]
        )

        start_time = datetime.now(timezone.utc)

        # 1. Recall relevant memories
        recall_input = RecallInput(
            query=input.query,
            types=input.types,
            subtypes=input.subtypes,
            tags=input.tags,
            space_id=input.space_id,
            user_id=input.user_id,
            mode=RecallMode.LLM,  # Use LLM mode for best semantic matching
            limit=20,  # Get more memories for synthesis
            min_relevance=0.5,
            include_associations=True,
            traverse_depth=input.depth,
        )

        recall_result = await self.memory_service.recall(
            workspace_id=workspace_id,
            input=recall_input
        )

        if not recall_result.memories:
            self.logger.warning("No memories found for reflection query: %s", input.query)
            return ReflectResult(
                reflection="No relevant memories found to reflect upon.",
                source_memories=[],
                confidence=0.0,
                tokens_processed=0
            )

        self.logger.debug("Found %s memories for reflection", len(recall_result.memories))

        # 2. Gather associated memories (already handled by traverse_depth in recall)
        source_memory_ids = [m.id for m in recall_result.memories]

        # 3. Synthesize with LLM
        if self.llm:
            reflection, tokens_used = await self._synthesize_with_llm(
                memories=recall_result.memories,
                query=input.query,
                max_tokens=input.max_tokens
            )
            confidence = self._calculate_confidence(recall_result.memories)
        else:
            # Fallback: Simple concatenation if no LLM available
            self.logger.warning("No LLM client available, using simple synthesis")
            reflection, tokens_used, confidence = self._simple_synthesis(
                memories=recall_result.memories,
                query=input.query,
                max_tokens=input.max_tokens
            )

        latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        self.logger.info(
            "Generated reflection in %s ms, %s tokens, confidence: %.2f",
            latency_ms,
            tokens_used,
            confidence
        )

        result = ReflectResult(
            reflection=reflection,
            source_memories=source_memory_ids if input.include_sources else [],
            confidence=confidence,
            tokens_processed=tokens_used
        )

        return result

    async def _synthesize_with_llm(
            self,
            memories: list,
            query: str,
            max_tokens: int
    ) -> tuple[str, int]:
        """
        Use LLM to synthesize memories into coherent reflection.

        In production, this would call OpenAI/Anthropic API.
        """
        self.logger.debug("Synthesizing %s memories with LLM", len(memories))

        # Build context from memories
        context_parts = []
        for i, memory in enumerate(memories, 1):
            context_parts.append(
                f"[{i}] {memory.type.value.upper()} - {memory.content}"
            )

        context = "\n\n".join(context_parts)

        # Build synthesis prompt
        prompt = f"""Based on the following memories, provide a synthesized reflection on: "{query}"

Memories:
{context}

Synthesize these memories into a coherent, insightful reflection that directly addresses the query. Focus on patterns, relationships, and key insights. Be concise but comprehensive.

Reflection:"""

        # In production, call actual LLM API
        # For now, return a placeholder
        if self.llm:
            try:
                # Placeholder - replace with actual LLM call
                reflection = await self._call_llm(prompt, max_tokens)
                tokens_used = len(prompt.split()) + len(reflection.split())  # Rough estimate

                return reflection, tokens_used
            except Exception as e:
                self.logger.error("LLM synthesis failed: %s", e)
                # Fall back to simple synthesis
                return self._simple_synthesis(memories, query, max_tokens)
        else:
            return self._simple_synthesis(memories, query, max_tokens)

    async def _call_llm(self, prompt: str, max_tokens: int) -> str:
        """Call LLM API using the configured LLM service."""
        if not self.llm:
            self.logger.warning("No LLM service available, using fallback")
            return "Memory synthesis requires LLM integration. Please configure an LLM provider."

        try:
            result = await self.llm.synthesize(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return result
        except LLMNotConfiguredError:
            self.logger.warning("LLM provider not configured, using fallback")
            return "Memory synthesis requires LLM integration. Please configure an LLM provider (set MEMORYLAYER_LLM_PROVIDER=openai)."
        except Exception as e:
            self.logger.error("LLM call failed: %s", e)
            return f"LLM synthesis failed: {e}"

    def _simple_synthesis(
            self,
            memories: list,
            query: str,
            max_tokens: int
    ) -> tuple[str, int, float]:
        """
        Simple synthesis without LLM.

        Returns: (reflection, tokens_used, confidence)
        """
        self.logger.debug("Using simple synthesis for %s memories", len(memories))

        # Group by type
        by_type = {}
        for memory in memories:
            type_name = memory.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(memory)

        # Build reflection
        parts = [f"Reflection on: {query}\n"]

        for type_name, type_memories in by_type.items():
            parts.append(f"\n{type_name.upper()} memories ({len(type_memories)}):")
            for memory in type_memories[:5]:  # Limit to 5 per type
                parts.append(f"- {memory.content[:200]}...")  # Truncate

        reflection = "\n".join(parts)

        # Truncate to max_tokens (rough estimate: 1 token ~= 4 chars)
        max_chars = max_tokens * 4
        if len(reflection) > max_chars:
            reflection = reflection[:max_chars] + "..."

        tokens_used = len(reflection.split())
        confidence = min(1.0, len(memories) / 10.0)  # Simple confidence based on memory count

        return reflection, tokens_used, confidence

    def _calculate_confidence(self, memories: list) -> float:
        """
        Calculate confidence score based on memory quality.

        Factors:
        - Number of memories found
        - Average importance
        - Recency
        """
        if not memories:
            return 0.0

        # Number of memories (more is better, up to a point)
        count_factor = min(1.0, len(memories) / 10.0)

        # Average importance
        avg_importance = sum(m.importance for m in memories) / len(memories)

        # Recency factor (memories accessed recently are more relevant)
        recency_factor = 0.0
        if memories[0].last_accessed_at:
            # Simple heuristic - if recently accessed, boost confidence
            recency_factor = 0.2

        confidence = (count_factor * 0.5) + (avg_importance * 0.4) + recency_factor

        return min(1.0, confidence)

    async def summarize_category(
            self,
            workspace_id: str,
            category_name: str,
    ) -> str:
        """
        Generate or update category summary from constituent memories.

        This creates a high-level overview of all memories in a category.
        """
        self.logger.info("Generating summary for category: %s", category_name)

        # Get or create category
        category = await self.storage.get_or_create_category(workspace_id, category_name)

        # Recall all memories with this category as tag
        recall_input = RecallInput(
            query=category_name,
            tags=[category_name.lower()],
            mode=RecallMode.RAG,
            limit=100,  # Get many memories for comprehensive summary
            min_relevance=0.3,  # Lower threshold for category members
        )

        recall_result = await self.memory_service.recall(
            workspace_id=workspace_id,
            input=recall_input
        )

        if not recall_result.memories:
            summary = f"No memories found in category: {category_name}"
            self.logger.warning(summary)
            return summary

        # Generate summary
        if self.llm:
            summary = await self._generate_category_summary_with_llm(
                category_name=category_name,
                memories=recall_result.memories
            )
        else:
            summary = self._generate_category_summary_simple(
                category_name=category_name,
                memories=recall_result.memories
            )

        # Update category in storage
        await self.storage.update_category_summary(
            workspace_id=workspace_id,
            category_id=category.id,
            summary=summary,
            item_ids=[m.id for m in recall_result.memories]
        )

        self.logger.info("Generated category summary: %s chars", len(summary))
        return summary

    async def _generate_category_summary_with_llm(
            self,
            category_name: str,
            memories: list
    ) -> str:
        """Generate category summary using LLM."""
        # Build context
        context_parts = []
        for memory in memories[:50]:  # Limit to avoid token overflow
            context_parts.append(f"- {memory.content[:100]}")

        context = "\n".join(context_parts)

        prompt = f"""Summarize the following memories from the "{category_name}" category. Provide a concise overview of the key themes, patterns, and insights.

Memories:
{context}

Summary:"""

        # Call LLM
        summary = await self._call_llm(prompt, max_tokens=300)
        return summary

    def _generate_category_summary_simple(
            self,
            category_name: str,
            memories: list
    ) -> str:
        """Generate category summary without LLM."""
        # Count by type and subtype
        type_counts = {}
        subtype_counts = {}

        for memory in memories:
            type_name = memory.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            if memory.subtype:
                subtype_name = memory.subtype.value
                subtype_counts[subtype_name] = subtype_counts.get(subtype_name, 0) + 1

        # Build summary
        summary_parts = [
            f"Category: {category_name}",
            f"Total memories: {len(memories)}",
            "",
            "Memory types:"
        ]

        for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"- {type_name}: {count}")

        if subtype_counts:
            summary_parts.append("")
            summary_parts.append("Memory subtypes:")
            for subtype_name, count in sorted(subtype_counts.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"- {subtype_name}: {count}")

        # Add sample memories
        summary_parts.append("")
        summary_parts.append("Sample memories:")
        for memory in memories[:3]:
            summary_parts.append(f"- {memory.content[:100]}...")

        return "\n".join(summary_parts)

    async def answer_question(
            self,
            workspace_id: str,
            question: str,
            context_memories: Optional[list[str]] = None,
    ) -> ReflectResult:
        """
        Answer a question using memories as knowledge base.

        If context_memories provided, use those; otherwise, recall relevant memories.
        """
        self.logger.info("Answering question: %s", question[:50])

        # Use provided context or recall memories
        if context_memories:
            memories = []
            for memory_id in context_memories:
                memory = await self.storage.get_memory(workspace_id, memory_id)
                if memory:
                    memories.append(memory)
        else:
            # Recall relevant memories
            recall_input = RecallInput(
                query=question,
                mode=RecallMode.LLM,
                limit=10,
                min_relevance=0.6,
            )
            recall_result = await self.memory_service.recall(workspace_id, recall_input)
            memories = recall_result.memories

        if not memories:
            return ReflectResult(
                reflection="I don't have enough information to answer this question.",
                source_memories=[],
                confidence=0.0,
                tokens_processed=0
            )

        # Generate answer using reflection
        reflect_input = ReflectInput(
            query=question,
            max_tokens=500,
            include_sources=True,
            depth=1
        )

        result = await self.reflect(workspace_id, reflect_input)
        return result


class DefaultReflectServicePlugin(ReflectServicePluginBase):
    """Default reflect service plugin."""
    PROVIDER_NAME = 'default'

    def get_dependencies(self, v: Variables):
        return (EXT_STORAGE, EXT_MEMORY_SERVICE, EXT_LLM_SERVICE)

    def initialize(self, v: Variables, logger: Logger) -> ReflectService:
        storage: StorageBackend = self.get_extension(EXT_STORAGE, v)
        memory: MemoryService = self.get_extension(EXT_MEMORY_SERVICE, v)
        llm_service: LLMService = self.get_extension(EXT_LLM_SERVICE, v)
        return ReflectService(
            storage=storage,
            memory_service=memory,
            llm_service=llm_service,
        )
