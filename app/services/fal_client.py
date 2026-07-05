"""fal.ai image generation client."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


class FalImageError(Exception):
    """Raised when fal.ai image generation fails."""


class FalImageClient:
    def __init__(self, api_key: str, default_model: str, timeout: int = 180):
        self.api_key = (api_key or "").strip()
        self.default_model = (default_model or "fal-ai/flux/dev").strip()
        self.timeout = int(timeout or 180)

    async def generate_image(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int | None = None,
        guidance_scale: float | None = None,
        seed: int | None = None,
        model: str | None = None,
    ) -> list[bytes]:
        if not self.api_key:
            raise FalImageError("FAL_KEY is not configured")
        endpoint = (model or self.default_model or "").strip()
        if not endpoint:
            raise FalImageError("fal.ai model endpoint is not configured")

        os.environ["FAL_KEY"] = self.api_key
        arguments: dict[str, Any] = {
            "prompt": prompt,
            "image_size": {"width": int(width), "height": int(height)},
            "num_images": 1,
        }
        if negative_prompt:
            arguments["negative_prompt"] = negative_prompt
        if steps is not None:
            arguments["num_inference_steps"] = int(steps)
        if guidance_scale is not None:
            arguments["guidance_scale"] = float(guidance_scale)
        if seed is not None and int(seed) != -1:
            arguments["seed"] = int(seed)

        try:
            import fal_client as fal_sdk
        except Exception as exc:  # pragma: no cover - dependency/environment issue
            raise FalImageError("fal-client dependency is not installed") from exc

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(fal_sdk.subscribe, endpoint, arguments=arguments),
                timeout=self.timeout,
            )
        except Exception as exc:
            raise FalImageError(f"fal.ai request failed for {endpoint}: {exc}") from exc

        urls = self._extract_urls(result)
        if not urls:
            raise FalImageError("fal.ai response did not contain image URLs")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                responses = await asyncio.gather(*(client.get(url) for url in urls))
            images: list[bytes] = []
            for response in responses:
                response.raise_for_status()
                images.append(response.content)
            return images
        except Exception as exc:
            raise FalImageError(f"failed to download fal.ai image: {exc}") from exc

    @staticmethod
    def _extract_urls(result: Any) -> list[str]:
        urls: list[str] = []
        if isinstance(result, dict):
            images = result.get("images")
            if isinstance(images, list):
                for item in images:
                    if isinstance(item, dict) and item.get("url"):
                        urls.append(str(item["url"]))
                    elif isinstance(item, str):
                        urls.append(item)
            image = result.get("image")
            if isinstance(image, dict) and image.get("url"):
                urls.append(str(image["url"]))
            if result.get("url"):
                urls.append(str(result["url"]))
        return list(dict.fromkeys(urls))
