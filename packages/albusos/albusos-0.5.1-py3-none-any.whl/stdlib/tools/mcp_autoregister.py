"""MCP Auto-Registration - Make MCP tools first-class.

This module auto-discovers tools from configured MCP servers and registers
them as native tools (e.g., github.search_code, notion.query_database).

Usage:
    # During bootstrap (async context required)
    from stdlib.tools.mcp_autoregister import register_mcp_tools
    
    # The MCP client should be configured by the host runtime (e.g. albus.yaml).
    mcp_client = McpClientService(servers=[...])
    await register_mcp_tools(mcp_client)
    
    # Now MCP tools are available as:
    step.tool("github.search_code", q="...")
    step.agent_loop(tools=["github.*", "search.*"])
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Track which MCP tools have been registered
_MCP_REGISTERED_TOOLS: set[str] = set()

# Global reference to MCP client (set during registration)
_MCP_CLIENT: Any = None


def _create_mcp_tool_handler(
    server_id: str,
    tool_name: str,
) -> Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]:
    """Create a handler that delegates to MCP call_tool.

    The handler looks up the MCP client from context.extras or the global.
    """

    async def handler(inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
        # Get MCP client from context or global
        mcp_client = None
        # Prefer explicit wiring in execution Context extras (server path).
        extras = getattr(ctx, "extras", None)
        if isinstance(extras, dict):
            mcp_client = extras.get("mcp_client")
        # Fall back to typed services view (SDK/dev path).
        if mcp_client is None:
            services = getattr(ctx, "services", None)
            mcp_client = (
                getattr(services, "mcp_client", None) if services is not None else None
            )
        if mcp_client is None:
            mcp_client = _MCP_CLIENT

        if mcp_client is None:
            return {
                "success": False,
                "error": f"MCP client not available for {server_id}.{tool_name}",
            }

        try:
            result = await mcp_client.call_tool(
                server_id=server_id,
                tool=tool_name,
                arguments=inputs,
            )
            return {
                "success": True,
                "result": result,
                "server_id": server_id,
                "tool": tool_name,
            }
        except Exception as e:
            logger.error("MCP tool %s.%s failed: %s", server_id, tool_name, e)
            return {
                "success": False,
                "error": str(e),
                "server_id": server_id,
                "tool": tool_name,
            }

    return handler


def _register_single_mcp_tool(
    server_id: str,
    tool_name: str,
    description: str,
    input_schema: dict[str, Any],
) -> str:
    """Register a single MCP tool as a native tool.

    Returns the registered tool name (e.g., "github.search_code").
    """
    # Create namespaced tool name
    full_name = f"{server_id}.{tool_name}"

    if full_name in _MCP_REGISTERED_TOOLS:
        return full_name

    # Create handler
    handler = _create_mcp_tool_handler(server_id, tool_name)

    # Register in global registries
    TOOL_HANDLERS[full_name] = handler
    TOOL_DEFINITIONS[full_name] = {
        "description": description or f"MCP tool: {full_name}",
        "parameters": input_schema
        or {"type": "object", "properties": {}, "required": []},
        "requires_privileged": False,  # MCP tools don't require privileged by default
        "mcp": True,  # Mark as MCP tool
        "mcp_server": server_id,
        "mcp_tool": tool_name,
    }

    _MCP_REGISTERED_TOOLS.add(full_name)
    logger.debug("Registered MCP tool: %s", full_name)

    return full_name


async def register_mcp_tools(mcp_client: Any) -> list[str]:
    """Auto-discover and register all tools from configured MCP servers.

    Args:
        mcp_client: McpClientService instance

    Returns:
        List of registered tool names
    """
    global _MCP_CLIENT
    _MCP_CLIENT = mcp_client

    registered: list[str] = []

    # Get all configured server IDs
    server_ids = mcp_client.list_server_ids()

    if not server_ids:
        logger.info("No MCP servers configured")
        return registered

    logger.info(
        "Discovering tools from %d MCP server(s): %s", len(server_ids), server_ids
    )

    for server_id in server_ids:
        try:
            # List tools from this server
            tools = await mcp_client.list_tools(server_id=server_id)

            for tool in tools:
                full_name = _register_single_mcp_tool(
                    server_id=server_id,
                    tool_name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                )
                registered.append(full_name)

            logger.info(
                "Registered %d tools from MCP server '%s': %s",
                len(tools),
                server_id,
                [t.name for t in tools],
            )

        except Exception as e:
            logger.warning(
                "Failed to list tools from MCP server '%s': %s", server_id, e
            )

    return registered


def get_mcp_tool_names() -> list[str]:
    """Get list of registered MCP tool names."""
    return sorted(_MCP_REGISTERED_TOOLS)


def is_mcp_tool(tool_name: str) -> bool:
    """Check if a tool name is an MCP tool."""
    return tool_name in _MCP_REGISTERED_TOOLS


def get_mcp_tools_by_server(server_id: str) -> list[str]:
    """Get all MCP tool names for a specific server."""
    prefix = f"{server_id}."
    return [name for name in _MCP_REGISTERED_TOOLS if name.startswith(prefix)]


__all__ = [
    "register_mcp_tools",
    "get_mcp_tool_names",
    "is_mcp_tool",
    "get_mcp_tools_by_server",
]
