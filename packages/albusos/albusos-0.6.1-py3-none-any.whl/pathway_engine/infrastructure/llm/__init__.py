from __future__ import annotations

"""LLM configuration and function capability models (contracts-only).

Also includes small DTOs used by the runtime LLM port boundary (no SDK deps).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

from .attachments import LLMAttachment
from .config import LlmCallConfig, LLMConfig
from .enums import ModelProvider
from .request import LLMRequest
from .tools import LLMTool, ToolChoice


class ModelCapability(Enum):
    """Model capabilities."""

    CHAT = "chat"
    TOOLS = "tools"
    JSON = "json"
    VISION = "vision"
    CODE = "code"
    REASONING = "reasoning"
    AUDIO_IN = "audio_in"
    AUDIO_OUT = "audio_out"


@dataclass
class LLMResponse:
    """LLM response."""

    content: str
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "ModelCapability",
    "ModelProvider",
    "LLMResponse",
    "LLMRequest",
    "LLMConfig",
    "LlmCallConfig",
    "LLMTool",
    "ToolChoice",
    "LLMAttachment",
]
