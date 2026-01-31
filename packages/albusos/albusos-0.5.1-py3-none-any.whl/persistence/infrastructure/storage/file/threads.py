"""Thread persistence for the file-backed Studio store.

Threads are conversation sessions that persist across restarts.
Each thread is stored as a JSON file: threads/{thread_id}.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def _thread_path(state: FileStoreState, thread_id: str) -> Path:
    """Get the path for a thread file."""
    return state.threads / f"{safe_segment(thread_id)}.json"


def save_thread(state: FileStoreState, thread_id: str, data: dict[str, Any]) -> None:
    """Save or update a thread.

    Args:
        state: File store state
        thread_id: Unique thread identifier
        data: Thread data (AgentInstance serialized as dict)
    """
    path = _thread_path(state, thread_id)

    # Ensure thread_id is in the data
    data = dict(data)
    data["id"] = thread_id
    data["updated_at"] = utcnow_iso()

    atomic_write_json(path, data)


def get_thread(state: FileStoreState, thread_id: str) -> dict[str, Any] | None:
    """Load a thread by ID.

    Args:
        state: File store state
        thread_id: Thread identifier

    Returns:
        Thread data as dict, or None if not found
    """
    path = _thread_path(state, thread_id)
    return read_json_optional(path)


def list_threads(
    state: FileStoreState,
    *,
    workspace_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List threads, optionally filtered by workspace.

    Args:
        state: File store state
        workspace_id: Filter by workspace (None = all)
        limit: Max threads to return
        offset: Pagination offset

    Returns:
        List of thread data dicts, sorted by updated_at descending
    """
    threads = []

    if not state.threads.exists():
        return []

    for path in state.threads.glob("*.json"):
        data = read_json_optional(path)
        if data is None:
            continue

        # Filter by workspace if specified
        if workspace_id is not None:
            if data.get("workspace_id") != workspace_id:
                continue

        threads.append(data)

    # Sort by updated_at descending (most recent first)
    threads.sort(key=lambda t: t.get("updated_at", ""), reverse=True)

    # Apply pagination
    return threads[offset : offset + limit]


def delete_thread(state: FileStoreState, thread_id: str) -> bool:
    """Delete a thread.

    Args:
        state: File store state
        thread_id: Thread identifier

    Returns:
        True if deleted, False if not found
    """
    path = _thread_path(state, thread_id)

    if not path.exists():
        return False

    path.unlink()
    return True


def count_threads(state: FileStoreState, *, workspace_id: str | None = None) -> int:
    """Count threads, optionally filtered by workspace.

    Args:
        state: File store state
        workspace_id: Filter by workspace (None = all)

    Returns:
        Thread count
    """
    if workspace_id is None:
        # Fast path: just count files
        if not state.threads.exists():
            return 0
        return len(list(state.threads.glob("*.json")))

    # Slow path: need to read each file to check workspace
    count = 0
    if not state.threads.exists():
        return 0

    for path in state.threads.glob("*.json"):
        data = read_json_optional(path)
        if data is None:
            continue
        if data.get("workspace_id") == workspace_id:
            count += 1

    return count


__all__ = [
    "save_thread",
    "get_thread",
    "list_threads",
    "delete_thread",
    "count_threads",
]
