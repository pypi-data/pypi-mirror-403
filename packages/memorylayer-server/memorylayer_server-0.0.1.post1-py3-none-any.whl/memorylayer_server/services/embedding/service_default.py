import hashlib
from logging import Logger

import numpy as np

from pathlib import Path
from typing import Any, Optional, Union, Iterable

from scitrera_app_framework import get_logger, Variables as Variables

from .base import (
    EmbeddingProvider, EmbeddingInput, EmbeddingType,
    MultimodalEmbeddingProvider, ColPaliEmbeddingProvider, MultiVectorEmbedding,
    EmbeddingServicePluginBase, EXT_EMBEDDING_PROVIDER,
)


class EmbeddingService:
    """
    Embedding service that wraps providers and adds caching.

    Supports both single-vector and multi-vector (ColPali) embeddings,
    as well as multimodal content (text + images).
    """

    def __init__(self, provider: EmbeddingProvider, cache: Optional[Any] = None):
        self.provider = provider
        self.cache = cache
        self.logger = get_logger(name=self.__class__.__name__)
        self._is_multimodal = isinstance(provider, MultimodalEmbeddingProvider)
        self._is_multivector = isinstance(provider, ColPaliEmbeddingProvider)
        self.logger.info(
            "Initialized EmbeddingService with provider: %s, dimensions: %s, multimodal: %s",
            provider.__class__.__name__,
            provider.dimensions,
            self._is_multimodal
        )

    @property
    def is_multimodal(self) -> bool:
        """Whether this service supports multimodal (text + image) embeddings."""
        return self._is_multimodal

    @property
    def is_multivector(self) -> bool:
        """Whether this service supports multi-vector embeddings (ColPali)."""
        return self._is_multivector

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with optional caching."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Check cache first
        if self.cache:
            cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
            cached = await self.cache.get_json(cache_key)
            if cached:
                self.logger.debug("Cache hit for embedding: %s", cache_key)
                return cached

        # Generate embedding
        embedding = await self.provider.embed(text)

        # Cache result
        if self.cache:
            await self.cache.set_json(cache_key, embedding, ex=3600)  # 1 hour TTL
            self.logger.debug("Cached embedding: %s", cache_key)

        return embedding

    async def embed_image(self, image: Union[str, bytes, Path]) -> list[float]:
        """
        Generate embedding for an image.

        Requires a multimodal provider (Qwen3-VL, vLLM, or ColPali).
        """
        if not self._is_multimodal:
            raise ValueError(
                f"Provider {self.provider.__class__.__name__} does not support image embeddings. "
                "Use Qwen3VLEmbeddingProvider, VLLMEmbeddingProvider, or ColPaliEmbeddingProvider."
            )

        provider: MultimodalEmbeddingProvider = self.provider
        return await provider.embed_image(image)

    async def embed_multimodal(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """
        Generate embedding for combined text and image.

        Requires a multimodal provider.
        """
        if not self._is_multimodal:
            if image:
                raise ValueError(
                    f"Provider {self.provider.__class__.__name__} does not support image embeddings."
                )
            return await self.embed(text)

        provider: MultimodalEmbeddingProvider = self.provider
        return await provider.embed_multimodal(text, image)

    async def embed_input(self, input: EmbeddingInput) -> list[float]:
        """Generate embedding for EmbeddingInput (convenience method)."""
        if input.embedding_type == EmbeddingType.TEXT:
            return await self.embed(input.text)
        elif self._is_multimodal:
            provider: MultimodalEmbeddingProvider = self.provider
            return await provider.embed_input(input)
        else:
            raise ValueError("Multimodal input requires a multimodal provider")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch (more efficient)."""
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")

        return await self.provider.embed_batch(valid_texts)

    async def embed_multivector(self, text: str) -> MultiVectorEmbedding:
        """
        Generate multi-vector embedding (ColPali only).

        Returns multiple vectors for late interaction retrieval.
        """
        if not self._is_multivector:
            raise ValueError(
                f"Provider {self.provider.__class__.__name__} does not support multi-vector embeddings. "
                "Use ColPaliEmbeddingProvider."
            )

        provider: ColPaliEmbeddingProvider = self.provider
        return await provider.embed_text_multivector(text)

    async def embed_image_multivector(
            self,
            image: Union[str, bytes, Path]
    ) -> MultiVectorEmbedding:
        """
        Generate multi-vector embedding for image (ColPali only).

        Ideal for document/PDF retrieval with visual elements.
        """
        if not self._is_multivector:
            raise ValueError("Multi-vector embeddings require ColPaliEmbeddingProvider")

        provider: ColPaliEmbeddingProvider = self.provider
        return await provider.embed_image_multivector(image)

    @property
    def dimensions(self) -> int:
        return self.provider.dimensions

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            raise ValueError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")

        a_np = np.array(a)
        b_np = np.array(b)

        # Handle zero vectors
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a_np, b_np) / (norm_a * norm_b))

    @staticmethod
    def maxsim_score(
            query_vectors: MultiVectorEmbedding,
            doc_vectors: MultiVectorEmbedding
    ) -> float:
        """
        Calculate MaxSim score for multi-vector embeddings.

        Delegates to ColPaliEmbeddingProvider.maxsim_score.
        """
        return ColPaliEmbeddingProvider.maxsim_score(query_vectors, doc_vectors)


class EmbeddingServicePlugin(EmbeddingServicePluginBase):
    """Default plugin for embedding service."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> object | None:
        cache_service = None  # TODO: cache service should be a plugin with default resolving to None
        embedding_provider: EmbeddingProvider = self.get_extension(EXT_EMBEDDING_PROVIDER, v)
        return EmbeddingService(
            provider=embedding_provider,
            cache=cache_service
        )
