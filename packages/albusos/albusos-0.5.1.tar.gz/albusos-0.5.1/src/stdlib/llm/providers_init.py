"""LLM Provider Adapters - Private implementation details for llm tools.

These adapters wrap external SDKs (OpenAI, Anthropic, Google) and are
called exclusively by the llm.* tools. They are NOT exposed publicly.

Architecture:
- Adapters are stateless where possible
- All cross-cutting concerns (retry, audit, policy) are in the tools layer
- Adapters translate: LLM tool inputs → SDK calls → normalized outputs
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Errors
# =============================================================================


class LLMProviderError(RuntimeError):
    """Normalized provider error."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: Optional[str] = None,
        is_transient: bool = False,
    ):
        self.message = message
        self.provider = provider
        self.model = model
        self.is_transient = is_transient
        super().__init__(f"{provider}: {message}")


# =============================================================================
# Response DTO
# =============================================================================


@dataclass
class LLMGenerateResult:
    """Normalized result from LLM generation."""

    content: str
    model: str
    tokens_used: int
    cost_usd: float
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "unknown"
    finish_reason: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: dict[str, Any] | None = None


@dataclass
class LLMEmbedResult:
    """Normalized result from embedding generation."""

    vectors: list[list[float]]
    model: str
    tokens_used: int
    cost_usd: float
    provider: str = "unknown"


# =============================================================================
# Provider Registry
# =============================================================================

_PROVIDERS: dict[str, Any] = {}
_INITIALIZED = False


def _init_providers() -> None:
    """Lazily initialize providers from environment."""
    global _INITIALIZED, _PROVIDERS

    if _INITIALIZED:
        return

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    if openai_key:
        from stdlib.llm.openai import OpenAIAdapter

        _PROVIDERS["openai"] = OpenAIAdapter(api_key=openai_key)
        logger.debug("Initialized OpenAI adapter")

    if anthropic_key:
        from stdlib.llm.anthropic import AnthropicAdapter

        _PROVIDERS["anthropic"] = AnthropicAdapter(api_key=anthropic_key)
        logger.debug("Initialized Anthropic adapter")

    if google_key:
        try:
            from stdlib.llm.google import GoogleAdapter

            _PROVIDERS["google"] = GoogleAdapter(api_key=google_key)
            logger.debug("Initialized Google adapter")
        except ImportError:
            logger.debug("Google SDK not installed, skipping")

    # Always register Ollama (it will fail gracefully if not running)
    from stdlib.llm.ollama import OllamaAdapter

    _PROVIDERS["ollama"] = OllamaAdapter(host=ollama_host)
    logger.debug("Initialized Ollama adapter (host=%s)", ollama_host)

    _INITIALIZED = True


def get_provider(model: str) -> Any:
    """Get the appropriate provider for a model.

    Args:
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022", "llama3", "ollama:mistral")

    Returns:
        Provider adapter instance

    Raises:
        LLMProviderError: If no provider available for model
    """
    _init_providers()

    model_lower = model.lower()

    # Route by model prefix
    #
    # Note: Speech models are OpenAI-only in this repo today:
    # - ASR: whisper-*
    # - TTS: tts-*
    if model_lower.startswith(("gpt-", "o1", "text-embedding", "whisper", "tts-")):
        if "openai" in _PROVIDERS:
            return _PROVIDERS["openai"]
        raise LLMProviderError(
            message=(
                f"OPENAI_API_KEY is not set, but model '{model}' requires OpenAI. "
                "Either set OPENAI_API_KEY (cloud), or use free local models by setting "
                "AGENT_STDLIB_BATTERY_PACK=local and running Ollama (ollama serve)."
            ),
            provider="openai",
            model=model,
            is_transient=False,
        )
    elif model_lower.startswith("claude"):
        if "anthropic" in _PROVIDERS:
            return _PROVIDERS["anthropic"]
        raise LLMProviderError(
            message=(
                f"ANTHROPIC_API_KEY is not set, but model '{model}' requires Anthropic. "
                "Either set ANTHROPIC_API_KEY (cloud), or use free local models by setting "
                "AGENT_STDLIB_BATTERY_PACK=local and running Ollama (ollama serve)."
            ),
            provider="anthropic",
            model=model,
            is_transient=False,
        )
    elif model_lower.startswith("gemini"):
        if "google" in _PROVIDERS:
            return _PROVIDERS["google"]
        raise LLMProviderError(
            message=(
                f"GOOGLE_API_KEY is not set, but model '{model}' requires Google. "
                "Either set GOOGLE_API_KEY (cloud), or use free local models by setting "
                "AGENT_STDLIB_BATTERY_PACK=local and running Ollama (ollama serve)."
            ),
            provider="google",
            model=model,
            is_transient=False,
        )

    # Local models via Ollama
    from stdlib.llm.ollama import is_ollama_model

    if is_ollama_model(model_lower):
        if "ollama" in _PROVIDERS:
            return _PROVIDERS["ollama"]

    # Fallback: only use OpenAI if configured; only use Ollama for Ollama-like model names.
    if "openai" in _PROVIDERS:
        return _PROVIDERS["openai"]

    if "ollama" in _PROVIDERS:
        raise LLMProviderError(
            message=(
                f"Model '{model}' does not look like an Ollama model name. "
                "If you're trying to run locally, set AGENT_STDLIB_BATTERY_PACK=local "
                "so the system selects local models (e.g. llama3.1:8b, phi3:mini)."
            ),
            provider="ollama",
            model=model,
            is_transient=False,
        )

    raise LLMProviderError(
        message="No LLM providers configured. Set OPENAI_API_KEY or run Ollama (ollama serve).",
        provider="none",
        model=model,
        is_transient=False,
    )


def list_available_providers() -> list[str]:
    """List configured provider names."""
    _init_providers()
    return list(_PROVIDERS.keys())


async def close_all_providers() -> None:
    """Close all provider connections (cleanup)."""
    for provider in _PROVIDERS.values():
        if hasattr(provider, "aclose"):
            try:
                await provider.aclose()
            except Exception:
                pass


__all__ = [
    "LLMProviderError",
    "LLMGenerateResult",
    "LLMEmbedResult",
    "get_provider",
    "list_available_providers",
    "close_all_providers",
]
