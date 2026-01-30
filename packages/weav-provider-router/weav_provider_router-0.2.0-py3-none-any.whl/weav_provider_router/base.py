"""Base classes and interfaces for all providers (LLM, Image, Video, Embedding)."""

from __future__ import annotations
from typing import Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum


class ImageSize(str, Enum):
    """Standard image sizes."""
    SQUARE_256 = "256x256"
    SQUARE_512 = "512x512"
    SQUARE_1024 = "1024x1024"
    LANDSCAPE_1792_1024 = "1792x1024"
    PORTRAIT_1024_1792 = "1024x1792"


class VideoQuality(str, Enum):
    """Video quality presets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class CompletionConfig:
    """Configuration for LLM completion requests."""

    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    stop: list[str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageConfig:
    """Configuration for image generation requests."""

    model: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: str | None = None
    n: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageResponse:
    """Response from image generation."""

    url: str | None = None
    b64_json: str | None = None
    revised_prompt: str | None = None


@dataclass
class VideoConfig:
    """Configuration for video generation requests."""

    model: str
    duration: int = 5  # seconds
    fps: int = 24
    quality: str = "medium"
    aspect_ratio: str = "16:9"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoResponse:
    """Response from video generation."""

    url: str | None = None
    duration: float | None = None
    thumbnail_url: str | None = None


@dataclass
class EmbeddingConfig:
    """Configuration for embedding requests."""

    model: str
    dimensions: int | None = None
    encoding_format: str = "float"
    extra: dict[str, Any] = field(default_factory=dict)


class LLMBase:
    """Base interface for all LLM provider adapters."""

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        """
        Send chat messages and get a response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            config: Completion configuration

        Returns:
            Generated response text
        """
        raise NotImplementedError

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        """
        Complete a text prompt.

        Args:
            prompt: Text prompt to complete
            config: Completion configuration

        Returns:
            Completed text
        """
        raise NotImplementedError

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        """
        Stream chat responses.

        Args:
            messages: List of message dictionaries
            config: Completion configuration

        Yields:
            Text chunks as they arrive
        """
        raise NotImplementedError
        # Make this a generator
        yield ""  # pragma: no cover

    def list_models(self) -> list[str]:
        """
        List available models for this provider.

        Returns:
            List of model identifiers
        """
        raise NotImplementedError


class ImageBase:
    """Base interface for image generation providers."""

    async def generate(self, prompt: str, config: ImageConfig) -> ImageResponse:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            config: Image generation configuration

        Returns:
            ImageResponse with URL or base64 data
        """
        raise NotImplementedError

    async def edit(self, image: bytes, prompt: str, mask: bytes | None = None, config: ImageConfig | None = None) -> ImageResponse:
        """
        Edit an existing image based on a prompt.

        Args:
            image: Original image bytes
            prompt: Text description of desired edits
            mask: Optional mask image bytes
            config: Image generation configuration

        Returns:
            ImageResponse with edited image
        """
        raise NotImplementedError

    async def variations(self, image: bytes, n: int = 1, config: ImageConfig | None = None) -> list[ImageResponse]:
        """
        Generate variations of an existing image.

        Args:
            image: Original image bytes
            n: Number of variations to generate
            config: Image generation configuration

        Returns:
            List of ImageResponse objects
        """
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """List available image models."""
        raise NotImplementedError


class VideoBase:
    """Base interface for video generation providers."""

    async def generate(self, prompt: str, config: VideoConfig) -> VideoResponse:
        """
        Generate a video from a text prompt.

        Args:
            prompt: Text description of the video to generate
            config: Video generation configuration

        Returns:
            VideoResponse with video URL
        """
        raise NotImplementedError

    async def image_to_video(self, image: bytes, config: VideoConfig) -> VideoResponse:
        """
        Generate a video from a starting image.

        Args:
            image: Starting image bytes
            config: Video generation configuration

        Returns:
            VideoResponse with video URL
        """
        raise NotImplementedError

    async def extend(self, video_url: str, config: VideoConfig) -> VideoResponse:
        """
        Extend an existing video.

        Args:
            video_url: URL of the video to extend
            config: Video generation configuration

        Returns:
            VideoResponse with extended video
        """
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """List available video models."""
        raise NotImplementedError


class EmbeddingBase:
    """Base interface for text embedding providers."""

    async def embed(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of text strings to embed
            config: Embedding configuration

        Returns:
            List of embedding vectors
        """
        raise NotImplementedError

    async def embed_query(self, text: str, config: EmbeddingConfig) -> list[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text to embed
            config: Embedding configuration

        Returns:
            Embedding vector
        """
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """List available embedding models."""
        raise NotImplementedError


__all__ = [
    "CompletionConfig",
    "ImageConfig", 
    "VideoConfig",
    "EmbeddingConfig",
    "ImageResponse",
    "VideoResponse",
    "LLMBase",
    "ImageBase",
    "VideoBase",
    "EmbeddingBase",
    "ImageSize",
    "VideoQuality",
]
