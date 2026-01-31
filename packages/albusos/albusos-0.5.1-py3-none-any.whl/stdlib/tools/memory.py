"""Memory tools - search, get, set for Albus memory.

These tools back the `remember` DSL verbs:
    remember.search("query")  → memory.search
    remember.get("key")       → memory.get
    remember.store(key, val)  → memory.set

For now, this is a simple in-memory store. 
Later we can swap in vector DB, Redis, etc.
"""

from __future__ import annotations

import logging
from typing import Any

from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


# =============================================================================
# IN-MEMORY STORE (placeholder - swap for real backend later)
# =============================================================================

# Namespace -> Key -> Value
_MEMORY_STORE: dict[str, dict[str, Any]] = {}

# Namespace -> List of {key, value, text} for search
_MEMORY_INDEX: dict[str, list[dict[str, Any]]] = {}


def _get_namespace(ns: str) -> dict[str, Any]:
    if ns not in _MEMORY_STORE:
        _MEMORY_STORE[ns] = {}
    return _MEMORY_STORE[ns]


def _get_index(ns: str) -> list[dict[str, Any]]:
    if ns not in _MEMORY_INDEX:
        _MEMORY_INDEX[ns] = []
    return _MEMORY_INDEX[ns]


# =============================================================================
# TOOLS
# =============================================================================


@register_tool(
    "memory.search",
    description="Semantic search over memory. Returns relevant memories.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "namespace": {
                "type": "string",
                "description": "Memory namespace",
                "default": "default",
            },
            "limit": {"type": "integer", "description": "Max results", "default": 5},
        },
        "required": ["query"],
    },
)
async def memory_search(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Search memory (simple substring match for now)."""
    query = inputs.get("query", "").lower()
    namespace = inputs.get("namespace", "default")
    limit = inputs.get("limit", 5)

    index = _get_index(namespace)

    # Simple relevance: substring match + recency
    results = []
    for i, entry in enumerate(reversed(index)):  # Most recent first
        text = str(entry.get("text", "") or entry.get("value", "")).lower()
        if query in text or any(word in text for word in query.split()):
            results.append(
                {
                    "id": entry.get("key", f"entry_{i}"),
                    "text": entry.get("text") or entry.get("value"),
                    "score": 1.0 - (i * 0.01),  # Recency bias
                    "metadata": entry.get("metadata", {}),
                }
            )
            if len(results) >= limit:
                break

    logger.debug(
        "memory.search: query=%r namespace=%s results=%d",
        query,
        namespace,
        len(results),
    )
    return {"results": results, "query": query, "namespace": namespace}


@register_tool(
    "memory.get",
    description="Get a specific value from memory by key.",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Memory key"},
            "namespace": {
                "type": "string",
                "description": "Memory namespace",
                "default": "default",
            },
        },
        "required": ["key"],
    },
)
async def memory_get(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Get value by key."""
    key = inputs.get("key", "")
    namespace = inputs.get("namespace", "default")

    store = _get_namespace(namespace)
    value = store.get(key)

    logger.debug(
        "memory.get: key=%r namespace=%s found=%s", key, namespace, value is not None
    )
    return {"key": key, "value": value, "found": value is not None}


@register_tool(
    "memory.set",
    description="Store a value in memory.",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Memory key"},
            "value": {"type": ["string", "object"], "description": "Value to store"},
            "namespace": {
                "type": "string",
                "description": "Memory namespace",
                "default": "default",
            },
            "metadata": {"type": "object", "description": "Optional metadata"},
        },
        "required": ["key", "value"],
    },
)
async def memory_set(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Store value in memory."""
    key = inputs.get("key", "")
    value = inputs.get("value")
    namespace = inputs.get("namespace", "default")
    metadata = inputs.get("metadata", {})

    # Store in key-value store
    store = _get_namespace(namespace)
    store[key] = value

    # Also index for search
    index = _get_index(namespace)
    text = value if isinstance(value, str) else str(value)
    index.append(
        {
            "key": key,
            "value": value,
            "text": text,
            "metadata": metadata,
        }
    )

    logger.debug("memory.set: key=%r namespace=%s", key, namespace)
    return {"key": key, "written": True, "namespace": namespace}


@register_tool(
    "memory.clear",
    description="Clear memory (optionally by namespace).",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {
                "type": "string",
                "description": "Namespace to clear (omit for all)",
            },
        },
    },
)
async def memory_clear(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Clear memory."""
    namespace = inputs.get("namespace")

    if namespace:
        _MEMORY_STORE.pop(namespace, None)
        _MEMORY_INDEX.pop(namespace, None)
        logger.info("memory.clear: namespace=%s", namespace)
        return {"cleared": True, "namespace": namespace}
    else:
        _MEMORY_STORE.clear()
        _MEMORY_INDEX.clear()
        logger.info("memory.clear: all namespaces")
        return {"cleared": True, "namespace": "all"}


__all__ = [
    "memory_search",
    "memory_get",
    "memory_set",
    "memory_clear",
]
