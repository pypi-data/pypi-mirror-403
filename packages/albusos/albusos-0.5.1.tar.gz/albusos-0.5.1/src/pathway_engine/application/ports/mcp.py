"""MCP Client Port - Interface for MCP server communication.

The pathway engine can call external MCP servers without knowing
implementation details.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MCPClientPort(Protocol):
    """Interface for MCP client implementations."""

    def list_server_ids(self) -> list[str]:
        """List configured MCP server IDs."""
        ...

    async def call_tool(
        self,
        *,
        server_id: str,
        tool: str,
        arguments: dict[str, Any],
        timeout_ms: int | None = None,
    ) -> Any:
        """Call a tool on an MCP server."""
        ...

    async def list_tools(self, server_id: str) -> list[Any]:
        """List available tools on a server."""
        ...

    async def close(self) -> None:
        """Close all server connections."""
        ...


__all__ = ["MCPClientPort"]
