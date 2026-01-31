from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TransformInput(BaseModel):
    """Input for data transformation nodes."""

    model_config = {"extra": "forbid"}

    data: Any
    transform_type: str
    options: dict[str, Any] = Field(default_factory=dict)


class TransformOutput(BaseModel):
    """Output from data transformation nodes."""

    model_config = {"extra": "forbid"}

    data: Any
    transform_applied: str
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["TransformInput", "TransformOutput"]
