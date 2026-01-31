from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CodeInput(BaseModel):
    """Input for code execution nodes."""

    model_config = {"extra": "forbid"}

    code: str
    language: Literal["python", "javascript", "bash", "sql"] = "python"
    variables: dict[str, Any] = Field(default_factory=dict)
    timeout: float = 10.0


class CodeOutput(BaseModel):
    """Output from code execution nodes."""

    model_config = {"extra": "forbid"}

    result: Any
    stdout: str | None = None
    stderr: str | None = None
    execution_time_ms: float | None = None
    variables: dict[str, Any] = Field(default_factory=dict)


__all__ = ["CodeInput", "CodeOutput"]
