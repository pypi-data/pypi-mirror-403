"""WorldStore port - Thread and artifact persistence.

Abstracts storage for threads, messages, artifacts.
This replaces the old ThreadStorePort.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WorldStorePort(Protocol):
    """Interface for thread persistence.

    Threads are conversation sessions that:
    - Persist across app restarts
    - Can be resumed
    - Track message history and context
    """

    def save_thread(self, thread_id: str, data: dict[str, Any]) -> None:
        """Save or update a thread.

        Args:
            thread_id: Unique thread identifier
            data: Thread data (AgentInstance serialized as dict)
        """
        ...

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        """Load a thread by ID.

        Args:
            thread_id: Thread identifier

        Returns:
            Thread data as dict, or None if not found
        """
        ...

    def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List threads, optionally filtered by workspace.

        Args:
            workspace_id: Filter by workspace (None = all workspaces)
            limit: Max threads to return
            offset: Pagination offset

        Returns:
            List of thread data dicts
        """
        ...

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    def count_threads(self, *, workspace_id: str | None = None) -> int:
        """Count threads, optionally filtered by workspace.

        Args:
            workspace_id: Filter by workspace (None = all workspaces)

        Returns:
            Thread count
        """
        ...


class NullWorldStore:
    """Null implementation for when persistence is disabled."""

    def save_thread(self, thread_id: str, data: dict[str, Any]) -> None:
        pass

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        return None

    def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return []

    def delete_thread(self, thread_id: str) -> bool:
        return False

    def count_threads(self, *, workspace_id: str | None = None) -> int:
        return 0


__all__ = ["WorldStorePort", "NullWorldStore"]
