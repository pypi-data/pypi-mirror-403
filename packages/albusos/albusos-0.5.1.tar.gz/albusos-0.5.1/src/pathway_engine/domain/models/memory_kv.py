from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MemoryReadInput(BaseModel):
    """Input for memory read operations."""

    model_config = {"extra": "forbid"}

    key: str
    namespace: str = "default"
    default: Any = None


class MemoryReadOutput(BaseModel):
    """Output from memory read operations."""

    model_config = {"extra": "forbid"}

    value: Any
    key: str
    found: bool
    namespace: str


class MemoryWriteInput(BaseModel):
    """Input for memory write operations."""

    model_config = {"extra": "forbid"}

    key: str
    value: Any
    namespace: str = "default"
    ttl_seconds: int | None = None


class MemoryWriteOutput(BaseModel):
    """Output from memory write operations."""

    model_config = {"extra": "forbid"}

    key: str
    written: bool
    namespace: str
    previous_value: Any = None


class MemoryDeleteInput(BaseModel):
    """Input for memory delete operations."""

    model_config = {"extra": "forbid"}

    key: str
    namespace: str = "default"


class MemoryDeleteOutput(BaseModel):
    """Output from memory delete operations."""

    model_config = {"extra": "forbid"}

    key: str
    namespace: str
    deleted: bool


__all__ = [
    "MemoryDeleteInput",
    "MemoryDeleteOutput",
    "MemoryReadInput",
    "MemoryReadOutput",
    "MemoryWriteInput",
    "MemoryWriteOutput",
]
