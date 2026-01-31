"""Streaming Primitives - VM-internal event sources.

These are fundamental to the pathway VM's streaming execution model:
- Timer intervals for scheduled triggers
- Webhook bus for event-driven triggers
- Event bus for internal pathway events

This module is NOT a general-purpose tool library.
It's part of the VM's execution infrastructure.
"""

from __future__ import annotations

from pathway_engine.domain.streaming.event_bus import (
    WebhookBus,
    WEBHOOK_BUS,
)
from pathway_engine.domain.streaming.timer import (
    timer_interval,
    timer_interval_stream,
)
from pathway_engine.domain.streaming.webhook import (
    webhook_listen,
    webhook_listen_stream,
    webhook_publish,
)
from pathway_engine.domain.streaming.registry import (
    STREAMING_HANDLERS,
    get_streaming_handler,
    register_streaming_handler,
)

__all__ = [
    # Event bus
    "WebhookBus",
    "WEBHOOK_BUS",
    # Timer
    "timer_interval",
    "timer_interval_stream",
    # Webhook
    "webhook_listen",
    "webhook_listen_stream",
    "webhook_publish",
    # Registry
    "STREAMING_HANDLERS",
    "get_streaming_handler",
    "register_streaming_handler",
]
