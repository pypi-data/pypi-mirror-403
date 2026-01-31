"""Execution DTOs - contracts for pathway execution.

These are the data types that describe execution state and results.
The actual execution happens in pathway_engine.vm.PathwayVM.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from pathway_engine.domain.context import Context


class PathwayStatus(Enum):
    """Status of a pathway execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class PathwayEvent(BaseModel):
    """An event that occurred during execution."""

    model_config = {"extra": "allow"}

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    node_id: str | None = None
    pathway_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class PathwayMetrics(BaseModel):
    """Metrics collected during execution."""

    model_config = {"extra": "allow"}

    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: float | None = None
    nodes_executed: int = 0
    nodes_succeeded: int = 0
    nodes_failed: int = 0
    nodes_skipped: int = 0


class PathwayRecord(BaseModel):
    """Record of a pathway execution."""

    model_config = {"extra": "allow"}

    id: str
    pathway_id: str
    status: PathwayStatus = PathwayStatus.PENDING
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    context: Context | None = None
    events: list[PathwayEvent] = Field(default_factory=list)
    metrics: PathwayMetrics = Field(default_factory=PathwayMetrics)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # Learning results, etc.

    @property
    def success(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == PathwayStatus.COMPLETED


__all__ = [
    "PathwayStatus",
    "PathwayEvent",
    "PathwayMetrics",
    "PathwayRecord",
]
