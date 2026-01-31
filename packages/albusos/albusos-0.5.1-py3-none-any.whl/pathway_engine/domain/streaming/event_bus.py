"""WebhookBus - In-memory pub/sub for webhook events.

This is a process-local event bus for webhook payloads.
External HTTP requests publish to topics, and triggers subscribe.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WebhookBus:
    """In-memory pub/sub bus for webhook events (process-local)."""

    _topics: dict[str, list[asyncio.Queue[dict[str, Any]]]] = field(
        default_factory=dict
    )

    def subscribe(
        self, topic: str, *, max_queue: int = 1000
    ) -> asyncio.Queue[dict[str, Any]]:
        """Subscribe to a topic. Returns a queue that receives events."""
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue)
        self._topics.setdefault(topic, []).append(q)
        return q

    def unsubscribe(self, topic: str, q: asyncio.Queue[dict[str, Any]]) -> None:
        """Unsubscribe a queue from a topic."""
        subs = self._topics.get(topic, [])
        if q in subs:
            subs.remove(q)
        if not subs and topic in self._topics:
            del self._topics[topic]

    def publish(self, topic: str, payload: dict[str, Any]) -> int:
        """Publish to a topic. Returns number of subscribers delivered-to (best-effort)."""
        subs = list(self._topics.get(topic, []))
        delivered = 0
        for q in subs:
            try:
                q.put_nowait(payload)
                delivered += 1
            except asyncio.QueueFull:
                # Drop under backpressure
                continue
            except Exception:
                continue
        return delivered

    def topic_count(self) -> int:
        """Number of active topics."""
        return len(self._topics)

    def subscriber_count(self, topic: str) -> int:
        """Number of subscribers for a topic."""
        return len(self._topics.get(topic, []))


# Global singleton for the process
WEBHOOK_BUS = WebhookBus()


__all__ = [
    "WebhookBus",
    "WEBHOOK_BUS",
]
