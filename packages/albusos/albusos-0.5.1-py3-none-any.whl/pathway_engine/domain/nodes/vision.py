"""Vision nodes - Image analysis and generation.

First-class pathway nodes for vision capabilities.
Uses tools via context to maintain layering (pathway_engine cannot import stdlib).
"""

from __future__ import annotations

import base64
import logging
from typing import Any, Literal

from pathway_engine.domain.context import Context
from pathway_engine.domain.models.vision import (
    VisionInput,
    VisionOutput,
    ImageGenInput,
    ImageGenOutput,
)
from pathway_engine.domain.nodes.base import NodeBase

logger = logging.getLogger(__name__)


class VisionNode(NodeBase):
    """Analyze images using vision-capable LLMs.

    Usage:
        node = VisionNode(
            id="analyze",
            prompt="Describe what you see in this image",
            model="gpt-4o",
        )
    """

    type: Literal["vision"] = "vision"
    prompt: str = "Describe this image."
    model: str = "gpt-4o"
    detail: str = "auto"  # auto, low, high
    max_output_tokens: int = 1024

    async def compute(
        self, inputs: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Analyze an image and return description."""
        # Get image from inputs
        image_base64 = inputs.get("image_base64") or inputs.get("image")
        image_url = inputs.get("image_url")
        image_data = inputs.get("image_data")

        if image_data and not image_base64:
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        prompt = inputs.get("prompt", self.prompt)
        model = inputs.get("model", self.model)

        # Build vision input
        vision_input = VisionInput(
            image_base64=image_base64,
            image_url=image_url,
            prompt=prompt,
            model=model,
            detail=self.detail,  # type: ignore[arg-type]
            max_output_tokens=self.max_output_tokens,
        )

        # Call LLM with vision via tool
        llm_generate = ctx.tools.get("llm.generate")
        if not llm_generate:
            return VisionOutput(
                response="Error: llm.generate tool not available",
                model=model,
            ).model_dump()

        # Prepare message with image
        content: list[dict[str, Any]] = []

        if vision_input.image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": vision_input.image_url, "detail": self.detail},
            })
        elif vision_input.image_base64:
            mime_type = self._detect_mime_type(vision_input.image_base64)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{vision_input.image_base64}",
                    "detail": self.detail,
                },
            })

        content.append({"type": "text", "text": prompt})

        result = await llm_generate(
            {
                "messages": [{"role": "user", "content": content}],
                "model": model,
                "max_tokens": self.max_output_tokens,
            },
            ctx,
        )

        response_text = result.get("response", result.get("content", result.get("text", "")))

        return VisionOutput(
            response=response_text,
            model=model,
            usage=result.get("usage"),
        ).model_dump()

    def _detect_mime_type(self, image_base64: str) -> str:
        """Detect MIME type from base64 prefix."""
        if image_base64.startswith("/9j/"):
            return "image/jpeg"
        elif image_base64.startswith("iVBORw"):
            return "image/png"
        elif image_base64.startswith("R0lGOD"):
            return "image/gif"
        return "image/png"


class ImageGenNode(NodeBase):
    """Generate images from text prompts.

    Uses vision.generate tool via context.

    Usage:
        node = ImageGenNode(
            id="generate",
            model="dall-e-3",
            size="1024x1024",
        )
    """

    type: Literal["image_gen"] = "image_gen"
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"  # standard, hd
    style: str | None = None  # vivid, natural
    n: int = 1
    response_format: str = "url"  # url, b64_json

    async def compute(
        self, inputs: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Generate an image from a text prompt."""
        prompt = inputs.get("prompt", "")
        if not prompt:
            return ImageGenOutput(
                images=[],
                model=self.model,
                provider="openai",
            ).model_dump()

        model = inputs.get("model", self.model)

        # Use vision.generate tool if available
        vision_generate = ctx.tools.get("vision.generate")
        if vision_generate:
            result = await vision_generate(
                {
                    "prompt": prompt,
                    "model": model,
                    "size": inputs.get("size", self.size),
                    "quality": inputs.get("quality", self.quality),
                    "n": inputs.get("n", self.n),
                    "response_format": inputs.get("response_format", self.response_format),
                    "style": self.style,
                },
                ctx,
            )
            return result

        # Fallback: return error if tool not available
        return ImageGenOutput(
            images=[],
            model=model,
            provider="openai",
            metadata={"error": "vision.generate tool not available"},
        ).model_dump()


__all__ = [
    "VisionNode",
    "ImageGenNode",
]
