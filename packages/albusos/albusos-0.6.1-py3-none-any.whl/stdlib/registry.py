from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable, cast

from pathway_engine.application.ports.tool_registry import (
    ToolContext,
    ToolNotFoundError,
    ToolSchema,
)

logger = logging.getLogger(__name__)

# Public handler signature expected by Pathway Engine Context.tools:
# async (inputs: dict, ctx: pathway_engine.domain.context.Context) -> dict
ToolHandler = Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]

# Internally, stdlib tool authors SHOULD implement:
# async (inputs: dict, context: ToolContext) -> dict
ToolHandlerWithToolContext = Callable[
    [dict[str, Any], ToolContext], Awaitable[dict[str, Any]]
]


TOOL_HANDLERS: dict[str, ToolHandler] = {}
TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {}


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _coerce_tool_context(ctx: Any) -> ToolContext:
    """Coerce a Pathway Engine execution Context into a ToolContext.

    `PathwayVM` passes `pathway_engine.domain.context.Context` into tool handlers.
    Stdlib tools are written against `ToolContext` (domain, pathway_executor, MCP, etc.).

    This adapter keeps `pathway_engine` runtime-neutral: tools are responsible for coercion.
    """
    if isinstance(ctx, ToolContext):
        return ctx

    extras = getattr(ctx, "extras", None)
    if not isinstance(extras, dict):
        extras = {}

    workspace_id = getattr(ctx, "workspace_id", None) or extras.get("workspace_id")
    thread_id = getattr(ctx, "thread_id", None) or extras.get("thread_id")

    return ToolContext(
        domain=extras.get("domain"),
        pathway_executor=cast(Any, extras.get("pathway_executor")),
        mcp_client=cast(Any, extras.get("mcp_client")),
        workspace_id=cast(Any, workspace_id),
        thread_id=cast(Any, thread_id),
        kernel=str(extras.get("kernel") or extras.get("kernel_type") or "user"),
        extras=extras,
    )


def register_tool(
    name: str,
    *,
    description: str | None = None,
    parameters: dict[str, Any] | None = None,
    requires_privileged: bool = False,
) -> Callable[[ToolHandlerWithToolContext], ToolHandlerWithToolContext]:
    """Decorator to register a stdlib tool.

    This produces a wrapper compatible with `Context.tools`:
      async (inputs, ctx) -> dict
    while allowing tool authors to implement:
      async (inputs, ToolContext) -> dict
    """

    def decorator(fn: ToolHandlerWithToolContext) -> ToolHandlerWithToolContext:
        async def _wrapped(inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
            tool_ctx = _coerce_tool_context(ctx)
            return await fn(inputs, tool_ctx)

        # Preserve streaming interface if provided (EventSourceNode checks `.stream`).
        try:
            stream_fn = getattr(fn, "stream", None)
            if stream_fn is not None:
                setattr(_wrapped, "stream", stream_fn)
        except Exception:
            pass

        TOOL_HANDLERS[name] = cast(Any, _wrapped)
        TOOL_DEFINITIONS[name] = {
            "description": description
            or getattr(fn, "__doc__", None)
            or f"Tool: {name}",
            "parameters": parameters
            or {"type": "object", "properties": {}, "required": []},
            "requires_privileged": requires_privileged,
        }

        if _env_bool("AGENT_STDLIB_LOG_TOOL_REGISTRATION", default=False):
            logger.debug("Registered tool: %s", name)

        return fn

    return decorator


def get_tool_handler(name: str) -> ToolHandler | None:
    return TOOL_HANDLERS.get(name)


async def execute_tool(
    name: str, inputs: dict[str, Any], context: Any
) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        raise ToolNotFoundError(name)
    return await handler(inputs, context)


def list_tools_by_category() -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {}
    for name in TOOL_HANDLERS.keys():
        category = name.split(".")[0] if "." in name else "misc"
        categories.setdefault(category, []).append(name)
    return categories


def _sanitize_tool_name_for_llm(name: str) -> str:
    """Convert tool name to OpenAI-compatible format (no dots allowed)."""
    return name.replace(".", "_")


def _unsanitize_tool_name(name: str) -> str:
    """Convert OpenAI-format tool name back to internal format."""
    # Common patterns: pathway_create -> pathway.create
    for prefix in (
        "pathway_",
        "workspace_",
        "search_",
        "vision_",
        "llm_",
        "code_",
        "mcp_",
        "kg_",
        "memory_",
        "vector_",
    ):
        if name.startswith(prefix):
            return name.replace("_", ".", 1)
    return name


def get_tool_schemas_for_llm() -> list[dict[str, Any]]:
    """Return OpenAI/Anthropic compatible tool schema payloads.

    Note: Function names are sanitized (dots -> underscores) for OpenAI compatibility.
    Use _unsanitize_tool_name() to map back to internal names.
    """
    schemas: list[dict[str, Any]] = []
    for name, defn in TOOL_DEFINITIONS.items():
        if name in TOOL_HANDLERS:
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": _sanitize_tool_name_for_llm(name),
                        "description": defn.get("description", ""),
                        "parameters": defn.get("parameters", {}),
                    },
                }
            )
    return schemas


def list_tool_schemas(*, privileged: bool = False) -> list[ToolSchema]:
    schemas: list[ToolSchema] = []
    for name, defn in TOOL_DEFINITIONS.items():
        if name not in TOOL_HANDLERS:
            continue
        req_priv = bool(defn.get("requires_privileged", False))
        if req_priv and not privileged:
            continue
        schemas.append(
            ToolSchema(
                id=name,
                name=name.split(".")[-1],
                description=str(defn.get("description", "")),
                input_schema=cast(Any, defn.get("parameters", {})),
                category="stdlib",
                requires_privileged=req_priv,
            )
        )
    return schemas
