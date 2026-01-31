"""Capability-Based Model Routing - Smart model selection for Albus.

Users never pick models. Albus picks the best model for each capability:

    model = get_model_for_capability("code.python")  # → claude-3-5-sonnet
    model = get_model_for_capability("vision.ocr")   # → gpt-4o
    model = get_model_for_capability("speech.asr")   # → whisper-1

Battery Packs:
    - "starter": Minimal viable set (one model handles most things)
    - "balanced": Good quality/cost tradeoff (recommended for production)
    - "premium": Best quality, highest cost
    - "local": Fully local via Ollama

Evaluation:
    - All model calls are logged for performance analysis
    - Use `evaluate_capability_mix()` to compare battery packs

Environment:
    AGENT_STDLIB_BATTERY_PACK: "starter" | "balanced" | "premium" | "local" (default: balanced)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================

Capability = Literal[
    # Code & Math
    "code",
    "code.python",
    "code.typescript",
    "code.review",
    "math",
    "math.symbolic",
    # Reasoning (explicit names)
    "reasoning",
    "reasoning.deep",
    "reasoning.fast",
    "reasoning.philosophical",  # Nuanced reasoning for ethics, epistemology, values
    # Tool Use
    "tool_calling",
    "scripting",
    "json_output",
    # Routing & Classification
    "routing",
    "classify",
    "intent",
    # Vision
    "vision",
    "vision.ocr",
    "vision.diagram",
    "vision.general",
    # Speech/Audio
    "speech.asr",
    "speech.tts",
    "audio.realtime",
    # Memory/Embeddings
    "embed",
    "embed.query",
    "embed.document",
]

BatteryPack = Literal["starter", "balanced", "premium", "local"]


# =============================================================================
# MODEL SPECIFICATIONS
# =============================================================================


@dataclass
class ModelSpec:
    """Specification for a model."""

    provider: str
    model: str
    cost_tier: str = "medium"  # low, medium, high
    capabilities: list[str] = field(default_factory=list)
    notes: str = ""


# Available models (canonical registry)
MODELS = {
    # OpenAI
    "gpt-4o": ModelSpec(
        provider="openai",
        model="gpt-4o",
        cost_tier="high",
        capabilities=["chat", "tools", "json", "vision", "code", "reasoning"],
        notes="Best all-rounder, excellent tool calling",
    ),
    "gpt-4o-mini": ModelSpec(
        provider="openai",
        model="gpt-4o-mini",
        cost_tier="low",
        capabilities=["chat", "tools", "json"],
        notes="Fast and cheap, good for routing/classification",
    ),
    "gpt-5.2": ModelSpec(
        provider="openai",
        model="gpt-5.2",
        cost_tier="high",
        capabilities=["chat", "tools", "json", "code", "reasoning"],
        notes="The new gold standard for general intelligence and logic.",
    ),
    "whisper-1": ModelSpec(
        provider="openai",
        model="whisper-1",
        cost_tier="low",
        capabilities=["audio_in"],
        notes="Best ASR quality",
    ),
    "tts-1": ModelSpec(
        provider="openai",
        model="tts-1",
        cost_tier="low",
        capabilities=["audio_out"],
        notes="Good quality TTS",
    ),
    "text-embedding-3-small": ModelSpec(
        provider="openai",
        model="text-embedding-3-small",
        cost_tier="low",
        capabilities=["embed"],
        notes="Fast, cheap embeddings",
    ),
    # Anthropic
    "claude-3-7-sonnet": ModelSpec(
        provider="anthropic",
        model="claude-3-7-sonnet",
        cost_tier="medium",
        capabilities=["chat", "tools", "json", "code", "reasoning", "vision"],
        notes="Best-in-class reasoning and coding (Extended Thinking).",
    ),
    "claude-3-5-sonnet": ModelSpec(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        cost_tier="medium",
        capabilities=["chat", "tools", "json", "code", "reasoning", "vision"],
        notes="Excellent at code, math, reasoning. Best for complex tasks.",
    ),
    "claude-3-haiku": ModelSpec(
        provider="anthropic",
        model="claude-3-haiku-20240307",
        cost_tier="low",
        capabilities=["chat", "tools", "json"],
        notes="Fast and cheap Anthropic option",
    ),
    # Google
    "gemini-2.5-flash": ModelSpec(
        provider="google",
        model="gemini-2.5-flash",
        cost_tier="low",
        capabilities=["chat", "tools", "json", "vision", "routing"],
        notes="Sub-100ms latency, massive context.",
    ),
    "gemini-1.5-flash": ModelSpec(
        provider="google",
        model="gemini-1.5-flash",
        cost_tier="low",
        capabilities=["chat", "tools", "json", "vision"],
        notes="Very fast, good for routing",
    ),
    "gemini-1.5-pro": ModelSpec(
        provider="google",
        model="gemini-1.5-pro",
        cost_tier="medium",
        capabilities=["chat", "tools", "json", "vision", "code"],
        notes="Long context, good reasoning",
    ),
    # Local (Ollama)
    "llama3.1:8b": ModelSpec(
        provider="ollama",
        model="llama3.1:8b",
        cost_tier="free",
        capabilities=["chat", "tools", "json", "code", "reasoning"],
        notes="Strong local model, good all-rounder",
    ),
    "qwen2.5:7b": ModelSpec(
        provider="ollama",
        model="qwen2.5:7b",
        cost_tier="free",
        capabilities=["chat", "tools", "json", "reasoning"],
        notes="Excellent tool calling and JSON output, fast",
    ),
    "qwen2.5-coder:7b": ModelSpec(
        provider="ollama",
        model="qwen2.5-coder:7b",
        cost_tier="free",
        capabilities=["code", "chat", "json"],
        notes="Best local code generation model",
    ),
    "deepseek-coder:6.7b": ModelSpec(
        provider="ollama",
        model="deepseek-coder:6.7b",
        cost_tier="free",
        capabilities=["code"],
        notes="Code-specialized local model",
    ),
    "phi3:mini": ModelSpec(
        provider="ollama",
        model="phi3:mini",
        cost_tier="free",
        capabilities=["chat", "json"],
        notes="Very fast, small local model",
    ),
    "nomic-embed-text": ModelSpec(
        provider="ollama",
        model="nomic-embed-text",
        cost_tier="free",
        capabilities=["embed"],
        notes="Local embeddings",
    ),
}


# =============================================================================
# BATTERY PACKS - Pre-configured model mixes
# =============================================================================

# Starter: Single model handles everything (simplest)
BATTERY_STARTER = {
    # Everything goes to GPT-4o-mini (cheap, decent quality)
    "code": "gpt-4o-mini",
    "code.python": "gpt-4o-mini",
    "code.typescript": "gpt-4o-mini",
    "code.review": "gpt-4o-mini",
    "math": "gpt-4o-mini",
    "math.symbolic": "gpt-4o-mini",
    "reasoning": "gpt-4o-mini",
    "reasoning.deep": "gpt-4o-mini",
    "reasoning.fast": "gpt-4o-mini",
    "reasoning.philosophical": "gpt-4o-mini",
    "tool_calling": "gpt-4o-mini",
    "scripting": "gpt-4o-mini",
    "json_output": "gpt-4o-mini",
    "routing": "gpt-4o-mini",
    "classify": "gpt-4o-mini",
    "intent": "gpt-4o-mini",
    "vision": "gpt-4o",  # Mini doesn't have vision
    "vision.ocr": "gpt-4o",
    "vision.diagram": "gpt-4o",
    "vision.general": "gpt-4o",
    "speech.asr": "whisper-1",
    "speech.tts": "tts-1",
    "audio.realtime": "gpt-4o",
    "embed": "text-embedding-3-small",
    "embed.query": "text-embedding-3-small",
    "embed.document": "text-embedding-3-small",
}

# Balanced: Best quality/cost tradeoff (recommended)
BATTERY_BALANCED = {
    # Code & Math: Claude excels
    "code": "claude-3-7-sonnet",
    "code.python": "claude-3-7-sonnet",
    "code.typescript": "claude-3-7-sonnet",
    "code.review": "claude-3-7-sonnet",
    "math": "claude-3-7-sonnet",
    "math.symbolic": "claude-3-7-sonnet",
    # Reasoning: GPT-5.2 for general logic, Claude 3.7 for deep/philosophical
    "reasoning": "gpt-5.2",
    "reasoning.deep": "claude-3-7-sonnet",
    "reasoning.fast": "gemini-2.5-flash",
    "reasoning.philosophical": "claude-3-7-sonnet",  # Best at nuance, ethics, epistemology
    # Tool calling: OpenAI excels
    "tool_calling": "gpt-4o",
    "scripting": "gpt-4o",
    "json_output": "gpt-4o",
    # Routing: Fast and cheap
    "routing": "gemini-2.5-flash",
    "classify": "gemini-2.5-flash",
    "intent": "gemini-2.5-flash",
    # Vision: Claude for diagrams, GPT-4o for OCR
    "vision": "claude-3-7-sonnet",
    "vision.ocr": "gpt-4o",
    "vision.diagram": "claude-3-7-sonnet",
    "vision.general": "gpt-5.2",
    # Speech: OpenAI only
    "speech.asr": "whisper-1",
    "speech.tts": "tts-1",
    "audio.realtime": "gpt-4o",
    # Embeddings
    "embed": "text-embedding-3-small",
    "embed.query": "text-embedding-3-small",
    "embed.document": "text-embedding-3-small",
}

# Premium: Best quality, highest cost
BATTERY_PREMIUM = {
    # Code & Math: Claude
    "code": "claude-3-5-sonnet",
    "code.python": "claude-3-5-sonnet",
    "code.typescript": "claude-3-5-sonnet",
    "code.review": "claude-3-5-sonnet",
    "math": "claude-3-5-sonnet",
    "math.symbolic": "claude-3-5-sonnet",
    # Reasoning: Claude for everything
    "reasoning": "claude-3-5-sonnet",
    "reasoning.deep": "claude-3-5-sonnet",
    "reasoning.fast": "gpt-4o",
    "reasoning.philosophical": "claude-3-5-sonnet",
    # Tool calling: GPT-4o
    "tool_calling": "gpt-4o",
    "scripting": "gpt-4o",
    "json_output": "gpt-4o",
    # Routing: Still cheap
    "routing": "gpt-4o-mini",
    "classify": "gpt-4o-mini",
    "intent": "gpt-4o",
    # Vision: Claude
    "vision": "claude-3-5-sonnet",
    "vision.ocr": "gpt-4o",
    "vision.diagram": "claude-3-5-sonnet",
    "vision.general": "claude-3-5-sonnet",
    # Speech
    "speech.asr": "whisper-1",
    "speech.tts": "tts-1",
    "audio.realtime": "gpt-4o",
    # Embeddings
    "embed": "text-embedding-3-small",
    "embed.query": "text-embedding-3-small",
    "embed.document": "text-embedding-3-small",
}

# Local: Fully local via Ollama
# Optimized for Qwen 2.5 + Llama 3.1 (commonly available local models)
BATTERY_LOCAL = {
    # Code: Qwen 2.5 Coder (excellent for code tasks)
    "code": "qwen2.5-coder:7b",
    "code.python": "qwen2.5-coder:7b",
    "code.typescript": "qwen2.5-coder:7b",
    "code.review": "qwen2.5-coder:7b",
    "math": "qwen2.5:7b",
    "math.symbolic": "qwen2.5:7b",
    # Reasoning: Llama 3.1 for deep reasoning, Qwen for fast
    "reasoning": "llama3.1:8b",
    "reasoning.deep": "llama3.1:8b",
    "reasoning.fast": "qwen2.5:7b",
    "reasoning.philosophical": "llama3.1:8b",
    # Tool calling: Qwen 2.5 (good tool calling support)
    "tool_calling": "qwen2.5:7b",
    "scripting": "qwen2.5:7b",
    "json_output": "qwen2.5:7b",
    # Routing: Qwen (fast, good at classification)
    "routing": "qwen2.5:7b",
    "classify": "qwen2.5:7b",
    "intent": "qwen2.5:7b",
    # Vision: Not available locally (fallback to cloud)
    "vision": None,  # Will need cloud fallback
    "vision.ocr": None,
    "vision.diagram": None,
    "vision.general": None,
    # Speech: Not available locally
    "speech.asr": None,
    "speech.tts": None,
    "audio.realtime": None,
    # Embeddings: Nomic
    "embed": "nomic-embed-text",
    "embed.query": "nomic-embed-text",
    "embed.document": "nomic-embed-text",
}

BATTERY_PACKS = {
    "starter": BATTERY_STARTER,
    "balanced": BATTERY_BALANCED,
    "premium": BATTERY_PREMIUM,
    "local": BATTERY_LOCAL,
}


# =============================================================================
# CAPABILITY ROUTING
# =============================================================================

# Runtime overrides (set by AlbusRuntime from deployment config)
_runtime_profile: str | None = None
_runtime_overrides: dict[str, str] = {}


def set_runtime_model_config(
    *,
    default_profile: str | None = None,
    routing: dict[str, str] | None = None,
) -> None:
    """Set runtime model routing config (called by AlbusRuntime at boot).

    Args:
        default_profile: Battery pack to use ("local", "balanced", etc.)
        routing: Capability → model overrides
    """
    global _runtime_profile, _runtime_overrides
    if default_profile is not None:
        _runtime_profile = default_profile
        logger.debug("Model routing: default_profile=%s", default_profile)
    if routing is not None:
        _runtime_overrides = dict(routing)
        if routing:
            logger.debug("Model routing: %d overrides configured", len(routing))


def get_runtime_model_config() -> dict[str, Any]:
    """Get current runtime model config (for API inspection)."""
    return {
        "default_profile": _runtime_profile or get_battery_pack(),
        "routing": dict(_runtime_overrides),
        "effective_profile": _runtime_profile or os.getenv("AGENT_STDLIB_BATTERY_PACK", "balanced"),
    }


def get_battery_pack() -> BatteryPack:
    """Get current battery pack from runtime config or environment."""
    # Runtime config takes precedence
    if _runtime_profile and _runtime_profile in BATTERY_PACKS:
        return _runtime_profile  # type: ignore

    pack = os.getenv("AGENT_STDLIB_BATTERY_PACK", "balanced").lower()
    if pack in BATTERY_PACKS:
        return pack  # type: ignore
    return "balanced"


def get_model_for_capability(
    capability: str,
    *,
    battery_pack: BatteryPack | None = None,
    fallback: str | None = None,
    agent_overrides: dict[str, str] | None = None,
) -> str | None:
    """Get the best model for a capability.

    Resolution order:
    1. agent_overrides (per-agent config)
    2. _runtime_overrides (from albus.yaml models.routing)
    3. battery_pack routes
    4. fallback

    Args:
        capability: What you need to do (e.g., "code.python", "vision.ocr")
        battery_pack: Override battery pack (default: from runtime/env)
        fallback: Model to use if capability not found
        agent_overrides: Per-agent model overrides (highest priority)

    Returns:
        Model name or None (for unavailable capabilities)

    Examples:
        model = get_model_for_capability("code.python")  # → claude-3-5-sonnet
        model = get_model_for_capability("vision.ocr")   # → gpt-4o
        model = get_model_for_capability("speech.asr")   # → whisper-1
    """
    # 1. Check agent-level overrides first
    if agent_overrides:
        model = agent_overrides.get(capability)
        if model:
            return model
        # Check parent capability
        if "." in capability:
            parent = capability.rsplit(".", 1)[0]
            model = agent_overrides.get(parent)
            if model:
                return model

    # 2. Check runtime overrides (from albus.yaml)
    if _runtime_overrides:
        model = _runtime_overrides.get(capability)
        if model:
            return model
        if "." in capability:
            parent = capability.rsplit(".", 1)[0]
            model = _runtime_overrides.get(parent)
            if model:
                return model

    # 3. Check battery pack routes
    pack = battery_pack or get_battery_pack()
    routes = BATTERY_PACKS.get(pack, BATTERY_BALANCED)

    # Try exact match first
    model = routes.get(capability)
    if model:
        return model

    # Try parent capability (e.g., "code.python" → "code")
    if "." in capability:
        parent = capability.rsplit(".", 1)[0]
        model = routes.get(parent)
        if model:
            return model

    # 4. Check for explicit "default" in runtime overrides
    if _runtime_overrides:
        default_model = _runtime_overrides.get("default")
        if default_model:
            return default_model

    # 5. User-provided fallback
    if fallback:
        return fallback

    # 6. Battery pack default or reasoning.fast
    pack_fallback = routes.get("default") or routes.get("reasoning.fast")
    if pack_fallback:
        return pack_fallback

    # Ultimate fallback - prefer local if profile is local
    if pack == "local":
        return "llama3.1:8b"
    return "gpt-4o-mini"


def get_model_spec(model_key: str) -> ModelSpec | None:
    """Get full specification for a model."""
    return MODELS.get(model_key)


def get_provider_for_model(model_key: str) -> str:
    """Get provider for a model key."""
    spec = MODELS.get(model_key)
    if spec:
        return spec.provider

    # Infer from model name
    if model_key.startswith(("gpt-", "o1", "whisper", "tts", "text-embedding")):
        return "openai"
    elif model_key.startswith("claude"):
        return "anthropic"
    elif model_key.startswith("gemini"):
        return "google"
    else:
        return "ollama"


def get_full_model_name(model_key: str) -> str:
    """Get full model name (for API calls)."""
    spec = MODELS.get(model_key)
    if spec:
        return spec.model
    return model_key


# =============================================================================
# CAPABILITY → INTERNAL OPERATION MAPPING
# =============================================================================

# Map capabilities to internal operation kinds (explicit names)
# See cognitive_models.py for operation kinds: reasoning, routing, tool_call, embedding, etc.
CAPABILITY_TO_OPERATION = {
    "code": "code_gen",
    "code.python": "code_gen",
    "code.typescript": "code_gen",
    "code.review": "code_gen",
    "math": "reasoning",
    "math.symbolic": "reasoning",
    "reasoning": "reasoning",
    "reasoning.deep": "reasoning",
    "reasoning.fast": "routing",
    "reasoning.philosophical": "reasoning",
    "tool_calling": "tool_call",
    "scripting": "tool_call",
    "json_output": "reasoning",
    "routing": "routing",
    "classify": "routing",
    "intent": "routing",
    "vision": "streaming",
    "vision.ocr": "streaming",
    "vision.diagram": "streaming",
    "vision.general": "streaming",
    "speech.asr": "streaming",
    "speech.tts": "tool_call",
    "audio.realtime": "tool_call",
    "embed": "embedding",
    "embed.query": "embedding",
    "embed.document": "embedding",
}


def get_operation_for_capability(capability: str) -> str:
    """Map capability to internal operation kind."""
    op = CAPABILITY_TO_OPERATION.get(capability)
    if op:
        return op

    # Infer from prefix
    if capability.startswith("code"):
        return "code_gen"
    elif capability.startswith("reasoning"):
        return "reasoning"
    elif capability.startswith("vision") or capability.startswith("speech"):
        return "streaming"
    elif capability.startswith("embed"):
        return "embedding"

    return "reasoning"  # Default


# =============================================================================
# EVALUATION & LOGGING
# =============================================================================


@dataclass
class ModelCallLog:
    """Log entry for a model call (for evaluation)."""

    timestamp: float
    capability: str
    model: str
    provider: str
    battery_pack: str
    latency_ms: float
    success: bool
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None


# In-memory log (for evaluation sessions)
_CALL_LOG: list[ModelCallLog] = []
_LOGGING_ENABLED = os.getenv("AGENT_STDLIB_MODEL_LOGGING", "").lower() in (
    "1",
    "true",
    "yes",
)


def enable_model_logging(enabled: bool = True) -> None:
    """Enable/disable model call logging."""
    global _LOGGING_ENABLED
    _LOGGING_ENABLED = enabled


def log_model_call(
    capability: str,
    model: str,
    latency_ms: float,
    success: bool,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    error: str | None = None,
) -> None:
    """Log a model call for evaluation."""
    if not _LOGGING_ENABLED:
        return

    spec = MODELS.get(model)
    provider = spec.provider if spec else get_provider_for_model(model)

    entry = ModelCallLog(
        timestamp=time.time(),
        capability=capability,
        model=model,
        provider=provider,
        battery_pack=get_battery_pack(),
        latency_ms=latency_ms,
        success=success,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        error=error,
    )
    _CALL_LOG.append(entry)


def get_call_log() -> list[ModelCallLog]:
    """Get the model call log."""
    return list(_CALL_LOG)


def clear_call_log() -> None:
    """Clear the call log."""
    _CALL_LOG.clear()


def summarize_calls() -> dict[str, Any]:
    """Summarize model calls by capability and model."""
    if not _CALL_LOG:
        return {"total_calls": 0, "by_capability": {}, "by_model": {}}

    by_capability: dict[str, dict[str, Any]] = {}
    by_model: dict[str, dict[str, Any]] = {}

    for entry in _CALL_LOG:
        # By capability
        if entry.capability not in by_capability:
            by_capability[entry.capability] = {
                "count": 0,
                "success": 0,
                "total_latency_ms": 0,
                "total_cost_usd": 0,
            }
        by_capability[entry.capability]["count"] += 1
        by_capability[entry.capability]["success"] += int(entry.success)
        by_capability[entry.capability]["total_latency_ms"] += entry.latency_ms
        by_capability[entry.capability]["total_cost_usd"] += entry.cost_usd

        # By model
        if entry.model not in by_model:
            by_model[entry.model] = {
                "count": 0,
                "success": 0,
                "total_latency_ms": 0,
                "total_cost_usd": 0,
            }
        by_model[entry.model]["count"] += 1
        by_model[entry.model]["success"] += int(entry.success)
        by_model[entry.model]["total_latency_ms"] += entry.latency_ms
        by_model[entry.model]["total_cost_usd"] += entry.cost_usd

    # Compute averages
    for stats in by_capability.values():
        if stats["count"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["count"]
            stats["success_rate"] = stats["success"] / stats["count"]

    for stats in by_model.values():
        if stats["count"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["count"]
            stats["success_rate"] = stats["success"] / stats["count"]

    return {
        "total_calls": len(_CALL_LOG),
        "by_capability": by_capability,
        "by_model": by_model,
    }


# =============================================================================
# BATTERY PACK HELPERS
# =============================================================================


def list_required_models(battery_pack: BatteryPack | None = None) -> list[str]:
    """List all models required for a battery pack."""
    pack = battery_pack or get_battery_pack()
    routes = BATTERY_PACKS.get(pack, BATTERY_BALANCED)

    models = set()
    for model in routes.values():
        if model:
            models.add(model)

    return sorted(models)


def list_required_providers(battery_pack: BatteryPack | None = None) -> list[str]:
    """List all providers required for a battery pack."""
    models = list_required_models(battery_pack)
    providers = set()
    for model in models:
        providers.add(get_provider_for_model(model))
    return sorted(providers)


def describe_battery_pack(battery_pack: BatteryPack | None = None) -> str:
    """Get human-readable description of a battery pack."""
    pack = battery_pack or get_battery_pack()

    descriptions = {
        "starter": "Minimal: GPT-4o-mini handles most tasks. Cheap, decent quality.",
        "balanced": "Recommended (2026): Claude 3.7 (Code), GPT-5.2 (Brain), Gemini 2.5 (Speed).",
        "premium": "Best quality: Claude for reasoning, GPT-4o for tools. Highest cost.",
        "local": "Fully local: Ollama models (Llama, DeepSeek, Phi). No cloud dependency.",
    }

    return descriptions.get(pack, f"Unknown pack: {pack}")


async def check_battery_pack_availability(
    battery_pack: BatteryPack | None = None,
    verbose: bool = True,
) -> dict[str, bool]:
    """Check if all models for a battery pack are available.

    Returns dict of {model: is_available}.
    """
    models = list_required_models(battery_pack)
    result: dict[str, bool] = {}

    # Check Ollama models
    ollama_models = [m for m in models if get_provider_for_model(m) == "ollama"]
    if ollama_models:
        try:
            from stdlib.llm.ollama import OllamaAdapter

            adapter = OllamaAdapter()

            if await adapter.is_available():
                available = await adapter.list_models()
                available_names = {m.get("name", "").split(":")[0] for m in available}

                for model in ollama_models:
                    base_name = model.split(":")[0]
                    is_available = base_name in available_names
                    result[model] = is_available
                    if verbose:
                        status = (
                            "✓" if is_available else f"✗ (run: ollama pull {model})"
                        )
                        print(f"  {model}: {status}")
            else:
                for model in ollama_models:
                    result[model] = False
                if verbose:
                    print("  ❌ Ollama is not running (start with: ollama serve)")

            await adapter.aclose()
        except Exception as e:
            for model in ollama_models:
                result[model] = False
            if verbose:
                print(f"  ❌ Ollama error: {e}")

    # Check cloud providers (just check API keys)
    cloud_models = [m for m in models if get_provider_for_model(m) != "ollama"]
    for model in cloud_models:
        provider = get_provider_for_model(model)

        if provider == "openai":
            available = bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "anthropic":
            available = bool(os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "google":
            available = bool(os.getenv("GOOGLE_API_KEY"))
        else:
            available = True  # Assume available

        result[model] = available
        if verbose:
            status = "✓" if available else f"✗ (set {provider.upper()}_API_KEY)"
            print(f"  {model}: {status}")

    return result


__all__ = [
    # Types
    "Capability",
    "BatteryPack",
    "ModelSpec",
    "ModelCallLog",
    # Model registry
    "MODELS",
    "BATTERY_PACKS",
    # Core routing
    "get_battery_pack",
    "get_model_for_capability",
    "get_model_spec",
    "get_provider_for_model",
    "get_full_model_name",
    # Runtime config
    "set_runtime_model_config",
    "get_runtime_model_config",
    # Operation mapping
    "CAPABILITY_TO_OPERATION",
    "get_operation_for_capability",
    # Logging/evaluation
    "enable_model_logging",
    "log_model_call",
    "get_call_log",
    "clear_call_log",
    "summarize_calls",
    # Battery pack helpers
    "list_required_models",
    "list_required_providers",
    "describe_battery_pack",
    "check_battery_pack_availability",
]
