"""LLM Tools - Atomic capabilities for language model operations.

These tools wrap LLM provider adapters and provide the interface that
pathways and nodes use to generate text, embeddings, etc.

Tools:
- llm.generate: Generate text using an LLM
- llm.embed: Generate embeddings for text
- llm.complete: Simple text completion (convenience wrapper)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext

from stdlib.llm import (
    LLMProviderError,
    get_provider,
    list_available_providers,
)
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool(
    "llm.generate",
    description="Generate text using an LLM. Supports chat, JSON output, tool calling, and vision.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user prompt/question",
            },
            "model": {
                "type": "string",
                "description": "Model to use. 'auto' uses capability routing. Explicit names (gpt-4o, qwen2.5:7b) are used directly.",
            },
            "capability": {
                "type": "string",
                "description": "Capability hint for 'auto' model selection (reasoning, tool_calling, code, vision, etc.)",
            },
            "system": {
                "type": "string",
                "description": "System prompt to set context/behavior",
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-2). Default: 0.7",
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens to generate. Default: 1200",
            },
            "response_format": {
                "type": "string",
                "enum": ["text", "json"],
                "description": "Output format. Default: text",
            },
            "messages": {
                "type": "array",
                "description": "Full conversation history (overrides prompt/system)",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                    },
                },
            },
            "tools": {
                "type": "array",
                "description": "Tool definitions for function calling",
                "items": {"type": "object"},
            },
            "tool_choice": {
                "type": ["string", "object"],
                "description": "Tool choice: 'auto', 'none', or specific tool name",
            },
            "images": {
                "type": "array",
                "description": "List of base64-encoded images for vision models (gpt-4o, claude-3, etc.)",
                "items": {"type": "string"},
            },
        },
        "required": ["prompt"],
    },
)
async def llm_generate(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Generate text using an LLM.

    This is the primary LLM tool. It handles:
    - Multi-provider routing (OpenAI, Anthropic, Google)
    - JSON mode with validation
    - Tool/function calling
    - Cost tracking

    Returns:
        {
            "content": str,           # Generated text
            "model": str,             # Model used
            "tokens_used": int,       # Total tokens
            "cost_usd": float,        # Estimated cost
            "provider": str,          # Provider used
            "tool_calls": list|None,  # Tool calls if any
            "finish_reason": str,     # Why generation stopped
        }
    """
    start_time = time.time()

    prompt = str(inputs.get("prompt", "")).strip()
    if not prompt and not inputs.get("messages"):
        return {
            "success": False,
            "error": "prompt is required",
            "content": "",
        }

    # Model resolution: "auto" or empty uses capability routing
    model_input = str(inputs.get("model", "")).strip()
    capability = str(inputs.get("capability", "")).strip() or "default"  # Use default routing, not reasoning

    if not model_input or model_input.lower() == "auto":
        # Resolve via capability routing
        try:
            from stdlib.llm.capability_routing import get_model_for_capability

            # Infer capability from context if not specified
            if inputs.get("tools"):
                capability = "tool_calling"

            model = get_model_for_capability(capability)
            if not model:
                model = "llama3.1:8b"  # Local-friendly ultimate fallback
            logger.debug("Model 'auto' resolved to %s for capability %s", model, capability)
        except Exception as e:
            logger.warning("Capability routing failed, using fallback: %s", e)
            model = "llama3.1:8b"
    else:
        model = model_input

    system = inputs.get("system")
    temperature = float(inputs.get("temperature", 0.7))
    max_tokens = int(inputs.get("max_tokens", 1200))
    response_format = str(inputs.get("response_format", "text")).strip()
    messages = inputs.get("messages")
    tools = inputs.get("tools")
    tool_choice = inputs.get("tool_choice")
    images = inputs.get("images")  # Vision support

    # Auto-select vision-capable model if images provided but model is auto
    if images and (not model_input or model_input.lower() == "auto"):
        try:
            from stdlib.llm.capability_routing import get_model_for_capability
            model = get_model_for_capability("vision.ocr") or "gpt-4o"
        except Exception:
            model = "gpt-4o"

    try:
        provider = get_provider(model)

        result = await provider.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            images=images,
        )

        duration_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "content": result.content,
            "model": result.model,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "provider": result.provider,
            "finish_reason": result.finish_reason,
            "tool_calls": result.tool_calls,
            "duration_ms": duration_ms,
        }

    except LLMProviderError as e:
        logger.warning("LLM generation failed: %s", e)
        return {
            "success": False,
            "error": str(e.message),
            "provider": e.provider,
            "model": e.model,
            "is_transient": e.is_transient,
            "content": "",
        }
    except Exception as e:
        logger.error("Unexpected LLM error: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "content": "",
        }


@register_tool(
    "llm.embed",
    description="Generate embeddings for text using an embedding model.",
    parameters={
        "type": "object",
        "properties": {
            "texts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of texts to embed",
            },
            "text": {
                "type": "string",
                "description": "Single text to embed (alternative to texts)",
            },
            "model": {
                "type": "string",
                "description": "Embedding model. Default: text-embedding-3-small",
            },
        },
        "required": [],
    },
)
async def llm_embed(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Generate embeddings for text.

    Returns:
        {
            "vectors": list[list[float]],  # Embedding vectors
            "model": str,
            "tokens_used": int,
            "cost_usd": float,
        }
    """
    # Handle both single text and list of texts
    texts = inputs.get("texts")
    if texts is None:
        text = inputs.get("text", "")
        texts = [text] if text else []

    if not texts:
        return {
            "success": False,
            "error": "texts or text is required",
            "vectors": [],
        }

    model = str(inputs.get("model", "text-embedding-3-small")).strip()

    try:
        # Only OpenAI supports embeddings currently
        from stdlib.llm import _PROVIDERS, _init_providers

        _init_providers()
        provider = _PROVIDERS.get("openai")
        if not provider:
            return {
                "success": False,
                "error": "OpenAI provider required for embeddings",
                "vectors": [],
            }

        result = await provider.embed(texts=texts, model=model)

        return {
            "success": True,
            "vectors": result.vectors,
            "model": result.model,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "provider": result.provider,
        }

    except LLMProviderError as e:
        logger.warning("Embedding failed: %s", e)
        return {
            "success": False,
            "error": str(e.message),
            "vectors": [],
        }
    except Exception as e:
        logger.error("Unexpected embedding error: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "vectors": [],
        }


@register_tool(
    "llm.json",
    description="Generate structured JSON output from an LLM.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The prompt describing what JSON to generate",
            },
            "schema": {
                "type": "object",
                "description": "JSON schema the output should match",
            },
            "model": {
                "type": "string",
                "description": "Model to use. Default: gpt-4o",
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature. Default: 0.3 (lower for structured output)",
            },
        },
        "required": ["prompt"],
    },
)
async def llm_json(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Generate structured JSON output.

    Convenience wrapper around llm.generate with JSON mode.

    Returns:
        {
            "data": dict|list,  # Parsed JSON
            "raw": str,         # Raw JSON string
            ...
        }
    """
    prompt = str(inputs.get("prompt", "")).strip()
    schema = inputs.get("schema")
    model_input = str(inputs.get("model", "")).strip()

    # Resolve "auto" or empty model via routing
    if not model_input or model_input.lower() == "auto":
        try:
            from stdlib.llm.capability_routing import get_model_for_capability

            model = get_model_for_capability("json_output") or "qwen2.5:7b"
        except Exception:
            model = "qwen2.5:7b"
    else:
        model = model_input

    temperature = float(inputs.get("temperature", 0.3))

    # Build prompt with schema hint
    if schema:
        prompt = f"{prompt}\n\nRespond with JSON matching this schema:\n```json\n{json.dumps(schema, indent=2)}\n```"

    result = await llm_generate(
        {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "response_format": "json",
            "max_tokens": inputs.get("max_tokens", 800),
        },
        context,
    )

    if not result.get("success"):
        return result

    # Parse JSON
    content = result.get("content", "")
    try:
        # Try to extract JSON from the response
        data = json.loads(content)
        result["data"] = data
        result["raw"] = content
    except json.JSONDecodeError as e:
        result["success"] = False
        result["error"] = f"Invalid JSON: {e}"
        result["data"] = None
        result["raw"] = content

    return result


@register_tool(
    "llm.providers",
    description="List available LLM providers.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
async def llm_providers(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """List available LLM providers.

    Returns:
        {
            "providers": list[str],  # Available provider names
        }
    """
    providers = list_available_providers()
    return {
        "success": True,
        "providers": providers,
    }


__all__ = [
    "llm_generate",
    "llm_embed",
    "llm_json",
    "llm_providers",
]
