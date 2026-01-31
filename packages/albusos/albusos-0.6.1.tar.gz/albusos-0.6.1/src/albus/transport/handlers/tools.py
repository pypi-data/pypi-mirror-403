"""Tool endpoint handlers."""

from __future__ import annotations

import logging
import time
from typing import Any

from aiohttp import web

from stdlib.registry import TOOL_DEFINITIONS, TOOL_HANDLERS
from albus.infrastructure.errors import ErrorCode, sanitize_error_message
from albus.transport.utils import (
    error_response,
    get_request_id,
    get_runtime,
    jsonable,
    parse_json_body,
)

logger = logging.getLogger(__name__)


async def handle_list_tools(request: web.Request) -> web.Response:
    """GET /api/v1/tools - List all available tools."""
    category_filter = request.query.get("category")
    output_format = request.query.get("format", "list")

    tools = []
    categories: dict[str, list[dict]] = {}

    for name in sorted(TOOL_HANDLERS.keys()):
        cat = name.split(".")[0]

        if category_filter and cat != category_filter:
            continue

        meta = TOOL_DEFINITIONS.get(name, {})
        tool_info = {
            "name": name,
            "category": cat,
            "description": meta.get("description", ""),
            "parameters": meta.get("parameters", {}),
        }
        tools.append(tool_info)
        categories.setdefault(cat, []).append(tool_info)

    if output_format == "grouped":
        return web.json_response(
            {
                "categories": {k: len(v) for k, v in categories.items()},
                "tools_by_category": categories,
                "total": len(tools),
            }
        )

    return web.json_response(
        {
            "tools": tools,
            "count": len(tools),
            "categories": sorted(categories.keys()),
        }
    )


async def handle_tool_call(request: web.Request) -> web.Response:
    """POST /api/v1/tools/{tool_name} - Execute a tool directly."""
    start = time.time()
    tool_name = request.match_info["tool_name"]
    request_id = get_request_id(request)

    tool_fn = TOOL_HANDLERS.get(tool_name)
    if not tool_fn:
        return error_response(
            request,
            f"Tool not found: {tool_name}",
            ErrorCode.TOOL_NOT_FOUND,
            status=404,
            details={"available_tools": list(TOOL_HANDLERS.keys())[:20]},
        )

    body = await parse_json_body(request)
    if body is None:
        body = {}

    try:
        # Build ToolContext from runtime PathwayVM context.
        from pathway_engine.application.ports.tool_registry import ToolContext

        runtime = get_runtime(request)
        vm_ctx = runtime.pathway_vm.ctx
        extras = getattr(vm_ctx, "extras", None) or {}

        domain = extras.get("domain")
        mcp_client = extras.get("mcp_client")
        pathway_executor = extras.get("pathway_executor") or runtime.pathway_vm

        workspace_id = body.get("workspace_id") or extras.get("workspace_id")
        thread_id = body.get("thread_id") or extras.get("thread_id")

        # Best-effort: create a default workspace when domain is available.
        if domain is not None and not workspace_id:
            try:
                ws = domain.create_workspace(name="API Tool Workspace")
                workspace_id = getattr(ws, "id", None) or getattr(ws, "workspace_id", None)
                # Persist for subsequent tool calls.
                if workspace_id:
                    try:
                        vm_ctx.extras["workspace_id"] = str(workspace_id)
                    except Exception:
                        pass
            except Exception:
                workspace_id = None

        tool_ctx = ToolContext(
            domain=domain,
            pathway_executor=pathway_executor,
            mcp_client=mcp_client,
            workspace_id=workspace_id,
            thread_id=thread_id,
            kernel="privileged",
            extras={
                **extras,
                # Provide tool registry for env/introspection helpers.
                "tools": TOOL_HANDLERS,
                "tool_definitions": TOOL_DEFINITIONS,
                # Provide runtime services for tools that need them.
                "pathway_service": getattr(runtime, "pathway_service", None),
                "agent_service": getattr(runtime, "agent_service", None),
            },
        )

        result = await tool_fn(body, tool_ctx)
        duration_ms = (time.time() - start) * 1000
        return web.json_response(
            {
                "success": True,
                "tool": tool_name,
                "result": jsonable(result),
                "duration_ms": duration_ms,
            }
        )
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(
            request,
            error_msg,
            ErrorCode.TOOL_EXECUTION_FAILED,
            status=500,
            details={"tool": tool_name, "duration_ms": duration_ms},
        )


__all__ = [
    "handle_list_tools",
    "handle_tool_call",
]
