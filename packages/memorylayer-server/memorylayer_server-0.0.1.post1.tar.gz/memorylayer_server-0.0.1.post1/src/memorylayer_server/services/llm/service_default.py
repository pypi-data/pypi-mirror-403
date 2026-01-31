from logging import Logger
from typing import AsyncIterator, Optional, List

from scitrera_app_framework import get_logger, Variables

from ...models.llm import LLMRequest, LLMResponse, LLMStreamChunk, LLMMessage, LLMRole
from .base import LLMProvider, EXT_LLM_PROVIDER, LLMServicePluginBase


class LLMService:
    """High-level LLM service wrapping provider.

    Similar to EmbeddingService wrapping EmbeddingProvider.
    Adds convenience methods for common patterns like synthesis.
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.logger = get_logger(name=self.__class__.__name__)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Pass-through to provider complete."""
        return await self.provider.complete(request)

    async def complete_stream(
            self,
            request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Pass-through to provider complete_stream."""
        async for chunk in self.provider.complete_stream(request):
            yield chunk

    async def synthesize(
            self,
            prompt: str,
            context: Optional[str] = None,
            max_tokens: int = 500,
            temperature: float = 0.7,
    ) -> str:
        """Simple synthesis - prompt with optional context.

        Args:
            prompt: User prompt/question
            context: Optional context to include
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        messages = []

        if context:
            messages.append(LLMMessage(
                role=LLMRole.SYSTEM,
                content=f"Use this context to inform your response:\n\n{context}"
            ))

        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        request = LLMRequest(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response = await self.provider.complete(request)
        return response.content

    async def answer_question(
            self,
            question: str,
            memories: List[str],
            max_tokens: int = 500,
    ) -> str:
        """Answer question using memories as context.

        Args:
            question: User question
            memories: List of memory contents
            max_tokens: Maximum response tokens

        Returns:
            Generated answer
        """
        context = "\n\n".join([f"- {m}" for m in memories])

        system_prompt = f"""You are a helpful assistant with access to the user's memories.
Answer questions based on the provided memories. If the memories don't contain
relevant information, say so.

Memories:
{context}"""

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
            LLMMessage(role=LLMRole.USER, content=question),
        ]

        request = LLMRequest(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.5,  # Lower temp for factual answers
        )

        response = await self.provider.complete(request)
        return response.content

    @property
    def default_model(self) -> str:
        """Default model from provider."""
        return self.provider.default_model

    @property
    def supports_streaming(self) -> bool:
        """Streaming support from provider."""
        return self.provider.supports_streaming


class DefaultLLMServicePlugin(LLMServicePluginBase):
    """Plugin for default LLM service."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> LLMService:
        provider: LLMProvider = self.get_extension(EXT_LLM_PROVIDER, v)
        return LLMService(provider=provider)
