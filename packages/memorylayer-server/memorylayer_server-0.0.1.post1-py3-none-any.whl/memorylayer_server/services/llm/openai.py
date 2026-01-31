"""OpenAI-compatible LLM provider."""
from logging import Logger
from typing import AsyncIterator, Optional

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import (
    LLMProvider, LLMProviderPluginBase
)
from ...models.llm import LLMRequest, LLMResponse, LLMStreamChunk
from ...config import (
    MEMORYLAYER_LLM_OPENAI_API_KEY,
    MEMORYLAYER_LLM_OPENAI_BASE_URL,
    DEFAULT_LLM_OPENAI_BASE_URL,
    MEMORYLAYER_LLM_OPENAI_MODEL,
    DEFAULT_LLM_OPENAI_MODEL,
)


class OpenAILLMProvider(LLMProvider):
    """OpenAI-compatible LLM provider.

    Works with OpenAI API, Azure OpenAI, Ollama, vLLM, and any
    OpenAI-compatible endpoint by configuring the base URL.
    """

    def __init__(
            self,
            api_key: str,
            base_url: str = DEFAULT_LLM_OPENAI_BASE_URL,
            model: str = DEFAULT_LLM_OPENAI_MODEL,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info(
            "Initialized OpenAILLMProvider: base_url=%s, model=%s",
            base_url, model
        )

    def _get_client(self):
        """Lazy-load OpenAI async client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using OpenAI API."""
        client = self._get_client()

        messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in request.messages
        ]

        model = request.model or self.model

        self.logger.debug("LLM request: model=%s, messages=%d", model, len(messages))

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            finish_reason=choice.finish_reason or "stop",
        )

    async def complete_stream(
            self,
            request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming completion using OpenAI API."""
        client = self._get_client()

        messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in request.messages
        ]

        model = request.model or self.model

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.delta

                if delta.content:
                    yield LLMStreamChunk(
                        content=delta.content,
                        is_final=False,
                    )

                if choice.finish_reason:
                    yield LLMStreamChunk(
                        content="",
                        is_final=True,
                        finish_reason=choice.finish_reason,
                    )

    @property
    def default_model(self) -> str:
        return self.model

    @property
    def supports_streaming(self) -> bool:
        return True


class OpenAILLMProviderPlugin(LLMProviderPluginBase):
    """Plugin for OpenAI LLM provider."""
    PROVIDER_NAME = 'openai'

    def initialize(self, v: Variables, logger: Logger) -> LLMProvider:
        api_key = v.environ(MEMORYLAYER_LLM_OPENAI_API_KEY, default=None)
        return OpenAILLMProvider(
            api_key=api_key,
            base_url=v.environ(MEMORYLAYER_LLM_OPENAI_BASE_URL, default=DEFAULT_LLM_OPENAI_BASE_URL),
            model=v.environ(MEMORYLAYER_LLM_OPENAI_MODEL, default=DEFAULT_LLM_OPENAI_MODEL),
        )
