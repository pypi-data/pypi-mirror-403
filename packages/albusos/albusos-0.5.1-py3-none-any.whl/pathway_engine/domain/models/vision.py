"""Vision modality models - image understanding and generation.

These define the contracts for vision nodes.
Implementation is in pathway_engine.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# =============================================================================
# IMAGE ANALYSIS (Vision LLM)
# =============================================================================


class VisionInput(BaseModel):
    """Input for vision/image analysis nodes."""

    model_config = {"extra": "allow"}

    image_data: bytes | None = None  # Raw image bytes
    image_url: str | None = None  # URL to image
    image_base64: str | None = None  # Base64-encoded image

    prompt: str = "Describe this image."
    model: str = "gpt-4o"  # Vision-capable model

    max_output_tokens: int = 1024
    detail: Literal["auto", "low", "high"] = "auto"

    context: dict[str, Any] = Field(default_factory=dict)


class VisionOutput(BaseModel):
    """Output from vision/image analysis nodes."""

    model_config = {"extra": "allow"}

    response: str  # LLM response describing the image

    # Structured extraction (if requested)
    objects: list[dict[str, Any]] = Field(default_factory=list)
    text_detected: list[str] = Field(default_factory=list)  # OCR results

    model: str = ""
    usage: dict[str, int] | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# IMAGE GENERATION
# =============================================================================


class ImageGenInput(BaseModel):
    """Input for image generation nodes."""

    model_config = {"extra": "allow"}

    prompt: str
    model: str = "dall-e-3"  # dall-e-3, dall-e-2, stable-diffusion-xl, etc.
    provider: Literal["openai", "stability"] = "openai"

    # Generation parameters
    size: str = "1024x1024"  # 1024x1024, 1792x1024, 1024x1792
    quality: Literal["standard", "hd"] = "standard"
    style: Literal["vivid", "natural"] | None = None
    n: int = 1  # Number of images to generate

    # Response format
    response_format: Literal["url", "b64_json"] = "url"

    # Stability-specific
    cfg_scale: float | None = None
    steps: int | None = None
    seed: int | None = None

    context: dict[str, Any] = Field(default_factory=dict)


class ImageGenOutput(BaseModel):
    """Output from image generation nodes."""

    model_config = {"extra": "allow"}

    images: list[dict[str, Any]] = Field(
        default_factory=list
    )  # List of {url, b64_json}

    # First image shortcuts
    image_url: str | None = None
    image_base64: str | None = None

    revised_prompt: str | None = None  # DALL-E 3 may revise prompts

    model: str = ""
    provider: str = ""

    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# IMAGE TRANSFORM (resize, crop, filter, etc.)
# =============================================================================


class ImageTransformInput(BaseModel):
    """Input for image transformation nodes."""

    model_config = {"extra": "allow"}

    image_data: bytes | None = None
    image_url: str | None = None
    image_base64: str | None = None

    operation: Literal[
        "resize", "crop", "rotate", "flip", "grayscale", "blur", "sharpen"
    ]

    # Resize parameters
    width: int | None = None
    height: int | None = None
    maintain_aspect: bool = True

    # Crop parameters
    crop_box: tuple[int, int, int, int] | None = None  # (left, top, right, bottom)

    # Rotate parameters
    angle: float = 0.0

    # Filter parameters
    blur_radius: float | None = None
    sharpen_amount: float | None = None

    output_format: str = "png"

    context: dict[str, Any] = Field(default_factory=dict)


class ImageTransformOutput(BaseModel):
    """Output from image transformation nodes."""

    model_config = {"extra": "allow"}

    image_data: bytes | None = None
    image_base64: str | None = None
    image_url: str | None = None

    format: str = "png"
    width: int | None = None
    height: int | None = None

    operation_applied: str = ""

    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "VisionInput",
    "VisionOutput",
    "ImageGenInput",
    "ImageGenOutput",
    "ImageTransformInput",
    "ImageTransformOutput",
]
