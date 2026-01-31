"""RuntimePort - Transport-facing interface for AlbusRuntime.

This is what transport layers program against.
It defines the contract between transport and the runtime.
"""

from __future__ import annotations

from typing import Any, Protocol


class RuntimePort(Protocol):
    """Transport-facing interface for AlbusRuntime.

    Transport layers (REST, WebSocket, JSON-RPC) should depend on this
    protocol, not the concrete AlbusRuntime class.

    This enables:
    - Testing with mocks
    - Alternative implementations
    - Clear contract definition
    """

    async def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        """Get thread information."""
        ...

    async def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List threads."""
        ...

    async def end_thread(self, thread_id: str) -> bool:
        """End/delete a thread."""
        ...

    def on(self, event_type: str, handler: Any) -> None:
        """Subscribe to events."""
        ...

    def off(self, event_type: str, handler: Any) -> None:
        """Unsubscribe from events."""
        ...

    def on_all(self, handler: Any) -> None:
        """Subscribe to ALL events (useful for streaming transports)."""
        ...

    def off_all(self, handler: Any) -> None:
        """Unsubscribe from ALL events."""
        ...


__all__ = [
    "RuntimePort",
]
