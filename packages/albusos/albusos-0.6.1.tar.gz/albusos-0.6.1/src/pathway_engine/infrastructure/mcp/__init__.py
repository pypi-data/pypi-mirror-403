"""MCP (Model Context Protocol) client.

This package provides connectivity to external MCP servers for tool access.
Supports both stdio (subprocess) and SSE (HTTP) transports.

Configuration is owned by the host runtime (e.g. Albus via `albus.yaml`), which
creates config objects and passes them into `McpClientService`.

Transports:
- stdio: Spawn local MCP server as subprocess (McpServerConfig)
- sse: Connect to remote MCP server via HTTP SSE (McpSseServerConfig)
"""

from pathway_engine.infrastructure.mcp.client import (
    McpClientService,
    McpProtocolError,
    McpServerConfig,
    McpServerNotConfiguredError,
    McpSseServerConfig,
    McpTimeoutError,
    McpTool,
)
from pathway_engine.infrastructure.mcp.sse_client import (
    McpSseConfig,
    McpSseConnection,
    McpSseProtocolError,
    McpSseTimeoutError,
)

__all__ = [
    # Client service (unified)
    "McpClientService",
    # Stdio config
    "McpServerConfig",
    # SSE config (high-level for service)
    "McpSseServerConfig",
    # SSE config (low-level for direct connection)
    "McpSseConfig",
    "McpSseConnection",
    # Tool type
    "McpTool",
    # Errors (stdio)
    "McpProtocolError",
    "McpServerNotConfiguredError",
    "McpTimeoutError",
    # Errors (SSE)
    "McpSseProtocolError",
    "McpSseTimeoutError",
]
