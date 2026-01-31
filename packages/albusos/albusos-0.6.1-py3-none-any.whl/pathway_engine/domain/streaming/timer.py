"""Timer Event Source - Emit events on interval.

VM primitive for time-based triggers.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator

from pathway_engine.domain.streaming.registry import register_streaming_handler


async def timer_interval(inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Non-streaming call: returns configuration."""
    seconds = float(inputs.get("seconds", 60.0))
    jitter = float(inputs.get("jitter_seconds", 0.0))
    return {"streaming": True, "seconds": seconds, "jitter_seconds": jitter}


async def timer_interval_stream(
    inputs: dict[str, Any], ctx: Any
) -> AsyncIterator[dict[str, Any]]:
    """Streaming call: yield events every N seconds."""
    seconds = float(inputs.get("seconds", 60.0))
    jitter = float(inputs.get("jitter_seconds", 0.0))

    # Safety clamp
    if seconds <= 0:
        seconds = 1.0
    if jitter < 0:
        jitter = 0.0

    while True:
        yield {"type": "timer", "timestamp": time.time(), "seconds": seconds}
        sleep_for = seconds
        if jitter:
            sleep_for += jitter * (0.5 - (time.time() % 1))  # deterministic-ish jitter
            if sleep_for < 0.1:
                sleep_for = 0.1
        await asyncio.sleep(sleep_for)


# Register with streaming registry
register_streaming_handler("timer.interval", timer_interval, timer_interval_stream)


__all__ = [
    "timer_interval",
    "timer_interval_stream",
]
