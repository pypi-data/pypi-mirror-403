"""Model routing hooks for Pathway Engine.

Pathway Engine (the language/kernel) should not depend on Albus (the built-in agent).
However, product builds often want capability-based model routing (e.g. "reasoning" vs "code_gen").

This module provides a tiny optional plug-in:
  - By default, we use a conservative fallback mapping.
  - Higher layers (e.g. AlbusRuntime) may register a router callable.
"""

from __future__ import annotations

from typing import Callable

ModelRouter = Callable[[str], str | None]

_model_router: ModelRouter | None = None


def set_model_router(router: ModelRouter | None) -> None:
    """Register (or clear) a model router callable.

    The router receives a capability/operation string like:
      - "reasoning", "reasoning.fast", "tool_call", "code_gen", "code_repair", "routing"

    It should return a model name (string) or None to fall back.
    """

    global _model_router
    _model_router = router


def get_default_model(capability: str) -> str:
    """Return the default model for a given capability.

    This function never raises; if routing fails, it returns a safe default.
    """

    if _model_router is not None:
        try:
            model = _model_router(capability)
            if isinstance(model, str) and model.strip():
                return model.strip()
        except Exception:
            # Routing should never break the language/kernel.
            pass

    # Pure fallback mapping (no external deps).
    # Uses local-friendly models as defaults.
    fallback = {
        "reasoning": "llama3.1:8b",
        "reasoning.fast": "qwen2.5:7b",
        "reasoning.deep": "llama3.1:8b",
        "routing": "qwen2.5:7b",
        "tool_call": "qwen2.5:7b",
        "tool_calling": "qwen2.5:7b",
        "code_gen": "qwen2.5-coder:7b",
        "code": "qwen2.5-coder:7b",
        "code_repair": "qwen2.5-coder:7b",
        "classify": "qwen2.5:7b",
        "intent": "qwen2.5:7b",
        "embedding": "text-embedding-3-small",
    }
    return fallback.get(capability, "llama3.1:8b")


__all__ = [
    "ModelRouter",
    "get_default_model",
    "set_model_router",
]
