"""Streaming Handler Registry - VM-internal streaming sources.

Unlike the stdlib tool registry, this is specifically for
streaming event sources that the VM uses internally.
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable, AsyncIterator

# Type for streaming handlers
# Regular call: async (inputs, ctx) -> dict
# Stream call: handler.stream(inputs, ctx) -> AsyncIterator[dict]
StreamingHandler = Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]

# Registry of streaming handlers by source name
STREAMING_HANDLERS: dict[str, StreamingHandler] = {}


def register_streaming_handler(
    source: str,
    handler: StreamingHandler,
    stream_fn: (
        Callable[[dict[str, Any], Any], AsyncIterator[dict[str, Any]]] | None
    ) = None,
) -> None:
    """Register a streaming handler.

    Args:
        source: Source identifier (e.g., "timer.interval")
        handler: Async callable for non-streaming calls
        stream_fn: Optional async iterator for streaming calls
    """
    if stream_fn is not None:
        setattr(handler, "stream", stream_fn)
    STREAMING_HANDLERS[source] = handler


def get_streaming_handler(source: str) -> StreamingHandler | None:
    """Get a streaming handler by source name."""
    return STREAMING_HANDLERS.get(source)


__all__ = [
    "STREAMING_HANDLERS",
    "register_streaming_handler",
    "get_streaming_handler",
]
