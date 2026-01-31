from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentToolCall(BaseModel):
    """A single tool call requested by the agent planner."""

    model_config = {"extra": "forbid"}

    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout: float | None = None


class AgentPlanInput(BaseModel):
    """Input to the agent planner step."""

    model_config = {"extra": "forbid"}

    message: str
    retrieved_memory: str = ""
    canvas_context: str = ""
    user_approved_tools: bool = False
    # Optional: caller-provided tool listing. If missing, the planner step may build its own.
    available_tools: str = ""


class AgentPlanOutput(BaseModel):
    """Planner output: either respond directly or call tools first."""

    model_config = {"extra": "forbid"}

    action: str = "respond"  # respond | propose_tool_calls | call_tools
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    notes: str | None = None


class AgentPlanJsonV1(BaseModel):
    """Strict JSON contract for the planner LLM output.

    This is intentionally narrower than `AgentPlanOutput`:
    - `action` is constrained to a small enum
    - extra keys are forbidden
    """

    model_config = {"extra": "forbid"}

    action: Literal["respond", "propose_tool_calls", "call_tools"] = "respond"
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    notes: str | None = None


__all__ = ["AgentPlanInput", "AgentPlanJsonV1", "AgentPlanOutput", "AgentToolCall"]
