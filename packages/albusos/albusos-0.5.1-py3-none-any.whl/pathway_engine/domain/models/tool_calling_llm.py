from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCallingLLMOutput(BaseModel):
    """Output from tool-calling LLM step."""

    model_config = {"extra": "forbid"}

    class ToolCallTrace(BaseModel):
        model_config = {"extra": "forbid"}

        round: int
        tool_name: str
        tool_call_id: str | None = None
        parameters: dict[str, Any] = Field(default_factory=dict)
        ok: bool
        result: Any | None = None
        error: str | None = None
        latency_ms: float | None = None

    response: str
    model: str | None = None
    rounds: int = 1
    tool_trace: list[ToolCallTrace] = Field(default_factory=list)
    error: str | None = None


__all__ = ["ToolCallingLLMOutput"]
