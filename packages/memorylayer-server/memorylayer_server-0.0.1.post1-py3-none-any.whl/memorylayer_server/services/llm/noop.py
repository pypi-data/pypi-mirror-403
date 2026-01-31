"""No-op LLM provider - raises NotConfigured (OSS default)."""
from logging import Logger
from typing import AsyncIterator

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import (
    LLMProvider, LLMProviderPluginBase
)
from ...models.llm import LLMRequest, LLMResponse, LLMStreamChunk


class LLMNotConfiguredError(Exception):
    """Raised when LLM is used but not configured."""
    pass


class NoOpLLMProvider(LLMProvider):
    """Default LLM provider that raises when called.

    OSS default - LLM features require explicit configuration.
    Set MEMORYLAYER_LLM_PROVIDER=openai and provide API key to enable.
    """

    def __init__(self):
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info(
            "Initialized NoOpLLMProvider - LLM calls will raise NotConfigured. "
            "Set MEMORYLAYER_LLM_PROVIDER=openai to enable LLM features."
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise LLMNotConfiguredError(
            "LLM provider not configured. Set MEMORYLAYER_LLM_PROVIDER=openai "
            "and provide MEMORYLAYER_LLM_OPENAI_API_KEY to enable LLM features."
        )

    async def complete_stream(
        self,
        request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        raise LLMNotConfiguredError("LLM provider not configured.")
        # Yield is needed for type hints even though we raise
        yield  # pragma: no cover

    @property
    def default_model(self) -> str:
        return "not-configured"

    @property
    def supports_streaming(self) -> bool:
        return False


class NoOpLLMProviderPlugin(LLMProviderPluginBase):
    """Plugin for no-op LLM provider."""
    PROVIDER_NAME = 'noop'

    def initialize(self, v: Variables, logger: Logger) -> LLMProvider:
        return NoOpLLMProvider()


