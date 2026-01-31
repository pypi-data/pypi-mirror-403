import hashlib

from logging import Logger

from scitrera_app_framework import Variables as Variables

from ...config import EmbeddingProviderType, MEMORYLAYER_EMBEDDING_DIMENSIONS

from .base import EmbeddingProvider, EmbeddingProviderPluginBase

DEFAULT_EMBEDDING_DIMENSIONS = 384


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Simple mock embedding provider for testing without heavy ML dependencies.

    Generates deterministic embeddings based on content hash.
    Not suitable for production - use for testing only.
    """

    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS):
        super().__init__(dimensions)
        self.logger.info("Initialized MockEmbeddingProvider with dimensions=%d", dimensions)

    async def embed(self, text: str) -> list[float]:
        """Generate deterministic embedding based on text hash."""

        # Create a deterministic embedding from text hash
        text_hash = hashlib.sha256(text.encode()).digest()

        # Generate embedding from hash bytes
        embedding = []
        for i in range(self._dimensions):
            byte_idx = i % len(text_hash)
            # Normalize to [-1, 1] range
            value = (text_hash[byte_idx] - 128) / 128.0
            embedding.append(value)

        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch."""
        return [await self.embed(text) for text in texts]


class MockEmbeddingProviderPlugin(EmbeddingProviderPluginBase):
    PROVIDER_NAME = EmbeddingProviderType.MOCK

    def initialize(self, v: Variables, logger: Logger) -> MockEmbeddingProvider:
        return MockEmbeddingProvider(
            dimensions=v.environ(MEMORYLAYER_EMBEDDING_DIMENSIONS, default=DEFAULT_EMBEDDING_DIMENSIONS, type_fn=int)
        )
