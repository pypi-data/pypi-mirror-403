"""Tool DTOs - data shapes for tool calling.

Defines the shape of tool requests and results.
Nodes import these; they don't define their own.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool call request."""

    model_config = {"extra": "forbid"}

    id: str = Field(description="Unique call ID for correlation")
    tool: str = Field(description="Tool name (e.g., 'pathway.create')")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolResult(BaseModel):
    """Result of a tool call."""

    model_config = {"extra": "forbid"}

    call_id: str = Field(description="ID of the corresponding ToolCall")
    tool: str = Field(description="Tool that was called")
    success: bool = Field(default=True)
    output: Any = Field(default=None, description="Tool output")
    error: str | None = Field(default=None, description="Error message if failed")


class ToolCallPlan(BaseModel):
    """Plan containing multiple tool calls."""

    model_config = {"extra": "forbid"}

    calls: list[ToolCall] = Field(default_factory=list)
    reasoning: str | None = Field(
        default=None, description="Why these tools are needed"
    )


class ToolExecutionResult(BaseModel):
    """Results of executing a tool plan."""

    model_config = {"extra": "forbid"}

    results: list[ToolResult] = Field(default_factory=list)
    all_succeeded: bool = Field(default=True)
    summary: str | None = Field(default=None)


__all__ = [
    "ToolCall",
    "ToolResult",
    "ToolCallPlan",
    "ToolExecutionResult",
]
