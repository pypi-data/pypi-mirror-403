from __future__ import annotations

"""Provider-agnostic LLM selection policy DTOs.

These are pure contract models used by higher-level pathways (e.g. Copilot turns)
to pick different models for different phases (planner vs chat vs tools).
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from .config import LLMConfig


class LLMPolicy(BaseModel):
    """Optional per-phase LLM configuration for a single pathway/turn."""

    model_config = ConfigDict(extra="allow")

    chat: LLMConfig | None = Field(
        default=None,
        description="LLM configuration for conversational/planning modes (ask/plan/research).",
    )
    planner: LLMConfig | None = Field(
        default=None,
        description="LLM configuration for edit/planning internals that generate patches.",
    )


@dataclass
class LLMResponse:
    """LLM response."""

    content: str
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = ["LLMPolicy", "LLMResponse"]
