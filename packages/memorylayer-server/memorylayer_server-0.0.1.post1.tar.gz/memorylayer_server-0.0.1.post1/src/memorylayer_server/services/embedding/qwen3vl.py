from logging import Logger
from pathlib import Path
from typing import Optional, Any, Union

from scitrera_app_framework import Variables, ext_parse_bool

from ...config import EmbeddingProviderType, MEMORYLAYER_EMBEDDING_MODEL, MEMORYLAYER_EMBEDDING_DIMENSIONS

from .base import MultimodalEmbeddingProvider, EmbeddingProviderPluginBase

MEMORYLAYER_EMBEDDING_DEVICE = 'MEMORYLAYER_EMBEDDING_DEVICE'
MEMORYLAYER_EMBEDDING_QWEN3_VL_USE_FLASH_ATTENTION = 'MEMORYLAYER_EMBEDDING_QWEN3_VL_USE_FLASH_ATTENTION'

DEFAULT_EMBEDDING_MODEL = 'Qwen/Qwen3-VL-Embedding-2B'
DEFAULT_EMBEDDING_DEVICE = None
DEFAULT_QWEN3_VL_USE_FLASH_ATTENTION = True
DEFAULT_EMBEDDING_DIMENSIONS = 2048


class Qwen3VLEmbeddingProvider(MultimodalEmbeddingProvider):
    """
    Qwen3-VL-Embedding-2B multimodal embedding provider.

    A 2B parameter vision-language model that creates unified embeddings
    for text, images, videos, and combined multimodal content.

    Model: https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B

    Features:
    - Self-hostable (no external API required)
    - Multimodal (text + image + video in same vector space)
    - Configurable output dimensions (64 to 2048)
    - 32k context length
    - GPU accelerated with flash attention support
    """

    def __init__(
            self,
            model_name: str = "Qwen/Qwen3-VL-Embedding-2B",
            device: Optional[str] = None,
            use_flash_attention: bool = True,
            output_dimensions: int = 2048,
    ):
        super().__init__(output_dimensions=output_dimensions)
        self.model_name = model_name
        self.device = device
        self.use_flash_attention = use_flash_attention
        self.output_dimensions = output_dimensions
        self._model = None
        self._dimensions = output_dimensions
        self.logger.info(
            "Initialized Qwen3VLEmbeddingProvider with model: %s, dimensions: %d",
            model_name,
            output_dimensions
        )

    def _get_model(self):
        """Lazy load the Qwen3-VL model."""
        if self._model is None:
            import torch

            self.logger.info("Loading Qwen3-VL model: %s", self.model_name)

            # Determine device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.logger.info("Using device: %s", self.device)

            try:
                # Try using the official Qwen3VLEmbedder interface
                from qwen_vl_utils import Qwen3VLEmbedder

                model_kwargs = {
                    "model_name_or_path": self.model_name,
                    "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                }

                if self.use_flash_attention and self.device == "cuda":
                    model_kwargs["attn_implementation"] = "flash_attention_2"

                self._model = Qwen3VLEmbedder(**model_kwargs)
                self._use_qwen_embedder = True
                self.logger.info("Using Qwen3VLEmbedder interface")

            except ImportError:
                self.logger.warning("qwen_vl_utils not found, using transformers fallback")
                # Fallback to transformers
                from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

                model_kwargs = {
                    "trust_remote_code": True,
                    "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                }

                if self.use_flash_attention and self.device == "cuda":
                    model_kwargs["attn_implementation"] = "flash_attention_2"

                self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                    self.model_name,
                    **model_kwargs
                ).to(self.device)
                self._model.eval()

                self._processor = AutoProcessor.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                self._use_qwen_embedder = False
                self.logger.info("Using transformers fallback")

        return self._model

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        self.logger.debug("Generating Qwen3-VL embedding for text: %s chars", len(text))

        model = self._get_model()

        if hasattr(self, '_use_qwen_embedder') and self._use_qwen_embedder:
            # Use official interface
            inputs = [{"text": text}]
            embeddings = model.process(inputs, output_dimensions=self.output_dimensions)
            return embeddings[0].cpu().numpy().tolist()
        else:
            # Transformers fallback
            return await self._embed_with_transformers(text=text)

    async def _embed_with_transformers(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """Generate embedding using transformers fallback."""
        import torch
        from PIL import Image
        import io

        model = self._get_model()

        # Prepare messages in Qwen VL format
        messages = [{"role": "user", "content": []}]

        if image:
            # Load image
            if isinstance(image, (str, Path)) and not str(image).startswith(("http://", "https://")):
                image_bytes = self.load_image_bytes(image)
                pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                messages[0]["content"].append({"type": "image", "image": pil_image})
            else:
                messages[0]["content"].append({"type": "image", "image": str(image)})

        if text:
            messages[0]["content"].append({"type": "text", "text": text})

        # Process with processor
        text_prompt = self._processor.apply_chat_template(messages, add_generation_prompt=True)

        if image:
            inputs = self._processor(
                text=[text_prompt],
                images=[pil_image] if 'pil_image' in locals() else None,
                return_tensors="pt",
                padding=True,
            ).to(self.device)
        else:
            inputs = self._processor(
                text=[text_prompt],
                return_tensors="pt",
                padding=True,
            ).to(self.device)

        # Generate embedding using hidden states
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
            # Use last hidden state mean pooling
            hidden_states = outputs.hidden_states[-1]
            embedding = hidden_states.mean(dim=1).squeeze()

            # Truncate/pad to target dimensions
            if embedding.shape[-1] > self.output_dimensions:
                embedding = embedding[:self.output_dimensions]

        return embedding.cpu().numpy().tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts."""
        self.logger.debug("Generating Qwen3-VL embeddings for batch of %s texts", len(texts))

        model = self._get_model()

        if hasattr(self, '_use_qwen_embedder') and self._use_qwen_embedder:
            # Use official interface
            inputs = [{"text": t} for t in texts]
            embeddings = model.process(inputs, output_dimensions=self.output_dimensions)
            return [e.cpu().numpy().tolist() for e in embeddings]
        else:
            # Transformers fallback - process one at a time
            results = []
            for text in texts:
                emb = await self._embed_with_transformers(text=text)
                results.append(emb)
            return results

    async def embed_image(self, image: Union[str, bytes, Path]) -> list[float]:
        """Generate embedding for an image."""
        self.logger.debug("Generating Qwen3-VL embedding for image")

        model = self._get_model()

        if hasattr(self, '_use_qwen_embedder') and self._use_qwen_embedder:
            # Use official interface
            # Convert to URL or path string if needed
            if isinstance(image, bytes):
                # Save to temp file for Qwen embedder
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    f.write(image)
                    image_path = f.name
                inputs = [{"image": image_path}]
            elif isinstance(image, Path):
                inputs = [{"image": str(image)}]
            else:
                inputs = [{"image": image}]

            embeddings = model.process(inputs, output_dimensions=self.output_dimensions)
            return embeddings[0].cpu().numpy().tolist()
        else:
            # Transformers fallback
            return await self._embed_with_transformers(image=image)

    async def embed_multimodal(
            self,
            text: Optional[str] = None,
            image: Optional[Union[str, bytes, Path]] = None
    ) -> list[float]:
        """Generate embedding for combined text and image."""
        self.logger.debug("Generating Qwen3-VL multimodal embedding")

        if not text and not image:
            raise ValueError("At least one of text or image must be provided")

        model = self._get_model()

        if hasattr(self, '_use_qwen_embedder') and self._use_qwen_embedder:
            # Use official interface
            input_dict = {}
            if text:
                input_dict["text"] = text
            if image:
                if isinstance(image, bytes):
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(image)
                        input_dict["image"] = f.name
                elif isinstance(image, Path):
                    input_dict["image"] = str(image)
                else:
                    input_dict["image"] = image

            embeddings = model.process([input_dict], output_dimensions=self.output_dimensions)
            return embeddings[0].cpu().numpy().tolist()
        else:
            # Transformers fallback
            return await self._embed_with_transformers(text=text, image=image)


class Qwen3VLEmbeddingProviderPlugin(EmbeddingProviderPluginBase):
    PROVIDER_NAME = EmbeddingProviderType.QWEN3_VL

    def initialize(self, v: Variables, logger: Logger) -> object | None:
        return Qwen3VLEmbeddingProvider(
            model_name=v.environ(MEMORYLAYER_EMBEDDING_MODEL, default=DEFAULT_EMBEDDING_MODEL),
            device=v.environ(MEMORYLAYER_EMBEDDING_DEVICE, default=DEFAULT_EMBEDDING_DEVICE),
            use_flash_attention=v.environ(MEMORYLAYER_EMBEDDING_QWEN3_VL_USE_FLASH_ATTENTION,
                                          default=DEFAULT_QWEN3_VL_USE_FLASH_ATTENTION, type_fn=ext_parse_bool),
            output_dimensions=v.environ(MEMORYLAYER_EMBEDDING_DIMENSIONS, default=DEFAULT_EMBEDDING_DIMENSIONS, type_fn=int),
        )
