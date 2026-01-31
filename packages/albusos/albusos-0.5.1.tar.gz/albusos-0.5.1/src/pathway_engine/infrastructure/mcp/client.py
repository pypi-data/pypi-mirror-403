"""MCP Client Service - Implements MCPClientPort.

Manages connections to MCP servers via stdio or SSE JSON-RPC transport.
Routes tool calls to appropriate servers.

Architecture:
- McpClientService owns server lifecycle (spawn/connect, call, close)
- Stdio: Each server runs as a subprocess with stdin/stdout JSON-RPC
- SSE: Each server connects via HTTP SSE for responses, POST for requests
- Connections are lazily established on first call
- Supports multiple concurrent servers (github, notion, filesystem, etc.)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pathway_engine.application.ports.mcp import MCPClientPort

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration Types
# ---------------------------------------------------------------------------


@dataclass
class McpServerConfig:
    """Configuration for a stdio-based MCP server.

    Example:
        McpServerConfig(
            id="github",
            command=["npx", "-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."},
        )
    """

    id: str  # Server identifier
    command: list[str]  # Command to spawn server
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    timeout_ms: int = 30_000


@dataclass
class McpSseServerConfig:
    """Configuration for an SSE-based MCP server.

    Example:
        McpSseServerConfig(
            id="remote-tools",
            url="https://mcp.example.com/sse",
            headers={"Authorization": "Bearer xxx"},
        )
    """

    id: str  # Server identifier
    url: str  # SSE endpoint URL
    headers: dict[str, str] = field(default_factory=dict)
    timeout_ms: int = 30_000
    retry_attempts: int = 3


@dataclass
class McpTool:
    """A tool exposed by an MCP server."""

    name: str
    description: str = ""
    inputSchema: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Connection Protocol (shared interface for stdio and SSE)
# ---------------------------------------------------------------------------


@runtime_checkable
class McpConnection(Protocol):
    """Protocol for MCP server connections (stdio or SSE)."""

    def is_alive(self) -> bool:
        """Check if connection is still active."""
        ...

    async def call(
        self,
        method: str,
        params: dict[str, Any],
        timeout_ms: int | None = None,
    ) -> Any:
        """Send JSON-RPC request and await response."""
        ...

    async def close(self) -> None:
        """Close the connection."""
        ...


# ---------------------------------------------------------------------------
# Client Service (unified for both transports)
# ---------------------------------------------------------------------------


class McpClientService(MCPClientPort):
    """MCP client supporting both stdio and SSE transports.

    Implements MCPClientPort from pathway_engine.application.ports.

    Usage:
        # Stdio servers
        client = McpClientService(servers=[McpServerConfig(...)])

        # SSE servers
        client = McpClientService(sse_servers=[McpSseServerConfig(...)])

        # Mixed
        client = McpClientService(
            servers=[McpServerConfig(...)],
            sse_servers=[McpSseServerConfig(...)],
        )

        # List available tools
        tools = await client.list_tools(server_id="github")

        # Call a tool
        result = await client.call_tool(
            server_id="github",
            tool="search_code",
            arguments={"q": "ReAct pattern"},
        )
    """

    def __init__(
        self,
        servers: list[McpServerConfig] | None = None,
        sse_servers: list[McpSseServerConfig] | None = None,
    ):
        self._stdio_configs: dict[str, McpServerConfig] = {}
        self._sse_configs: dict[str, McpSseServerConfig] = {}
        self._connections: dict[str, McpConnection] = {}
        self._lock = asyncio.Lock()

        if servers:
            for s in servers:
                self._stdio_configs[s.id] = s
                logger.debug("Registered stdio MCP server: %s", s.id)

        if sse_servers:
            for s in sse_servers:
                self._sse_configs[s.id] = s
                logger.debug("Registered SSE MCP server: %s", s.id)

    def list_server_ids(self) -> list[str]:
        """List configured MCP server IDs (both stdio and SSE)."""
        return list(self._stdio_configs.keys()) + list(self._sse_configs.keys())

    async def call_tool(
        self,
        *,
        server_id: str,
        tool: str,
        arguments: dict[str, Any],
        timeout_ms: int | None = None,
    ) -> Any:
        """Call a tool on an MCP server.

        Args:
            server_id: Which server to call
            tool: Tool name
            arguments: Tool arguments
            timeout_ms: Optional timeout override

        Returns:
            Tool result from server
        """
        conn = await self._ensure_connected(server_id)
        timeout = timeout_ms or self._get_timeout(server_id)

        result = await conn.call(
            "tools/call",
            {
                "name": tool,
                "arguments": arguments,
            },
            timeout_ms=timeout,
        )

        # MCP tools return content array
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) == 1:
                item = content[0]
                if isinstance(item, dict) and item.get("type") == "text":
                    return item.get("text", "")
            return content

        return result

    async def list_tools(self, *, server_id: str) -> list[McpTool]:
        """List tools available on an MCP server."""
        conn = await self._ensure_connected(server_id)
        result = await conn.call("tools/list", {})
        return [McpTool(**t) for t in result.get("tools", [])]

    async def close_server(self, *, server_id: str) -> None:
        """Close connection to an MCP server."""
        conn = self._connections.pop(server_id, None)
        if conn:
            await conn.close()
            logger.info("Closed MCP server: %s", server_id)

    async def close_all(self) -> None:
        """Close all MCP server connections."""
        for server_id in list(self._connections.keys()):
            await self.close_server(server_id=server_id)

    def _get_timeout(self, server_id: str) -> int:
        """Get timeout_ms for a server."""
        if server_id in self._stdio_configs:
            return self._stdio_configs[server_id].timeout_ms
        if server_id in self._sse_configs:
            return self._sse_configs[server_id].timeout_ms
        return 30_000

    async def _ensure_connected(self, server_id: str) -> McpConnection:
        """Ensure connection to server, spawning/connecting if needed."""
        # Check existing connection
        if server_id in self._connections:
            conn = self._connections[server_id]
            if conn.is_alive():
                return conn
            # Connection died, clean up
            del self._connections[server_id]
            logger.warning("MCP server %s connection lost, reconnecting", server_id)

        # Determine transport type
        is_stdio = server_id in self._stdio_configs
        is_sse = server_id in self._sse_configs

        if not is_stdio and not is_sse:
            raise McpServerNotConfiguredError(f"MCP server not configured: {server_id}")

        # Acquire lock for connection creation
        async with self._lock:
            # Double-check after lock
            if server_id in self._connections:
                return self._connections[server_id]

            if is_stdio:
                config = self._stdio_configs[server_id]
                logger.info("Spawning stdio MCP server: %s", server_id)
                conn = await _McpStdioConnection.create(config)
            else:
                config = self._sse_configs[server_id]
                logger.info("Connecting to SSE MCP server: %s", server_id)
                from pathway_engine.infrastructure.mcp.sse_client import (
                    McpSseConfig,
                    McpSseConnection,
                )

                sse_config = McpSseConfig(
                    id=config.id,
                    url=config.url,
                    headers=config.headers,
                    timeout_ms=config.timeout_ms,
                    retry_attempts=config.retry_attempts,
                )
                conn = await McpSseConnection.create(sse_config)

            self._connections[server_id] = conn
            return conn


class _McpStdioConnection:
    """A connection to a single MCP server process via stdio.

    Handles:
    - Process lifecycle (spawn, communicate, terminate)
    - JSON-RPC request/response matching
    - Async reader loop for responses
    """

    def __init__(self, config: McpServerConfig, process: asyncio.subprocess.Process):
        self._config = config
        self._process = process
        self._request_id = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._reader_task: asyncio.Task | None = None

    @classmethod
    async def create(cls, config: McpServerConfig) -> "_McpStdioConnection":
        """Create and initialize connection to MCP server."""
        # Merge environment
        env = {**os.environ, **config.env}

        # Spawn server process
        process = await asyncio.create_subprocess_exec(
            config.command[0],
            *config.command[1:],
            *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        conn = cls(config, process)
        conn._reader_task = asyncio.create_task(conn._reader_loop())

        # MCP initialize handshake
        try:
            await conn.call(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "albus", "version": "1.0.0"},
                },
                timeout_ms=10_000,
            )
            logger.info("MCP server %s initialized", config.id)
        except Exception as e:
            await conn.close()
            raise McpProtocolError(f"Failed to initialize {config.id}: {e}") from e

        return conn

    def is_alive(self) -> bool:
        """Check if the server process is still running."""
        return self._process.returncode is None

    async def call(
        self,
        method: str,
        params: dict[str, Any],
        timeout_ms: int | None = None,
    ) -> Any:
        """Send JSON-RPC request and wait for response."""
        self._request_id += 1
        req_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        # Create future for response
        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[req_id] = future

        # Send request
        line = json.dumps(request) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

        # Wait for response
        timeout = (timeout_ms or 30_000) / 1000
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise McpTimeoutError(f"Timeout calling {method} on {self._config.id}")

    async def _reader_loop(self) -> None:
        """Read responses from server stdout."""
        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break

                try:
                    msg = json.loads(line.decode())
                    req_id = msg.get("id")

                    if req_id is not None and req_id in self._pending:
                        future = self._pending.pop(req_id)
                        if "error" in msg:
                            future.set_exception(McpProtocolError(msg["error"]))
                        else:
                            future.set_result(msg.get("result"))

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from MCP server %s", self._config.id)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("MCP reader error for %s: %s", self._config.id, e)
            # Fail all pending requests
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(e)

    async def close(self) -> None:
        """Close the connection and terminate the server."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()


class McpServerNotConfiguredError(Exception):
    """Raised when calling an unconfigured MCP server."""

    pass


class McpProtocolError(Exception):
    """MCP protocol error (invalid response, initialization failure, etc.)."""

    pass


class McpTimeoutError(Exception):
    """MCP request timeout."""

    pass


__all__ = [
    # Client service
    "McpClientService",
    # Config types
    "McpServerConfig",
    "McpSseServerConfig",
    "McpTool",
    # Errors
    "McpServerNotConfiguredError",
    "McpProtocolError",
    "McpTimeoutError",
]
