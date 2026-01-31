"""ThreadRepository - Implementation of ThreadRepositoryPort.

Handles:
- In-memory caching for fast access
- Persistence to ThreadStorePort (optional)
- Thread ID normalization
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from albus.domain.world.thread import AgentInstance

if TYPE_CHECKING:
    from persistence.application.ports import ThreadStorePort

logger = logging.getLogger(__name__)


class ThreadRepository:
    """Thread repository with caching and optional persistence.

    This replaces the scattered thread management in AlbusService.

    Usage:
        repo = ThreadRepository(store=file_store)

        # Get or None
        thread = await repo.get("thread_123")

        # Save (caches + persists)
        await repo.save(thread)
    """

    def __init__(
        self,
        *,
        store: "ThreadStorePort | None" = None,
    ):
        """Create repository.

        Args:
            store: Optional persistence store. If None, in-memory only.
        """
        self._store = store
        self._cache: dict[str, AgentInstance] = {}

    async def get(self, thread_id: str) -> AgentInstance | None:
        """Get a thread by ID.

        Checks cache first, then persistence.
        """
        # Check cache
        if thread_id in self._cache:
            return self._cache[thread_id]

        # Try persistence
        if self._store is not None:
            stored = self._store.get_thread(thread_id)
            if stored is not None:
                try:
                    instance = AgentInstance.model_validate(stored)
                    self._cache[thread_id] = instance
                    logger.debug("Loaded thread %s from store", thread_id)
                    return instance
                except Exception as e:
                    logger.warning("Failed to load thread %s: %s", thread_id, e)

        return None

    async def save(self, instance: AgentInstance) -> None:
        """Save a thread.

        Updates cache and persists if store available.
        """
        thread_id = self._extract_thread_id(instance)

        # Update cache
        self._cache[thread_id] = instance

        # Persist
        if self._store is not None:
            try:
                data = instance.model_dump(mode="json")
                self._store.save_thread(thread_id, data)
            except Exception as e:
                logger.warning("Failed to persist thread %s: %s", thread_id, e)

    async def delete(self, thread_id: str) -> bool:
        """Delete a thread."""
        deleted = False

        # Remove from cache
        if thread_id in self._cache:
            del self._cache[thread_id]
            deleted = True

        # Remove from persistence
        if self._store is not None:
            if self._store.delete_thread(thread_id):
                deleted = True

        if deleted:
            logger.debug("Deleted thread %s", thread_id)

        return deleted

    async def list(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list[AgentInstance]:
        """List threads."""
        if self._store is None:
            # In-memory only
            threads = list(self._cache.values())
            if workspace_id:
                threads = [t for t in threads if t.workspace_id == workspace_id]
            return threads[:limit]

        # From persistence
        stored = self._store.list_threads(workspace_id=workspace_id, limit=limit)
        instances = []
        for data in stored:
            try:
                instance = AgentInstance.model_validate(data)
                instances.append(instance)
                # Cache while we're at it
                thread_id = self._extract_thread_id(instance)
                self._cache[thread_id] = instance
            except Exception:
                continue

        return instances

    async def exists(self, thread_id: str) -> bool:
        """Check if a thread exists."""
        if thread_id in self._cache:
            return True
        if self._store is not None:
            return self._store.get_thread(thread_id) is not None
        return False

    def _extract_thread_id(self, instance: AgentInstance) -> str:
        """Extract thread_id from instance."""
        return instance.context.data.get("thread_id") or instance.id


__all__ = [
    "ThreadRepository",
]
