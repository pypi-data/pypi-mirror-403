"""Introspection Tools - Albus can query its own capabilities.

These tools let Albus ask "what can I do?" and "what do I know?"
at runtime, enabling true environmental awareness.
"""

from __future__ import annotations

import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)

# Special scope for tool indexing (internal, not user-accessible)
_TOOLS_SCOPE = "__tools__"
_TOOLS_INDEXED_FLAG = "__tools_indexed__"


@register_tool(
    "env.list_tools",
    description="List all available tools, pathways, and capabilities",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Filter by category (workspace, pathway, search, etc.)",
            },
            "include_schemas": {
                "type": "boolean",
                "description": "Include parameter schemas (default: false)",
            },
        },
    },
)
async def list_capabilities(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """List all capabilities available to Albus."""
    from stdlib.registry import (
        TOOL_HANDLERS,
        TOOL_DEFINITIONS,
        list_tools_by_category,
    )

    category_filter = inputs.get("category")
    include_schemas = inputs.get("include_schemas", False)

    categories = list_tools_by_category()

    # Filter if requested
    if category_filter:
        categories = {k: v for k, v in categories.items() if k == category_filter}

    result = {
        "categories": list(categories.keys()),
        "tools_by_category": {},
        "total_tools": 0,
    }

    for cat, tool_names in categories.items():
        tools = []
        for name in tool_names:
            defn = TOOL_DEFINITIONS.get(name, {})
            tool_info = {
                "name": name,
                "description": defn.get("description", "No description"),
            }
            if include_schemas:
                tool_info["parameters"] = defn.get("parameters", {})
            tools.append(tool_info)

        result["tools_by_category"][cat] = tools
        result["total_tools"] += len(tools)

    # Add graph ops
    result["graph_ops"] = [
        "graph.add_node",
        "graph.remove_node",
        "graph.rename_node",
        "graph.connect",
        "graph.disconnect",
        "graph.update_node",
        "graph.update_prompt",
    ]

    return result


@register_tool(
    "env.get_tool_schema",
    description="Get detailed schema for a specific tool",
    parameters={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool (e.g., 'workspace.read_file')",
            },
        },
        "required": ["tool_name"],
    },
)
async def get_tool_schema(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Get detailed schema for a specific tool."""
    from stdlib.registry import (
        TOOL_HANDLERS,
        TOOL_DEFINITIONS,
    )

    tool_name = inputs.get("tool_name", "")

    if tool_name not in TOOL_HANDLERS:
        return {"success": False, "error": f"Tool not found: {tool_name}"}

    defn = TOOL_DEFINITIONS.get(tool_name, {})
    handler = TOOL_HANDLERS[tool_name]

    return {
        "success": True,
        "name": tool_name,
        "description": defn.get("description", handler.__doc__ or "No description"),
        "parameters": defn.get("parameters", {}),
        "requires_privileged": defn.get("requires_privileged", False),
    }


@register_tool(
    "env.list_pathways",
    description="List available pathways in workspace",
    parameters={
        "type": "object",
        "properties": {
            "workspace_id": {
                "type": "string",
                "description": "Workspace ID (uses current if not specified)",
            },
        },
    },
)
async def list_available_pathways(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """List pathways available in workspace."""
    workspace_id = inputs.get("workspace_id") or context.workspace_id

    if not workspace_id:
        return {"pathways": [], "note": "No workspace context"}

    # Delegate to pathway.list
    from stdlib.tools.pathway import list_pathways

    return await list_pathways({"workspace_id": workspace_id}, context)


@register_tool(
    "env.get_context",
    description="Get current execution context",
    parameters={
        "type": "object",
        "properties": {},
    },
)
async def get_context(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Get current execution context."""
    return {
        "workspace_id": context.workspace_id,
        "thread_id": context.thread_id,
        "has_domain": context.domain is not None,
        "available_extras": list(context.extras.keys()) if context.extras else [],
    }


@register_tool(
    "env.get_environment",
    description="Get complete environment context (tools, pathways, workspace)",
    parameters={
        "type": "object",
        "properties": {
            "include_files": {
                "type": "boolean",
                "description": "Include workspace file listing (default: false)",
            },
        },
    },
)
async def get_environment(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Get complete environment context."""
    # NOTE: stdlib.perception.* was removed; keep this tool functional by returning
    # a lightweight environment summary from ToolContext + registry.
    tools = context.extras.get("tools", {}) if context.extras else {}
    tool_defs = context.extras.get("tool_definitions", {}) if context.extras else {}

    categories: dict[str, int] = {}
    for name in tools.keys():
        cat = name.split(".", 1)[0] if "." in name else "misc"
        categories[cat] = categories.get(cat, 0) + 1

    out: dict[str, Any] = {
        "workspace_id": context.workspace_id,
        "thread_id": context.thread_id,
        "has_domain": context.domain is not None,
        "tool_count": len(tools),
        "tool_categories": dict(sorted(categories.items())),
    }

    # Include a small sample of tool names for debugging.
    out["tools_sample"] = sorted(list(tools.keys()))[:25]

    # Optionally include workspace files (requires workspace tools + workspace_id).
    if inputs.get("include_files", False):
        try:
            from stdlib.tools.workspace import list_files

            out["workspace_files"] = await list_files({"path": "."}, context)
        except Exception as e:
            out["workspace_files"] = {"success": False, "error": str(e)}

    return out


@register_tool(
    "env.get_prompt",
    description="Get environment formatted for LLM prompt",
    parameters={
        "type": "object",
        "properties": {},
    },
)
async def get_capabilities_prompt(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Get capabilities formatted as prompt text."""
    tools = context.extras.get("tools", {}) if context.extras else {}
    categories = sorted({(n.split(".", 1)[0] if "." in n else "misc") for n in tools.keys()})

    # Keep prompt small and stable.
    prompt_lines = [
        "## Environment",
        f"- workspace_id: {context.workspace_id}",
        f"- thread_id: {context.thread_id}",
        f"- tool_count: {len(tools)}",
        f"- categories: {', '.join(categories)}",
        "",
        "## Tools (sample)",
        *[f"- {name}" for name in sorted(list(tools.keys()))[:30]],
    ]

    return {
        "prompt_text": "\n".join(prompt_lines),
        "tool_count": len(tools),
        "categories": categories,
    }


async def _index_single_tool(tool_name: str, context: ToolContext) -> bool:
    """Index a single tool in vector memory.

    Useful for indexing tools registered at runtime (e.g., MCP tools).

    Returns True if indexing was successful, False otherwise.
    """
    from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS
    from stdlib.tools.vector import vector_upsert

    if tool_name not in TOOL_HANDLERS:
        return False

    handler = TOOL_HANDLERS[tool_name]
    defn = TOOL_DEFINITIONS.get(tool_name, {})
    description = defn.get("description", handler.__doc__ or f"Tool: {tool_name}")

    # Create searchable text: name, description, and parameter hints
    category = tool_name.split(".")[0] if "." in tool_name else "misc"
    params = defn.get("parameters", {})
    param_names = []
    if isinstance(params, dict) and "properties" in params:
        param_names = list(params["properties"].keys())

    # Build rich searchable text
    searchable_text = f"{tool_name}\n{description}"
    if param_names:
        searchable_text += f"\nParameters: {', '.join(param_names)}"
    searchable_text += f"\nCategory: {category}"

    # Index this tool
    try:
        result = await vector_upsert(
            {
                "text": searchable_text,
                "scope": _TOOLS_SCOPE,
                "source_id": tool_name,
                "metadata": {
                    "tool_name": tool_name,
                    "category": category,
                    "description": description,
                    "parameters": params,
                    "requires_privileged": defn.get("requires_privileged", False),
                },
                "chunk_size": 2000,  # Tools are usually short, allow larger chunks
            },
            context,
        )

        if result.get("success"):
            logger.debug("Indexed tool: %s", tool_name)
            return True
    except Exception as e:
        logger.warning("Failed to index tool %s: %s", tool_name, e)

    return False


async def _ensure_tools_indexed(context: ToolContext) -> bool:
    """Ensure all tools are indexed in vector memory.

    Returns True if indexing was successful or already done, False otherwise.
    """
    # Check if already indexed (lazy check via vector memory)
    vector_memory = context.extras.get("vector_memory")
    if vector_memory is None:
        pathway_executor = context.pathway_executor
        if pathway_executor and hasattr(pathway_executor, "vector_memory"):
            vector_memory = pathway_executor.vector_memory

    if vector_memory is None:
        logger.debug("Vector memory not available for tool indexing")
        return False

    # Check if already indexed by doing a quick search for a known marker
    # If we get results, assume indexing is done
    try:
        # Try to search for a tool we know exists
        from stdlib.registry import TOOL_HANDLERS

        if not TOOL_HANDLERS:
            return False

        # Quick check: search for a common tool name
        test_results = await vector_memory.search(
            scope=_TOOLS_SCOPE,
            query="workspace.read_file",
            k=1,
        )
        if test_results:
            logger.debug("Tools already indexed")
            return True
    except Exception:
        # If search fails, assume not indexed
        pass

    # Index all tools
    from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS
    from stdlib.tools.vector import vector_upsert

    logger.info("Indexing %d tools for semantic search", len(TOOL_HANDLERS))

    indexed_count = 0
    for tool_name, handler in TOOL_HANDLERS.items():
        defn = TOOL_DEFINITIONS.get(tool_name, {})
        description = defn.get("description", handler.__doc__ or f"Tool: {tool_name}")

        # Create searchable text: name, description, and parameter hints
        category = tool_name.split(".")[0] if "." in tool_name else "misc"
        params = defn.get("parameters", {})
        param_names = []
        if isinstance(params, dict) and "properties" in params:
            param_names = list(params["properties"].keys())

        # Build rich searchable text
        searchable_text = f"{tool_name}\n{description}"
        if param_names:
            searchable_text += f"\nParameters: {', '.join(param_names)}"
        searchable_text += f"\nCategory: {category}"

        # Index this tool
        try:
            result = await vector_upsert(
                {
                    "text": searchable_text,
                    "scope": _TOOLS_SCOPE,
                    "source_id": tool_name,
                    "metadata": {
                        "tool_name": tool_name,
                        "category": category,
                        "description": description,
                        "parameters": params,
                        "requires_privileged": defn.get("requires_privileged", False),
                    },
                    "chunk_size": 2000,  # Tools are usually short, allow larger chunks
                },
                context,
            )

            if result.get("success"):
                indexed_count += 1
        except Exception as e:
            logger.warning("Failed to index tool %s: %s", tool_name, e)

    logger.info("Indexed %d/%d tools", indexed_count, len(TOOL_HANDLERS))
    return indexed_count > 0


@register_tool(
    "tools.search",
    description="Semantically search available tools by capability or description. Automatically indexes tools on first use.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query (e.g., 'tools for reading files', 'web search capabilities', 'file operations')",
            },
            "k": {
                "type": "integer",
                "description": "Number of results to return (default: 5)",
            },
            "category": {
                "type": "string",
                "description": "Filter by category (optional, e.g., 'workspace', 'search', 'llm')",
            },
            "min_score": {
                "type": "number",
                "description": "Minimum similarity score 0-1 (default: 0.3)",
            },
        },
        "required": ["query"],
    },
)
async def search_tools(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Semantically search available tools.

    This tool automatically indexes all registered tools on first use,
    then performs semantic search over tool descriptions, names, and parameters.

    Returns:
        {
            "success": bool,
            "results": [
                {
                    "tool_name": str,
                    "description": str,
                    "category": str,
                    "score": float,
                    "parameters": dict,
                }
            ],
            "total": int,
        }
    """
    query = str(inputs.get("query", "")).strip()
    if not query:
        return {"success": False, "error": "query is required", "results": []}

    k = int(inputs.get("k", 5))
    category_filter = inputs.get("category")
    min_score = float(inputs.get("min_score", 0.3))

    # Ensure tools are indexed
    indexed = await _ensure_tools_indexed(context)
    if not indexed:
        # Fallback to non-semantic search if vector memory unavailable
        logger.warning("Tool indexing unavailable, falling back to keyword search")
        return await _fallback_tool_search(query, k, category_filter)

    # Use vector.search to find matching tools
    from stdlib.tools.vector import vector_search

    filters = {}
    if category_filter:
        filters["category"] = category_filter

    search_result = await vector_search(
        {
            "query": query,
            "scope": _TOOLS_SCOPE,
            "k": k * 2,  # Get more results to filter by score
            "min_score": min_score,
            "filters": filters if filters else None,
        },
        context,
    )

    if not search_result.get("success"):
        return {
            "success": False,
            "error": search_result.get("error", "Search failed"),
            "results": [],
        }

    # Transform results to include full tool information
    results = []
    for item in search_result.get("results", []):
        metadata = item.get("metadata", {})
        tool_name = metadata.get("tool_name", item.get("id", ""))

        # Skip if category filter doesn't match
        if category_filter and metadata.get("category") != category_filter:
            continue

        results.append(
            {
                "tool_name": tool_name,
                "description": metadata.get("description", item.get("text", "")),
                "category": metadata.get("category", "misc"),
                "score": item.get("score", 0.0),
                "parameters": metadata.get("parameters", {}),
                "requires_privileged": metadata.get("requires_privileged", False),
            }
        )

        if len(results) >= k:
            break

    return {
        "success": True,
        "results": results,
        "total": len(results),
        "query": query,
    }


async def _fallback_tool_search(
    query: str, k: int, category_filter: str | None
) -> dict[str, Any]:
    """Fallback keyword-based tool search when vector memory unavailable."""
    from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS

    query_lower = query.lower()
    results = []

    for tool_name, handler in TOOL_HANDLERS.items():
        defn = TOOL_DEFINITIONS.get(tool_name, {})
        description = defn.get("description", handler.__doc__ or "").lower()
        category = tool_name.split(".")[0] if "." in tool_name else "misc"

        # Skip if category filter doesn't match
        if category_filter and category != category_filter:
            continue

        # Simple keyword matching
        if query_lower in tool_name.lower() or query_lower in description:
            results.append(
                {
                    "tool_name": tool_name,
                    "description": defn.get("description", ""),
                    "category": category,
                    "score": 0.5,  # Lower score for fallback
                    "parameters": defn.get("parameters", {}),
                    "requires_privileged": defn.get("requires_privileged", False),
                }
            )

            if len(results) >= k:
                break

    return {
        "success": True,
        "results": results,
        "total": len(results),
        "query": query,
        "note": "Using keyword search (vector memory unavailable)",
    }


__all__ = [
    "list_capabilities",
    "get_tool_schema",
    "list_available_pathways",
    "get_context",
    "get_environment",
    "get_capabilities_prompt",
    "search_tools",
    "_ensure_tools_indexed",
    "_index_single_tool",
]
