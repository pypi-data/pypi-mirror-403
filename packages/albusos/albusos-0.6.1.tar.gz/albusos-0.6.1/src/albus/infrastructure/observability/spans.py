"""Span contracts for LangSmith-like trace trees.

We persist spans into the existing `StudioRunEvent` append-only log so callers can
reconstruct a hierarchical tree:

run (execution_id)
  pathway (pathway_id)
    node (node_id)
      ... (tool/llm can be added later)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SpanKind(str, Enum):
    RUN = "run"
    PATHWAY = "pathway"
    NODE = "node"
    TOOL = "tool"
    LLM = "llm"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


@dataclass(frozen=True)
class Span:
    """A minimal, JSON-friendly span record.

    Supports full I/O capture for Studio debugging:
    - inputs: Data that went into this span (node inputs, tool args)
    - outputs: Data that came out (node outputs, tool results)

    These are optional and may be truncated for large values.
    """

    span_id: str
    run_id: str
    parent_span_id: str | None
    kind: SpanKind
    name: str
    start_ms: int
    end_ms: int | None = None
    status: SpanStatus = SpanStatus.OK
    error: str | None = None
    attributes: dict[str, Any] | None = None
    # Full I/O capture for debugging
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None


__all__ = ["Span", "SpanKind", "SpanStatus"]
