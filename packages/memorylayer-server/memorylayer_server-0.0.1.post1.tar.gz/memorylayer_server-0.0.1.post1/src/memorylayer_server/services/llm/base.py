"""LLM Service - Pluggable LLM provider interface."""
from abc import ABC, abstractmethod
from typing import AsyncIterator

from scitrera_app_framework.api import Plugin, Variables, enabled_option_pattern

from ...config import (
    MEMORYLAYER_LLM_PROVIDER, DEFAULT_MEMORYLAYER_LLM_PROVIDER,
    MEMORYLAYER_LLM_SERVICE, DEFAULT_MEMORYLAYER_LLM_SERVICE,
)
from ...models.llm import LLMRequest, LLMResponse, LLMStreamChunk

EXT_LLM_PROVIDER = 'memorylayer-llm-provider'
EXT_LLM_SERVICE = 'memorylayer-llm-service'


class LLMProvider(ABC):
    """Abstract LLM provider interface.

    Provides low-level access to LLM completions.
    Similar to EmbeddingProvider, this is the actual API client.
    """

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from LLM.

        Args:
            request: LLM request with messages and parameters

        Returns:
            LLM response with content and token counts
        """
        pass

    @abstractmethod
    async def complete_stream(
            self,
            request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming completion.

        Args:
            request: LLM request with stream=True

        Yields:
            LLMStreamChunk for each token/chunk
        """
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model name for this provider."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming."""
        pass


# noinspection PyAbstractClass
class LLMProviderPluginBase(Plugin):
    """Base plugin for LLM providers."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_LLM_PROVIDER}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_LLM_PROVIDER

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(
            self, v,
            MEMORYLAYER_LLM_PROVIDER,
            default=DEFAULT_MEMORYLAYER_LLM_PROVIDER,
            self_attr='PROVIDER_NAME'
        )


# noinspection PyAbstractClass
class LLMServicePluginBase(Plugin):
    """Base plugin for LLM service."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_LLM_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_LLM_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(
            self, v,
            MEMORYLAYER_LLM_SERVICE,
            default=DEFAULT_MEMORYLAYER_LLM_SERVICE,
            self_attr='PROVIDER_NAME'
        )

    def get_dependencies(self, v: Variables):
        return (EXT_LLM_PROVIDER,)
