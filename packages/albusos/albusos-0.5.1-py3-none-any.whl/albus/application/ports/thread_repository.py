"""ThreadRepository - Port for thread/agent instance persistence.

Abstracts thread storage from the application layer.
Implementations can use in-memory, file, or database storage.
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from albus.domain.world.thread import AgentInstance


class ThreadRepositoryPort(Protocol):
    """Repository for agent threads/instances.

    This port abstracts storage details from the application layer.
    Implementations handle caching, persistence, etc.
    """

    async def get(self, thread_id: str) -> "AgentInstance | None":
        """Get a thread by ID. Returns None if not found."""
        ...

    async def save(self, instance: "AgentInstance") -> None:
        """Save/update a thread."""
        ...

    async def delete(self, thread_id: str) -> bool:
        """Delete a thread. Returns True if deleted."""
        ...

    async def list(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list["AgentInstance"]:
        """List threads, optionally filtered by workspace."""
        ...

    async def exists(self, thread_id: str) -> bool:
        """Check if a thread exists."""
        ...


__all__ = [
    "ThreadRepositoryPort",
]
