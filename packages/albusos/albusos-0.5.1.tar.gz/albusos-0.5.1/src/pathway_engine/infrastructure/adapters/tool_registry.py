"""Tool Registry - Tools available in the Runtime environment.

This module manages the tools that pathways can use.

Tool categories:
- Builtin tools: Core capabilities (llm, vector, search, etc.)
- User tools: Tools defined by users
- MCP tools: Tools from MCP servers

The registry provides a unified view of all available tools and bridges
the albus tools with the pathway execution layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from pathway_engine.application.ports.tool_registry import (
    ToolContext,
    ToolInvocationError,
    ToolNotFoundError,
    ToolRegistryPort,
    ToolSchema,
)

if TYPE_CHECKING:
    from pathway_engine.application.ports.mcp import MCPClientPort

logger = logging.getLogger(__name__)

# Type for tool handlers
ToolHandler = Callable[..., Awaitable[Any] | Any]


class ToolCategory(str, Enum):
    """Categories of tools."""

    BUILTIN = "builtin"  # Core capabilities
    USER = "user"  # User-defined
    MCP = "mcp"  # From MCP servers


@dataclass
class RegisteredTool:
    """A tool registered in the runtime."""

    # Identity
    tool_id: str
    name: str
    description: str = ""

    # Category
    category: ToolCategory = ToolCategory.USER

    # Schema
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] | None = None

    # Handler (for builtin tools)
    handler: Callable[..., Awaitable[Any]] | None = None

    # For MCP tools
    mcp_server_id: str | None = None

    # Permissions
    requires_approval: bool = False
    allowed_categories: list[str] = field(default_factory=list)


class ToolRegistry(ToolRegistryPort):
    """Tool registry implementing ToolRegistryPort.

    Manages builtin tools and MCP tools with unified discovery and invocation.

    This registry bridges the albus tools (registered via @register_tool)
    with the pathway execution layer.
    """

    def __init__(self, *, mcp_client: "MCPClientPort | None" = None):
        self._mcp_client = mcp_client
        self._tools: dict[str, ToolSchema] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._mcp_tools: dict[str, str] = {}  # tool_id -> server_id

    def register_builtin(
        self,
        tool_id: str,
        *,
        name: str,
        description: str,
        handler: ToolHandler,
        input_schema: dict[str, Any],
        requires_privileged: bool = False,
    ) -> ToolSchema:
        """Register a builtin tool with its handler."""
        schema = ToolSchema(
            id=tool_id,
            name=name,
            description=description,
            input_schema=input_schema,
            category="builtin",
            requires_privileged=requires_privileged,
        )
        self._tools[tool_id] = schema
        self._handlers[tool_id] = handler
        return schema

    # =========================================================================
    # ToolRegistryPort implementation
    # =========================================================================

    def list_tools(self, *, privileged: bool = False) -> list[ToolSchema]:
        """List available tools."""
        if privileged:
            return list(self._tools.values())
        return [t for t in self._tools.values() if not t.requires_privileged]

    def get_tool(self, tool_id: str) -> ToolSchema | None:
        """Get a specific tool's schema by ID."""
        return self._tools.get(tool_id)

    async def invoke(
        self,
        tool_id: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Invoke a tool with arguments and context.

        Routes to builtin handler or MCP server based on tool type.
        """
        schema = self._tools.get(tool_id)
        if not schema:
            raise ToolNotFoundError(tool_id)

        # Permission check
        if schema.requires_privileged and not context.is_privileged:
            raise PermissionError(f"Tool {tool_id} requires privileged context")

        try:
            # Builtin tool (including albus tools)
            if tool_id in self._handlers:
                handler = self._handlers[tool_id]
                # albus tools expect (inputs: dict, context: ToolContext)
                # Check handler signature to determine call pattern
                result = handler(arguments, context)
                # Handle async
                if hasattr(result, "__await__"):
                    result = await result
                # Normalize to dict
                if not isinstance(result, dict):
                    result = {"result": result}
                return result

            # MCP tool
            if tool_id in self._mcp_tools:
                if not self._mcp_client:
                    raise ToolInvocationError(tool_id, "MCP client not configured")
                server_id = self._mcp_tools[tool_id]
                result = await self._mcp_client.call_tool(
                    server_id=server_id,
                    tool=schema.name,
                    arguments=arguments,
                )
                if not isinstance(result, dict):
                    result = {"result": result}
                return result

            raise ToolInvocationError(tool_id, "No handler configured")

        except (ToolNotFoundError, ToolInvocationError, PermissionError):
            raise
        except Exception as e:
            raise ToolInvocationError(tool_id, str(e), cause=e) from e

    def get_schemas_for_prompt(self, *, privileged: bool = False) -> str:
        """Get tool schemas formatted for LLM prompts."""
        tools = self.list_tools(privileged=privileged)
        if not tools:
            return "No tools available."

        lines = ["Available tools:"]
        for t in tools:
            lines.append(f"\n- {t.id}: {t.description}")
            if t.input_schema:
                props = t.input_schema.get("properties", {})
                if props:
                    params = ", ".join(props.keys())
                    lines.append(f"  Parameters: {params}")
        return "\n".join(lines)

    # =========================================================================
    # MCP tool loading
    # =========================================================================

    async def load_mcp_tools(self) -> int:
        """Load tools from configured MCP servers.

        Returns number of tools loaded.
        """
        if not self._mcp_client:
            return 0

        count = 0
        for server_id in self._mcp_client.list_server_ids():
            try:
                mcp_tools = await self._mcp_client.list_tools(server_id=server_id)
                for mcp_tool in mcp_tools:
                    tool_id = f"mcp.{server_id}.{mcp_tool.name}"
                    schema = ToolSchema(
                        id=tool_id,
                        name=mcp_tool.name,
                        description=getattr(mcp_tool, "description", ""),
                        input_schema=getattr(mcp_tool, "inputSchema", {}),
                        category="mcp",
                        source=f"mcp:{server_id}",
                        requires_privileged=True,  # MCP tools need privileged
                    )
                    self._tools[tool_id] = schema
                    self._mcp_tools[tool_id] = server_id
                    count += 1
            except Exception as e:
                logger.warning(
                    "Failed to load tools from MCP server %s: %s", server_id, e
                )

        return count

    def as_dict(self) -> dict[str, ToolHandler]:
        """Export tools as a dict for Context.tools.

        Returns dict[tool_id, handler] where handlers accept (args, context) signature.
        """
        return dict(self._handlers)


__all__ = [
    "ToolHandler",
    "ToolRegistry",
    "ToolCategory",
    "RegisteredTool",
]
