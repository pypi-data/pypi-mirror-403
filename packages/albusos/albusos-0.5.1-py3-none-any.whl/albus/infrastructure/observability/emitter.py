"""Event Emitter - Pub/sub system for observability events.

Usage:
    emitter = EventEmitter()
    emitter.on("state_transition", my_handler)
    emitter.emit(StateTransitionEvent(...))
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Awaitable

from albus.infrastructure.observability.events import Event, EventType, EventHandler

logger = logging.getLogger(__name__)


class EventEmitter:
    """Simple event emitter with sync and async handler support."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._all_handlers: list[EventHandler] = []

    def on(self, event_type: str | EventType, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._handlers[key].append(handler)

    def on_all(self, handler: EventHandler) -> None:
        """Subscribe to ALL events."""
        self._all_handlers.append(handler)

    def off(self, event_type: str | EventType, handler: EventHandler) -> None:
        """Unsubscribe from a specific event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if handler in self._handlers[key]:
            self._handlers[key].remove(handler)

    def off_all(self, handler: EventHandler) -> None:
        """Unsubscribe from all events."""
        if handler in self._all_handlers:
            self._all_handlers.remove(handler)

    def emit(self, event: Event) -> None:
        """Emit an event to all subscribers (sync)."""
        key = event.type.value

        # Call specific handlers
        for handler in self._handlers[key]:
            try:
                result = handler(event)
                # If handler is async, log warning (should use emit_async)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.warning("Event handler error for %s: %s", key, e)

        # Call all-event handlers
        for handler in self._all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.warning("Event handler error (all): %s", e)

    async def emit_async(self, event: Event) -> None:
        """Emit an event to all subscribers (async)."""
        key = event.type.value

        # Call specific handlers
        for handler in self._handlers[key]:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning("Event handler error for %s: %s", key, e)

        # Call all-event handlers
        for handler in self._all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning("Event handler error (all): %s", e)


__all__ = ["EventEmitter"]
