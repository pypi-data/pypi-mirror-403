from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMAttachment(BaseModel):
    """Provider-agnostic attachment DTO.

    This is the "clean" alternative to embedding provider-specific multimodal message parts.
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["image"] = "image"
    mime_type: str = "image/png"
    data_base64: str = Field(
        min_length=1, description="Base64-encoded payload (no data: prefix)."
    )
    name: Optional[str] = None

    @field_validator("mime_type")
    @classmethod
    def _mime(cls, v: str) -> str:
        s = str(v or "").strip()
        if not s:
            raise ValueError("mime_type_empty")
        return s

    @field_validator("data_base64")
    @classmethod
    def _b64(cls, v: str) -> str:
        s = str(v or "").strip()
        if not s:
            raise ValueError("data_base64_empty")
        # Size cap guardrail: ~4.5MB binary is already huge for prompts; keep parity with existing tool caps.
        if len(s) > 6_000_000:
            raise ValueError("attachment_too_large")
        return s


__all__ = ["LLMAttachment"]
