"""Cross-layer error types.

These exceptions are used at boundaries (Studio domain, host adapters, tools) to
communicate stable failure modes without importing implementation modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class StudioError(Exception):
    """Base error for Studio domain operations."""

    message: str = "studio_error"

    def __str__(self) -> str:  # pragma: no cover
        return str(self.message or self.__class__.__name__)


@dataclass
class StudioNotFound(StudioError):
    """Entity not found (workspace/folder/document/revision)."""

    message: str = "not_found"


@dataclass
class StudioValidationError(StudioError):
    """Input/content validation failed."""

    message: str = "validation_error"


@dataclass
class StudioConflict(StudioError):
    """Conflict (typically optimistic concurrency / base revision mismatch)."""

    message: str = "conflict"
    doc_id: Optional[str] = None
    base_rev: Optional[str] = None
    head_rev: Optional[str] = None
    head_content: Any | None = None
    conflict_code: Optional[str] = None


__all__ = [
    "StudioError",
    "StudioNotFound",
    "StudioValidationError",
    "StudioConflict",
]
