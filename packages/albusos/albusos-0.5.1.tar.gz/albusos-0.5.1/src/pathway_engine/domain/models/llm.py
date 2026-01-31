from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LLMInput(BaseModel):
    """Input for LLM nodes."""

    model_config = {"extra": "forbid"}

    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_output_tokens: int | None = None
    system_prompt: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class LLMOutput(BaseModel):
    """Output from LLM nodes."""

    model_config = {"extra": "forbid"}

    response: str
    model: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["LLMInput", "LLMOutput"]
