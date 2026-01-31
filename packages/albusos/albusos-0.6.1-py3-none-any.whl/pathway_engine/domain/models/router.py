from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RouterInput(BaseModel):
    """Input for routing decisions."""

    model_config = {"extra": "forbid"}

    data: Any
    routes: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouterOutput(BaseModel):
    """Output from routing decisions."""

    model_config = {"extra": "forbid"}

    selected_route: str
    reason: str | None = None
    confidence: float | None = None
    data: Any  # Pass through the input data


__all__ = ["RouterInput", "RouterOutput"]
