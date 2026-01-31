"""MCP Client using SSE (Server-Sent Events) transport.

Connects to remote MCP servers that expose an SSE endpoint.
Communication flow:
- Server → Client: Events delivered via SSE stream  
- Client → Server: Requests sent via HTTP POST

This is complementary to the stdio transport (client.py) which
spawns local subprocess servers.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class McpSseConfig:
    """Configuration for an SSE-based MCP server.

    Example:
        McpSseConfig(
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


class McpSseConnection:
    """Connection to an MCP server via SSE transport.

    Handles:
    - SSE event stream for receiving responses/notifications
    - HTTP POST for sending requests
    - JSON-RPC request/response correlation
    - Automatic reconnection on connection loss
    """

    def __init__(self, config: McpSseConfig):
        self._config = config
        self._session: aiohttp.ClientSession | None = None
        self._request_id = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._sse_task: asyncio.Task | None = None
        self._message_endpoint: str | None = None
        self._endpoint_ready: asyncio.Event | None = None
        self._connected = False
        self._closed = False

    @classmethod
    async def create(cls, config: McpSseConfig) -> "McpSseConnection":
        """Create and initialize SSE connection to MCP server."""
        conn = cls(config)
        await conn._connect()
        return conn

    async def _connect(self) -> None:
        """Establish SSE connection and perform MCP handshake."""
        headers = dict(self._config.headers)
        headers.setdefault("Accept", "text/event-stream")

        self._session = aiohttp.ClientSession(headers=headers)
        self._endpoint_ready = asyncio.Event()

        # Start SSE listener task
        self._sse_task = asyncio.create_task(self._sse_reader())

        # Wait for endpoint event (with timeout)
        try:
            await asyncio.wait_for(self._endpoint_ready.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            # Some servers don't send endpoint event - use default
            logger.debug("No endpoint event received, using default")
            if not self._message_endpoint:
                base_url = self._config.url
                if base_url.endswith("/sse"):
                    self._message_endpoint = base_url[:-4] + "/message"
                else:
                    self._message_endpoint = base_url.rstrip("/") + "/message"

        # MCP initialize handshake
        try:
            result = await self.call(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "albus", "version": "1.0.0"},
                },
                timeout_ms=10_000,
            )
            self._connected = True
            logger.info("MCP SSE server %s initialized", self._config.id)

            # Send initialized notification (required by MCP protocol)
            await self._send_notification("notifications/initialized", {})

        except Exception as e:
            await self.close()
            raise McpSseProtocolError(
                f"Failed to initialize SSE connection to {self._config.id}: {e}"
            ) from e

    async def _sse_reader(self) -> None:
        """Read SSE events from server and dispatch to pending requests."""
        retry_count = 0
        max_retries = self._config.retry_attempts

        while not self._closed and retry_count < max_retries:
            try:
                async with self._session.get(self._config.url) as resp:
                    if resp.status != 200:
                        raise McpSseProtocolError(
                            f"SSE connection failed: HTTP {resp.status}"
                        )

                    retry_count = 0  # Reset on successful connection
                    event_type = None
                    data_lines: list[str] = []

                    async for line in resp.content:
                        if self._closed:
                            break

                        line_str = line.decode("utf-8").rstrip("\r\n")

                        if line_str.startswith("event:"):
                            event_type = line_str[6:].strip()
                        elif line_str.startswith("data:"):
                            data_lines.append(line_str[5:].strip())
                        elif line_str == "":
                            # Empty line = end of event
                            if data_lines:
                                data = "\n".join(data_lines)
                                await self._handle_sse_event(event_type, data)
                            event_type = None
                            data_lines = []

            except asyncio.CancelledError:
                break
            except aiohttp.ClientError as e:
                retry_count += 1
                if retry_count < max_retries and not self._closed:
                    logger.warning(
                        "SSE connection lost for %s, retrying (%d/%d): %s",
                        self._config.id,
                        retry_count,
                        max_retries,
                        e,
                    )
                    await asyncio.sleep(1.0 * retry_count)  # Exponential backoff
                else:
                    logger.error(
                        "SSE connection failed for %s after %d retries",
                        self._config.id,
                        retry_count,
                    )
                    # Fail all pending requests
                    for fut in self._pending.values():
                        if not fut.done():
                            fut.set_exception(e)
                    break
            except Exception as e:
                logger.error("SSE reader error for %s: %s", self._config.id, e)
                for fut in self._pending.values():
                    if not fut.done():
                        fut.set_exception(e)
                break

    async def _handle_sse_event(self, event_type: str | None, data: str) -> None:
        """Process an SSE event."""
        try:
            # MCP SSE sends endpoint info on connect
            if event_type == "endpoint":
                # Server tells us where to POST requests
                endpoint = data.strip()
                # Handle relative paths by combining with base URL
                if endpoint.startswith("/"):
                    # Relative path - combine with base URL
                    from urllib.parse import urlparse, urlunparse

                    parsed = urlparse(self._config.url)
                    self._message_endpoint = urlunparse(
                        (parsed.scheme, parsed.netloc, endpoint, "", "", "")
                    )
                else:
                    # Absolute URL
                    self._message_endpoint = endpoint
                logger.debug(
                    "MCP SSE %s message endpoint: %s",
                    self._config.id,
                    self._message_endpoint,
                )
                # Signal that we're ready to make requests
                if self._endpoint_ready:
                    self._endpoint_ready.set()
                return

            # Parse JSON-RPC message
            msg = json.loads(data)
            msg_id = msg.get("id")

            if msg_id is not None and msg_id in self._pending:
                fut = self._pending.pop(msg_id)
                if "error" in msg:
                    error = msg["error"]
                    error_msg = (
                        error.get("message", str(error))
                        if isinstance(error, dict)
                        else str(error)
                    )
                    fut.set_exception(McpSseProtocolError(error_msg))
                else:
                    fut.set_result(msg.get("result"))
            elif "method" in msg:
                # Server-initiated notification/request (e.g., progress)
                logger.debug(
                    "MCP SSE %s notification: %s", self._config.id, msg.get("method")
                )

        except json.JSONDecodeError as e:
            logger.warning(
                "Invalid JSON from MCP SSE server %s: %s", self._config.id, e
            )

    def is_alive(self) -> bool:
        """Check if the SSE connection is still active."""
        return self._connected and not self._closed and self._sse_task is not None

    async def call(
        self,
        method: str,
        params: dict[str, Any],
        timeout_ms: int | None = None,
    ) -> Any:
        """Send JSON-RPC request via HTTP POST, await response via SSE."""
        self._request_id += 1
        req_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        # Create future for response
        fut: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut

        # Determine POST endpoint
        endpoint = self._message_endpoint
        if not endpoint:
            # Default: replace /sse with /message, or append /message
            base_url = self._config.url
            if base_url.endswith("/sse"):
                endpoint = base_url[:-4] + "/message"
            else:
                endpoint = base_url.rstrip("/") + "/message"

        try:
            async with self._session.post(endpoint, json=request) as resp:
                # MCP SSE typically returns 202 Accepted (response comes via SSE)
                # Some servers may return 200 with immediate response
                if resp.status == 200:
                    # Immediate response in body
                    result = await resp.json()
                    self._pending.pop(req_id, None)
                    if "error" in result:
                        raise McpSseProtocolError(result["error"])
                    return result.get("result")
                elif resp.status not in (202, 204):
                    self._pending.pop(req_id, None)
                    raise McpSseProtocolError(
                        f"MCP request failed: HTTP {resp.status} - {await resp.text()}"
                    )
        except aiohttp.ClientError as e:
            self._pending.pop(req_id, None)
            raise McpSseProtocolError(f"Failed to send request: {e}") from e

        # Wait for response via SSE
        timeout = (timeout_ms or self._config.timeout_ms) / 1000
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise McpSseTimeoutError(
                f"Timeout calling {method} on {self._config.id}"
            ) from None

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        endpoint = self._message_endpoint
        if not endpoint:
            base_url = self._config.url
            if base_url.endswith("/sse"):
                endpoint = base_url[:-4] + "/message"
            else:
                endpoint = base_url.rstrip("/") + "/message"

        try:
            async with self._session.post(endpoint, json=notification) as resp:
                if resp.status not in (200, 202, 204):
                    logger.warning(
                        "Notification %s failed: HTTP %s", method, resp.status
                    )
        except aiohttp.ClientError as e:
            logger.warning("Failed to send notification %s: %s", method, e)

    async def close(self) -> None:
        """Close the SSE connection."""
        self._closed = True
        self._connected = False

        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None

        if self._session:
            await self._session.close()
            self._session = None

        # Fail any remaining pending requests
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(McpSseProtocolError("Connection closed"))
        self._pending.clear()


class McpSseProtocolError(Exception):
    """MCP SSE protocol error."""

    pass


class McpSseTimeoutError(Exception):
    """MCP SSE request timeout."""

    pass


__all__ = [
    "McpSseConfig",
    "McpSseConnection",
    "McpTool",
    "McpSseProtocolError",
    "McpSseTimeoutError",
]

