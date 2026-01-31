from logging import Logger
from pathlib import Path
from typing import Optional, Any, Union

from scitrera_app_framework import Variables as Variables

from ...config import EmbeddingProviderType, MEMORYLAYER_EMBEDDING_MODEL, MEMORYLAYER_EMBEDDING_DIMENSIONS

from .base import MultimodalEmbeddingProvider, EmbeddingProviderPluginBase

MEMORYLAYER_EMBEDDING_VLLM_DTYPE = 'MEMORYLAYER_EMBEDDING_VLLM_DTYPE'
MEMORYLAYER_EMBEDDING_VLLM_MAX_LENGTH = 'MEMORYLAYER_EMBEDDING_VLLM_MAX_LENGTH'

DEFAULT_EMBEDDING_MODEL = 'Qwen/Qwen3-VL-Embedding-2B'
DEFAULT_EMBEDDING_DIMENSIONS = 2048
DEFAULT_DTYPE = 'bfloat16'
DEFAULT_MAX_LENGTH = 32768


class VLLMEmbeddingProvider(MultimodalEmbeddingProvider):
    """
    vLLM-based embedding provider for high-performance inference.

    Uses vLLM's pooling runner for efficient embedding generation.
    Supports any model compatible with vLLM's embedding mode.

    Features:
    - High throughput with batching
    - GPU optimized
    - Supports multimodal models
    """

    def __init__(
            self,
            model_name: str = "Qwen/Qwen3-VL-Embedding-2B",
            dtype: str = "bfloat16",
            max_model_len: int = 32768,
            output_dimensions: int = 2048,
    ):
        super().__init__(output_dimensions=output_dimensions)
        self.model_name = model_name
        self.dtype = dtype
        self.max_model_len = max_model_len
        self.output_dimensions = output_dimensions
        self._model = None
        self._dimensions = output_dimensions
        self.logger.info(
            "Initialized VLLMEmbeddingProvider with model: %s, dtype: %s",
            model_name,
            dtype
        )

    def _get_model(self):
        """Lazy load the vLLM model."""
        if self._model is None:
            from vllm import LLM

            self.logger.info("Loading vLLM model: %s", self.model_name)

            self._model = LLM(
                model=self.model_name,
                task="embed",
                dtype=self.dtype,
                max_model_len=self.max_model_len,
                trust_remote_code=True,
            )

            self.logger.info("vLLM model loaded successfully")

        return self._model

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text using vLLM."""
        self.logger.debug("Generating vLLM embedding for text: %s chars", len(text))

        model = self._get_model()
        outputs = model.embed([text])
        embedding = outputs[0].outputs.embedding

        # Truncate if needed
        if len(embedding) > self.output_dimensions:
            embedding = embedding[:self.output_dimensions]

        return list(embedding)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch using vLLM (highly efficient)."""
        self.logger.debug("Generating vLLM embeddings for batch of %s texts", len(texts))

        model = self._get_model()
        outputs = model.embed(texts)

        results = []
        for output in outputs:
            embedding = output.outputs.embedding
            if len(embedding) > self.output_dimensions:
                embedding = embedding[:self.output_dimensions]
            results.append(list(embedding))

        return results

    async def embed_image(self, image: Union[str, bytes, Path]) -> list[float]:
        """Generate embedding for image using vLLM."""
        self.logger.debug("Generating vLLM embedding for image")

        # vLLM requires specific multimodal input format
        # This depends on the model's expected format
        model = self._get_model()

        # Load image
        from PIL import Image
        import io

        image_bytes = self.load_image_bytes(image)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Create multimodal input
        mm_data = {"image": pil_image}

        outputs = model.embed(
            [{"prompt": "", "multi_modal_data": mm_data}]
        )

        embedding = outputs[0].outputs.embedding
        if len(embedding) > self.output_dimensions:
            embedding = embedding[:self.output_dimensions]

        return list(embedding)

    async def embed_multimodal(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """Generate embedding for multimodal content using vLLM."""
        self.logger.debug("Generating vLLM multimodal embedding")

        if not text and not image:
            raise ValueError("At least one of text or image must be provided")

        model = self._get_model()

        prompt = text or ""
        mm_data = None

        if image:
            from PIL import Image
            import io

            image_bytes = self.load_image_bytes(image)
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            mm_data = {"image": pil_image}

        if mm_data:
            outputs = model.embed(
                [{"prompt": prompt, "multi_modal_data": mm_data}]
            )
        else:
            outputs = model.embed([prompt])

        embedding = outputs[0].outputs.embedding
        if len(embedding) > self.output_dimensions:
            embedding = embedding[:self.output_dimensions]

        return list(embedding)

    @property
    def dimensions(self) -> int:
        return self._dimensions


class VLLMEmbeddingProviderPlugin(EmbeddingProviderPluginBase):
    PROVIDER_NAME = EmbeddingProviderType.VLLM

    def initialize(self, v: Variables, logger: Logger) -> object | None:
        return VLLMEmbeddingProvider(
            model_name=v.environ(MEMORYLAYER_EMBEDDING_MODEL, default=DEFAULT_EMBEDDING_MODEL),
            dtype=v.environ(MEMORYLAYER_EMBEDDING_VLLM_DTYPE, default=DEFAULT_DTYPE),
            max_model_len=v.environ(MEMORYLAYER_EMBEDDING_VLLM_MAX_LENGTH, default=DEFAULT_MAX_LENGTH, type_fn=int),
            output_dimensions=v.environ(MEMORYLAYER_EMBEDDING_DIMENSIONS, default=DEFAULT_EMBEDDING_DIMENSIONS, type_fn=int),
        )
