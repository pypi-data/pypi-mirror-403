"""MCP Tools - Model Context Protocol integration.

These tools expose MCP server capabilities to pathways:
- mcp.call: Call a tool on an MCP server
- mcp.list_tools: List tools available on an MCP server
- mcp.servers: List configured MCP servers
"""

from __future__ import annotations

import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext

from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool(
    "mcp.call",
    description="Call a tool on an MCP server (e.g., GitHub, Notion, filesystem).",
    parameters={
        "type": "object",
        "properties": {
            "server_id": {
                "type": "string",
                "description": "MCP server ID (e.g., 'github', 'notion')",
            },
            "tool": {
                "type": "string",
                "description": "Tool name on the server",
            },
            "arguments": {
                "type": "object",
                "description": "Arguments to pass to the tool",
            },
            "timeout_ms": {
                "type": "integer",
                "description": "Timeout in milliseconds. Default: 30000",
            },
        },
        "required": ["server_id", "tool"],
    },
    requires_privileged=True,
)
async def mcp_call(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Call a tool on an MCP server.

    This is a privileged tool - only available to Albus (PrivilegedKernel).

    Returns:
        {
            "result": any,  # Tool output
        }
    """
    server_id = str(inputs.get("server_id", "")).strip()
    tool_name = str(inputs.get("tool", "")).strip()
    arguments = inputs.get("arguments", {})
    timeout_ms = inputs.get("timeout_ms")

    if not server_id:
        return {"success": False, "error": "server_id is required"}
    if not tool_name:
        return {"success": False, "error": "tool is required"}

    # Get MCP client from context
    mcp_client = context.mcp_client
    if mcp_client is None:
        mcp_client = context.extras.get("mcp_client")

    if mcp_client is None:
        return {
            "success": False,
            "error": "MCP client not available (privileged context required)",
        }

    try:
        result = await mcp_client.call_tool(
            server_id=server_id,
            tool=tool_name,
            arguments=arguments,
            timeout_ms=timeout_ms,
        )

        return {
            "success": True,
            "result": result,
            "server_id": server_id,
            "tool": tool_name,
        }

    except Exception as e:
        logger.error("MCP call failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "server_id": server_id,
            "tool": tool_name,
        }


@register_tool(
    "mcp.list_tools",
    description="List tools available on an MCP server.",
    parameters={
        "type": "object",
        "properties": {
            "server_id": {
                "type": "string",
                "description": "MCP server ID",
            },
        },
        "required": ["server_id"],
    },
    requires_privileged=True,
)
async def mcp_list_tools(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """List tools available on an MCP server.

    Returns:
        {
            "tools": [
                {
                    "name": str,
                    "description": str,
                    "inputSchema": dict,
                }
            ],
        }
    """
    server_id = str(inputs.get("server_id", "")).strip()
    if not server_id:
        return {"success": False, "error": "server_id is required", "tools": []}

    mcp_client = context.mcp_client
    if mcp_client is None:
        mcp_client = context.extras.get("mcp_client")

    if mcp_client is None:
        return {
            "success": False,
            "error": "MCP client not available",
            "tools": [],
        }

    try:
        tools = await mcp_client.list_tools(server_id=server_id)

        return {
            "success": True,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                }
                for t in tools
            ],
            "server_id": server_id,
        }

    except Exception as e:
        logger.error("MCP list_tools failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "tools": [],
        }


@register_tool(
    "mcp.servers",
    description="List configured MCP servers.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    requires_privileged=True,
)
async def mcp_servers(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """List configured MCP servers.

    Returns:
        {
            "servers": list[str],  # Server IDs
        }
    """
    mcp_client = context.mcp_client
    if mcp_client is None:
        mcp_client = context.extras.get("mcp_client")

    if mcp_client is None:
        return {
            "success": True,
            "servers": [],
            "note": "MCP client not configured",
        }

    try:
        servers = mcp_client.list_server_ids()
        return {
            "success": True,
            "servers": servers,
        }

    except Exception as e:
        logger.error("MCP servers list failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "servers": [],
        }


__all__ = [
    "mcp_call",
    "mcp_list_tools",
    "mcp_servers",
]
