import base64
import numpy as np

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from scitrera_app_framework.api import Variables, Plugin, enabled_option_pattern
from scitrera_app_framework import get_extension, get_logger

from ...config import (MEMORYLAYER_EMBEDDING_PROVIDER, DEFAULT_MEMORYLAYER_EMBEDDING_PROVIDER,
                       MEMORYLAYER_EMBEDDING_SERVICE, DEFAULT_MEMORYLAYER_EMBEDDING_SERVICE)

EXT_EMBEDDING_PROVIDER = 'embedding-provider'
EXT_EMBEDDING_SERVICE = 'embedding-service'


class EmbeddingType(str, Enum):
    """Type of content being embedded."""
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"  # Combined text + image


@dataclass
class EmbeddingInput:
    """Input for embedding generation, supporting multimodal content."""
    text: Optional[str] = None
    image: Optional[Union[str, bytes, Path]] = None  # Base64, bytes, URL, or file path

    def __post_init__(self):
        if not self.text and not self.image:
            raise ValueError("At least one of text or image must be provided")

    @property
    def embedding_type(self) -> EmbeddingType:
        if self.text and self.image:
            return EmbeddingType.MULTIMODAL
        elif self.image:
            return EmbeddingType.IMAGE
        return EmbeddingType.TEXT

    def to_dict(self) -> dict:
        """Convert to dict format for Qwen3-VL."""
        result = {}
        if self.text:
            result["text"] = self.text
        if self.image:
            result["image"] = self.image if isinstance(self.image, str) else None
        return result


@dataclass
class MultiVectorEmbedding:
    """
    Multi-vector embedding (used by ColPali).

    Instead of a single vector, stores multiple vectors that represent
    different aspects/patches of the content. Enables late interaction
    retrieval which can be more accurate for documents with visual elements.
    """
    vectors: list[list[float]]  # List of embedding vectors

    @property
    def num_vectors(self) -> int:
        return len(self.vectors)

    @property
    def dimensions(self) -> int:
        return len(self.vectors[0]) if self.vectors else 0


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    def __init__(self, output_dimensions: Optional[int] = None):
        self._dimensions = output_dimensions
        self.logger = get_logger(name=self.__class__.__name__)

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (more efficient)."""
        pass

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        return self._dimensions


class MultimodalEmbeddingProvider(EmbeddingProvider):
    """
    Abstract multimodal embedding provider that supports text, images, and combined content.

    Extends base EmbeddingProvider with multimodal capabilities.
    """

    @abstractmethod
    async def embed_image(self, image: Union[str, bytes, Path]) -> list[float]:
        """Generate embedding for an image."""
        pass

    @abstractmethod
    async def embed_multimodal(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """Generate embedding for combined text and image."""
        pass

    async def embed_input(self, input: EmbeddingInput) -> list[float]:
        """Generate embedding for EmbeddingInput (convenience method)."""
        if input.embedding_type == EmbeddingType.TEXT:
            return await self.embed(input.text)
        elif input.embedding_type == EmbeddingType.IMAGE:
            return await self.embed_image(input.image)
        else:
            return await self.embed_multimodal(input.text, input.image)

    @staticmethod
    def load_image_bytes(image: Union[str, bytes, Path]) -> bytes:
        """Load image as bytes from various input formats."""
        if isinstance(image, bytes):
            return image
        elif isinstance(image, Path):
            return image.read_bytes()
        elif isinstance(image, str):
            # Check if it's base64 or a file path
            if image.startswith("data:image"):
                # Data URL format
                _, encoded = image.split(",", 1)
                return base64.b64decode(encoded)
            elif image.startswith(("http://", "https://")):
                # URL - download
                import urllib.request
                with urllib.request.urlopen(image) as response:
                    return response.read()
            elif len(image) > 500 and not Path(image).exists():
                # Likely base64 string
                return base64.b64decode(image)
            else:
                # File path
                return Path(image).read_bytes()
        raise ValueError(f"Unsupported image type: {type(image)}")


class ColPaliEmbeddingProvider(MultimodalEmbeddingProvider):
    """
    ColPali multi-vector embedding provider.

    Uses late interaction (multi-vector) approach for document retrieval,
    particularly effective for documents with visual elements like PDFs.

    Features:
    - Multi-vector embeddings (one per image patch/token)
    - Late interaction scoring (MaxSim)
    - Excellent for document retrieval with visual elements
    - Self-hostable
    """

    def __init__(
            self,
            model_name: str = "vidore/colpali-v1.3",
            device: Optional[str] = None,
    ):
        super().__init__(output_dimensions=128)  # ColPali default dimension per vector
        self.model_name = model_name
        self.device = device
        self._model = None
        self._processor = None
        self.logger.info("Initialized ColPaliEmbeddingProvider with model: %s", model_name)

    def _get_model(self):
        """Lazy load the ColPali model."""
        if self._model is None:
            import torch

            self.logger.info("Loading ColPali model: %s", self.model_name)

            # Determine device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            try:
                from colpali_engine.models import ColPali
                from colpali_engine.utils.colpali_processing_utils import (
                    ColPaliProcessor
                )

                self._model = ColPali.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                ).to(self.device)
                self._model.eval()

                self._processor = ColPaliProcessor.from_pretrained(self.model_name)

            except ImportError:
                self.logger.warning(
                    "colpali_engine not installed. Install with: pip install colpali-engine"
                )
                raise

        return self._model, self._processor

    async def embed(self, text: str) -> list[float]:
        """
        Generate single-vector embedding for text (averaged from multi-vector).

        For compatibility with standard vector databases.
        """
        multi_vec = await self.embed_text_multivector(text)
        # Average all vectors to get single vector
        return np.mean(multi_vec.vectors, axis=0).tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate single-vector embeddings for batch."""
        results = []
        for text in texts:
            results.append(await self.embed(text))
        return results

    async def embed_image(self, image: Union[str, bytes, Path]) -> list[float]:
        """Generate single-vector embedding for image (averaged)."""
        multi_vec = await self.embed_image_multivector(image)
        return np.mean(multi_vec.vectors, axis=0).tolist()

    async def embed_multimodal(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """Generate single-vector embedding for multimodal content."""
        if image:
            return await self.embed_image(image)
        elif text:
            return await self.embed(text)
        raise ValueError("At least one of text or image must be provided")

    async def embed_text_multivector(self, text: str) -> MultiVectorEmbedding:
        """Generate multi-vector embedding for text (native ColPali format)."""
        self.logger.debug("Generating ColPali multi-vector for text: %s chars", len(text))
        import torch

        model, processor = self._get_model()

        # Process text query
        inputs = processor.process_queries([text]).to(self.device)

        with torch.no_grad():
            embeddings = model(**inputs)

        # Return as MultiVectorEmbedding
        vectors = embeddings[0].cpu().numpy().tolist()
        return MultiVectorEmbedding(vectors=vectors)

    async def embed_image_multivector(
            self,
            image: Union[str, bytes, Path]
    ) -> MultiVectorEmbedding:
        """Generate multi-vector embedding for image (native ColPali format)."""
        self.logger.debug("Generating ColPali multi-vector for image")
        import torch
        from PIL import Image
        import io

        model, processor = self._get_model()

        # Load image
        image_bytes = self.load_image_bytes(image)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Process image
        inputs = processor.process_images([pil_image]).to(self.device)

        with torch.no_grad():
            embeddings = model(**inputs)

        vectors = embeddings[0].cpu().numpy().tolist()
        return MultiVectorEmbedding(vectors=vectors)

    @staticmethod
    def maxsim_score(
            query_vectors: MultiVectorEmbedding,
            doc_vectors: MultiVectorEmbedding
    ) -> float:
        """
        Calculate MaxSim score between query and document multi-vectors.

        This is the late interaction scoring used by ColPali/ColBERT.
        For each query vector, find max similarity to any document vector,
        then sum these max similarities.
        """
        q_vecs = np.array(query_vectors.vectors)
        d_vecs = np.array(doc_vectors.vectors)

        # Compute all pairwise similarities
        similarities = np.dot(q_vecs, d_vecs.T)

        # MaxSim: for each query vector, take max over document vectors
        max_sims = np.max(similarities, axis=1)

        # Sum of max similarities
        return float(np.sum(max_sims))

    @property
    def dimensions(self) -> int:
        return self._dimensions


# noinspection PyAbstractClass
class EmbeddingProviderPluginBase(Plugin):
    """Base Plugin Implementation for embedding providers."""
    PROVIDER_NAME: str = ''

    def name(self) -> str:
        return f"{EXT_EMBEDDING_PROVIDER}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_EMBEDDING_PROVIDER

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_EMBEDDING_PROVIDER, default=DEFAULT_MEMORYLAYER_EMBEDDING_PROVIDER,
                                      self_attr='PROVIDER_NAME')


# noinspection PyAbstractClass
class EmbeddingServicePluginBase(Plugin):
    """Base plugin for association service - allows SaaS to extend/override."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_EMBEDDING_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_EMBEDDING_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_EMBEDDING_SERVICE,
                                      default=DEFAULT_MEMORYLAYER_EMBEDDING_SERVICE,
                                      self_attr='PROVIDER_NAME')

    def get_dependencies(self, v: Variables):
        return (EXT_EMBEDDING_PROVIDER,)
