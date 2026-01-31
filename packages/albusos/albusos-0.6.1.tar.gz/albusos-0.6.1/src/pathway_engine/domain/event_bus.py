"""AsyncEventBus - minimal async pub/sub for streaming nodes.

This is intentionally tiny and dependency-free.

Why this exists:
- `observe.inner(...).stream()` needs an async subscription primitive.
- The PathwayVM emits execution events; we can publish them into this bus.
- Nodes can then consume those events via `ctx.extras["event_bus"]`.

This module is part of `pathway_engine` (not `albus`) to avoid coupling
streaming node semantics to any particular app/runtime.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator


class AsyncEventBus:
    """Simple channel-based async pub/sub.

    - `publish(channel, event)` broadcasts to all subscribers of that channel.
    - `subscribe(channel)` returns an async iterator that yields events.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(
            list
        )

    def publish(self, channel: str, event: dict[str, Any]) -> None:
        queues = list(self._subscribers.get(channel, []))
        if not queues:
            return
        for q in queues:
            # Best-effort; drop if queue is full.
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def subscribe(
        self,
        channel: str,
        *,
        max_queue_size: int = 1000,
    ) -> AsyncIterator[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self._subscribers[channel].append(q)
        try:
            while True:
                yield await q.get()
        finally:
            try:
                self._subscribers[channel].remove(q)
            except ValueError:
                pass


__all__ = ["AsyncEventBus"]
