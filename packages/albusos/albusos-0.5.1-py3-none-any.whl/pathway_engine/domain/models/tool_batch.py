from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pathway_engine.domain.models.agent import AgentToolCall


class ToolBatchInput(BaseModel):
    """Input for executing many tool calls."""

    model_config = {"extra": "forbid"}

    tool_calls: list[AgentToolCall] = Field(default_factory=list)


class ToolBatchOutput(BaseModel):
    """Output from executing many tool calls."""

    model_config = {"extra": "forbid"}

    results: list[dict[str, Any]] = Field(default_factory=list)


__all__ = ["ToolBatchInput", "ToolBatchOutput"]
