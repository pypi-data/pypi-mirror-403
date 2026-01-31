from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GenericInput(BaseModel):
    """Generic input when you don't need specific typing."""

    model_config = {"extra": "allow"}  # Allow any fields

    data: Any = None


class GenericOutput(BaseModel):
    """Generic output when you don't need specific typing."""

    model_config = {"extra": "allow"}  # Allow any fields

    data: Any = None


__all__ = ["GenericInput", "GenericOutput"]
