from __future__ import annotations

from enum import Enum


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


__all__ = ["ModelProvider"]
