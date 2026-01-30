from __future__ import annotations

from typing import Any

from weav_provider_router.base import ImageBase, ImageConfig, ImageResponse


class OpenAIImage(ImageBase):
    """OpenAI DALL-E image generation adapter."""

    def __init__(self, api_key: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package is required for OpenAIImage. Install it to use this provider.") from exc
        
        self._client = AsyncOpenAI(api_key=api_key)
        self._api_key = api_key

    async def generate(self, prompt: str, config: ImageConfig) -> ImageResponse:
        """Generate an image using DALL-E."""
        kwargs: dict[str, Any] = {
            "model": config.model,
            "prompt": prompt,
            "size": config.size,
            "quality": config.quality,
            "n": config.n,
        }
        
        if config.style:
            kwargs["style"] = config.style
        
        response = await self._client.images.generate(**kwargs)
        
        if response.data:
            first_image = response.data[0]
            return ImageResponse(
                url=first_image.url,
                b64_json=getattr(first_image, 'b64_json', None),
                revised_prompt=getattr(first_image, 'revised_prompt', None)
            )
        else:
            raise RuntimeError("No image generated")

    async def edit(self, image: bytes, prompt: str, mask: bytes | None = None, config: ImageConfig | None = None) -> ImageResponse:
        """Edit an existing image using DALL-E."""
        if config is None:
            raise ValueError("config is required for edit operation")
        
        kwargs: dict[str, Any] = {
            "model": config.model,
            "image": image,
            "prompt": prompt,
            "size": config.size,
            "n": config.n,
        }
        
        if mask:
            kwargs["mask"] = mask
        
        response = await self._client.images.edit(**kwargs)
        
        if response.data:
            first_image = response.data[0]
            return ImageResponse(
                url=first_image.url,
                b64_json=getattr(first_image, 'b64_json', None),
                revised_prompt=getattr(first_image, 'revised_prompt', None)
            )
        else:
            raise RuntimeError("No image generated")

    async def variations(self, image: bytes, n: int = 1, config: ImageConfig | None = None) -> list[ImageResponse]:
        """Generate variations of an existing image."""
        if config is None:
            raise ValueError("config is required for variations operation")
        
        kwargs: dict[str, Any] = {
            "model": config.model,
            "image": image,
            "n": n,
            "size": config.size,
        }
        
        response = await self._client.images.create_variation(**kwargs)
        
        results = []
        for img_data in response.data:
            results.append(ImageResponse(
                url=img_data.url,
                b64_json=getattr(img_data, 'b64_json', None),
            ))
        
        return results

    def list_models(self) -> list[str]:
        """List available DALL-E models."""
        return [
            "dall-e-3",
            "dall-e-2",
        ]
