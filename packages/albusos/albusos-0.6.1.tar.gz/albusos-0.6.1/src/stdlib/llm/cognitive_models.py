"""Model Routing - model selection per operation kind.

Different operations have different requirements:
- reasoning: Needs strong reasoning, context awareness
- routing: Needs speed, structured output (classification/branching)
- tool_call: Needs good tool use, following instructions
- embedding: Uses embedding models
- meta: Lightweight operations (feedback, logging)
- code_gen: Code generation
- code_repair: Error analysis, fixing code
- streaming: Usually doesn't need LLM directly

This module provides recommended model configurations for local and cloud.

Usage:
    from stdlib.llm.cognitive_models import get_model_for_operation
    
    model = get_model_for_operation("reasoning")  # Returns appropriate model
    model = get_model_for_operation("routing", prefer_local=True)  # Prefers local
"""

from __future__ import annotations

import os
from typing import Literal

OperationKind = Literal[
    "reasoning",  # LLM reasoning (was: think)
    "routing",  # Fast classification/branching (was: decide)
    "tool_call",  # Tool execution (was: do)
    "embedding",  # Vector embeddings (was: remember)
    "meta",  # Lightweight meta operations (was: learn)
    "code_gen",  # Code generation (was: code)
    "code_repair",  # Error analysis/fixing (was: debug)
    "streaming",  # No LLM needed (was: observe)
]


# =============================================================================
# MODEL PROFILES
# =============================================================================

# Cloud models (API-based)
CLOUD_MODELS = {
    "reasoning": "gpt-5.2",  # Strong reasoning
    "routing": "gemini-2.5-flash",  # Fast, structured output (sub-100ms)
    "tool_call": "gpt-4o",  # Good tool use
    "embedding": "text-embedding-3-small",
    "meta": "gpt-4o-mini",  # Lightweight
    "code_gen": "claude-3-7-sonnet",  # Code generation (extended thinking)
    "code_repair": "claude-3-7-sonnet",  # Error analysis (needs reasoning)
    "streaming": None,  # No LLM needed
}

# Local models (Ollama)
LOCAL_MODELS = {
    "reasoning": "llama3.1:8b",  # Strong local reasoning
    "routing": "phi3:mini",  # Fast, small
    "tool_call": "llama3.1:8b",  # Good instruction following
    "embedding": None,  # Local embeddings TBD (nomic-embed-text)
    "meta": "phi3:mini",  # Lightweight
    "code_gen": "deepseek-coder:6.7b",  # Code-specialized
    "code_repair": "llama3.1:8b",  # Good at reasoning about errors
    "streaming": None,  # No LLM needed
}

# Fast/cheap models for development/testing
DEV_MODELS = {
    "reasoning": "phi3:mini",
    "routing": "phi3:mini",
    "tool_call": "phi3:mini",
    "embedding": None,
    "meta": "phi3:mini",
    "code_gen": "phi3:mini",
    "code_repair": "phi3:mini",
    "streaming": None,
}


# =============================================================================
# MODEL SELECTION
# =============================================================================


def get_model_for_operation(
    operation: OperationKind,
    *,
    prefer_local: bool | None = None,
    profile: str | None = None,
) -> str | None:
    """Get recommended model for an operation kind.

    Args:
        operation: Operation kind (reasoning, routing, tool_call, etc.)
        prefer_local: If True, prefer local models. If None, uses AGENT_STDLIB_PREFER_LOCAL env.
        profile: Model profile ("cloud", "local", "dev"). If None, auto-selects.

    Returns:
        Model name or None (for operations that don't need LLM)
    """
    # Determine preference
    if prefer_local is None:
        prefer_local = os.getenv("AGENT_STDLIB_PREFER_LOCAL", "").lower() in (
            "1",
            "true",
            "yes",
        )

    # Determine profile
    if profile is None:
        profile_env = os.getenv("AGENT_STDLIB_MODEL_PROFILE", "").lower()
        if profile_env in ("cloud", "local", "dev"):
            profile = profile_env
        elif prefer_local:
            profile = "local"
        else:
            profile = "cloud"

    # Get model from profile
    if profile == "dev":
        return DEV_MODELS.get(operation)
    elif profile == "local":
        return LOCAL_MODELS.get(operation)
    else:
        return CLOUD_MODELS.get(operation)


def get_all_models_for_profile(profile: str = "local") -> dict[str, str | None]:
    """Get all models for a profile."""
    if profile == "dev":
        return dict(DEV_MODELS)
    elif profile == "local":
        return dict(LOCAL_MODELS)
    else:
        return dict(CLOUD_MODELS)


def list_required_local_models() -> list[str]:
    """List all local models needed for full operation coverage."""
    models = set()
    for model in LOCAL_MODELS.values():
        if model:
            models.add(model)
    for model in DEV_MODELS.values():
        if model:
            models.add(model)
    return sorted(models)


# =============================================================================
# OLLAMA SETUP HELPER
# =============================================================================


async def ensure_local_models(
    models: list[str] | None = None,
    verbose: bool = True,
) -> dict[str, bool]:
    """Check which local models are available and which need to be pulled.

    Args:
        models: Models to check. If None, checks all required local models.
        verbose: Print status to stdout.

    Returns:
        Dict of {model: is_available}
    """
    from stdlib.llm.ollama import OllamaAdapter

    if models is None:
        models = list_required_local_models()

    adapter = OllamaAdapter()

    if not await adapter.is_available():
        if verbose:
            print("❌ Ollama is not running. Start it with: ollama serve")
        await adapter.aclose()
        return {m: False for m in models}

    available_models = await adapter.list_models()
    available_names = {m.get("name", "").split(":")[0] for m in available_models}

    result = {}
    for model in models:
        base_name = model.split(":")[0]
        is_available = base_name in available_names
        result[model] = is_available

        if verbose:
            status = "✓" if is_available else "✗ (run: ollama pull " + model + ")"
            print(f"  {model}: {status}")

    await adapter.aclose()
    return result


__all__ = [
    "OperationKind",
    "CLOUD_MODELS",
    "LOCAL_MODELS",
    "DEV_MODELS",
    "get_model_for_operation",
    "get_all_models_for_profile",
    "list_required_local_models",
    "ensure_local_models",
]
