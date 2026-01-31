from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationInput(BaseModel):
    """Input for validation nodes."""

    model_config = {"extra": "forbid"}

    data: Any
    validation_schema: dict[str, Any] | None = None
    rules: list[str] = Field(default_factory=list)


class ValidationOutput(BaseModel):
    """Output from validation nodes."""

    model_config = {"extra": "forbid"}

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    cleaned_data: Any = None


__all__ = ["ValidationInput", "ValidationOutput"]
