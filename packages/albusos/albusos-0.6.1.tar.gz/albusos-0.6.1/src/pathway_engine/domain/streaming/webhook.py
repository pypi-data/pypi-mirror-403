"""Webhook Event Sources - Listen to and publish webhook events.

VM primitives for event-driven triggers.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from pathway_engine.domain.streaming.event_bus import WEBHOOK_BUS
from pathway_engine.domain.streaming.registry import register_streaming_handler


async def webhook_listen(inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Non-streaming call: returns subscription info."""
    topic = str(inputs.get("topic", "")).strip()
    if not topic:
        return {"success": False, "error": "topic is required"}
    return {"streaming": True, "topic": topic}


async def webhook_listen_stream(
    inputs: dict[str, Any], ctx: Any
) -> AsyncIterator[dict[str, Any]]:
    """Streaming call: yield webhook events for a topic."""
    topic = str(inputs.get("topic", "")).strip()
    if not topic:
        yield {"error": "topic is required"}
        return

    q = WEBHOOK_BUS.subscribe(topic)
    try:
        while True:
            payload = await q.get()
            yield {"type": "webhook", "topic": topic, "payload": payload}
    finally:
        WEBHOOK_BUS.unsubscribe(topic, q)


async def webhook_publish(inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Publish an event to the webhook bus."""
    topic = str(inputs.get("topic", "")).strip()
    if not topic:
        return {"success": False, "error": "topic is required"}
    payload = inputs.get("payload")
    if not isinstance(payload, dict):
        return {"success": False, "error": "payload must be an object"}
    delivered = WEBHOOK_BUS.publish(topic, payload)
    return {"success": True, "topic": topic, "delivered": delivered}


# Register with streaming registry
register_streaming_handler("webhook.listen", webhook_listen, webhook_listen_stream)
register_streaming_handler("webhook.publish", webhook_publish, None)


__all__ = [
    "webhook_listen",
    "webhook_listen_stream",
    "webhook_publish",
]
