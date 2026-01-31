"""Streaming Nodes - Live event sources and introspection.

These nodes don't complete once - they yield events over time.

Usage:
    # External event source
    watch = EventSourceNode(
        source="file.watch",
        config={"path": "/workspace"},
    )
    
    # Internal introspection
    monitor = IntrospectionNode(
        source="pathway.events",
        filter={"event_type": "node_completed"},
    )
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal

from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.context import Context


class EventSourceNode(NodeBase):
    """A node that subscribes to external event streams.

    Unlike compute nodes, this yields events over time.
    Use with streaming VM execution.

    Attributes:
        source: Event source identifier (e.g., "file.watch", "timer.interval")
        config: Source-specific configuration
        buffer_size: Max events to buffer before backpressure
    """

    type: Literal["event_source"] = "event_source"
    source: str
    config: dict[str, Any] = Field(default_factory=dict)
    buffer_size: int = 100

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """For batch execution, return immediately with stream info."""
        return {
            "streaming": True,
            "source": self.source,
            "config": self.config,
            "message": "Use stream() for continuous events",
        }

    async def stream(
        self, inputs: dict[str, Any], ctx: Context
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield events from the source continuously.

        Looks up handlers from:
        1. Internal streaming registry (VM primitives)
        2. Context tools (user-provided)
        """
        # First check internal streaming registry
        from pathway_engine.domain.streaming import get_streaming_handler

        handler = get_streaming_handler(self.source)

        # Fall back to context tools
        if not handler:
            handler = ctx.tools.get(self.source)

        if not handler:
            yield {"error": f"Event source not available: {self.source}"}
            return

        # Merge config with inputs
        stream_config = {**self.config, **inputs}

        # Check if handler supports streaming
        if hasattr(handler, "stream"):
            async for event in handler.stream(stream_config, ctx):
                yield {"event": event, "source": self.source}
        else:
            # Fall back to polling
            import asyncio

            interval = stream_config.get("poll_interval", 1.0)
            while True:
                try:
                    result = await handler(stream_config, ctx)
                    yield {"event": result, "source": self.source, "polled": True}
                except Exception as e:
                    yield {"error": str(e), "source": self.source}
                await asyncio.sleep(interval)


class IntrospectionNode(NodeBase):
    """A node that observes internal Albus events.

    This enables metacognition - Albus watching his own processes.

    Attributes:
        source: What to observe:
            - "pathway.events" - pathway execution events
            - "attention.state" - current attention budget
            - "goals.active" - active goal stack
            - "memory.recent" - recent working memory
            - "errors.recent" - recent errors
        filter: Optional filter criteria
        window: Time window in seconds (for aggregation)
    """

    type: Literal["introspection"] = "introspection"
    source: Literal[
        "pathway.events",
        "attention.state",
        "goals.active",
        "memory.recent",
        "errors.recent",
        "metrics.recent",
    ]
    filter: dict[str, Any] = Field(default_factory=dict)
    window: float = 60.0  # seconds

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Get current snapshot of internal state."""

        if self.source == "pathway.events":
            return await self._get_pathway_events(ctx)
        elif self.source == "attention.state":
            return await self._get_attention_state(ctx)
        elif self.source == "goals.active":
            return await self._get_active_goals(ctx)
        elif self.source == "memory.recent":
            return await self._get_recent_memory(ctx)
        elif self.source == "errors.recent":
            return await self._get_recent_errors(ctx)
        elif self.source == "metrics.recent":
            return await self._get_recent_metrics(ctx)
        else:
            return {"error": f"Unknown introspection source: {self.source}"}

    async def _get_pathway_events(self, ctx: Context) -> dict[str, Any]:
        """Get recent pathway execution events."""
        event_buffer = ctx.extras.get("event_buffer", [])

        # Apply filter
        filtered = []
        for event in event_buffer[-100:]:  # Last 100 events
            if self._matches_filter(event):
                filtered.append(event)

        return {
            "events": filtered,
            "count": len(filtered),
            "source": "pathway.events",
        }

    async def _get_attention_state(self, ctx: Context) -> dict[str, Any]:
        """Get current attention/resource state."""
        context_manager = ctx.extras.get("context_manager")
        if context_manager:
            return {
                "total_tokens_used": context_manager.total_input_tokens
                + context_manager.total_output_tokens,
                "total_cost_usd": context_manager.total_cost_usd,
                "call_count": context_manager.call_count,
                "available_tokens": context_manager.available_tokens(),
                "source": "attention.state",
            }
        return {
            "available": True,
            "source": "attention.state",
            "message": "No context manager found",
        }

    async def _get_active_goals(self, ctx: Context) -> dict[str, Any]:
        """Get active goals from goal stack."""
        goals = ctx.extras.get("goals", [])
        return {
            "goals": goals,
            "count": len(goals),
            "source": "goals.active",
        }

    async def _get_recent_memory(self, ctx: Context) -> dict[str, Any]:
        """Get recent items from working memory."""
        working_memory = ctx.extras.get("working_memory", [])
        return {
            "items": working_memory[-10:],  # Last 10 items
            "count": len(working_memory),
            "source": "memory.recent",
        }

    async def _get_recent_errors(self, ctx: Context) -> dict[str, Any]:
        """Get recent errors."""
        errors = ctx.extras.get("error_buffer", [])
        return {
            "errors": errors[-10:],  # Last 10 errors
            "count": len(errors),
            "source": "errors.recent",
        }

    async def _get_recent_metrics(self, ctx: Context) -> dict[str, Any]:
        """Get recent performance metrics."""
        metrics = ctx.extras.get("metrics_buffer", [])

        # Aggregate recent metrics
        if not metrics:
            return {"source": "metrics.recent", "message": "No metrics available"}

        recent = metrics[-50:]  # Last 50 data points
        durations = [m.get("duration_ms", 0) for m in recent if "duration_ms" in m]

        return {
            "count": len(recent),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "source": "metrics.recent",
        }

    def _matches_filter(self, event: dict[str, Any]) -> bool:
        """Check if event matches filter criteria."""
        if not self.filter:
            return True

        for key, value in self.filter.items():
            if event.get(key) != value:
                return False
        return True

    async def stream(
        self, inputs: dict[str, Any], ctx: Context
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream internal events continuously."""
        import asyncio

        # Get async event bus if available.
        bus = ctx.services.event_bus

        if bus and hasattr(bus, "subscribe"):
            # If bus supports subscription
            async for event in bus.subscribe(self.source):
                if self._matches_filter(event):
                    yield {"event": event, "source": self.source}
        else:
            # Fall back to polling compute()
            while True:
                result = await self.compute(inputs, ctx)
                yield result
                await asyncio.sleep(1.0)


__all__ = [
    "EventSourceNode",
    "IntrospectionNode",
]
