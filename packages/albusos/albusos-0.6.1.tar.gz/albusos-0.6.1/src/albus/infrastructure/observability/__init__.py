"""Observability - Events, emitters, and debugging for Albus.

Usage:
    # Enable debug mode
    albus = AlbusService(debug=True)
    
    # Subscribe to events
    albus.events.on("tool_called", my_handler)
    albus.events.on_all(my_generic_handler)
"""

from albus.infrastructure.observability.events import (
    EventType,
    Event,
    NodeInfo,
    StateTransitionEvent,
    TurnStartedEvent,
    TurnCompletedEvent,
    TurnFailedEvent,
    PathwayCreatedEvent,
    PathwayStartedEvent,
    PathwayCompletedEvent,
    NodeStartedEvent,
    NodeCompletedEvent,
    NodeFailedEvent,
    ToolCalledEvent,
    ToolCompletedEvent,
    ToolFailedEvent,
    LLMRequestEvent,
    LLMResponseEvent,
    EventHandler,
)

from albus.infrastructure.observability.emitter import EventEmitter
from albus.infrastructure.observability.debug import DebugHandler
from albus.infrastructure.observability.run_recorder import RunRecorder
from albus.infrastructure.observability.spans import Span, SpanKind, SpanStatus


__all__ = [
    # Core
    "EventType",
    "Event",
    "EventEmitter",
    "EventHandler",
    "NodeInfo",
    # Debug
    "DebugHandler",
    "RunRecorder",
    "Span",
    "SpanKind",
    "SpanStatus",
    # Event types
    "StateTransitionEvent",
    "TurnStartedEvent",
    "TurnCompletedEvent",
    "TurnFailedEvent",
    "PathwayCreatedEvent",
    "PathwayStartedEvent",
    "PathwayCompletedEvent",
    "NodeStartedEvent",
    "NodeCompletedEvent",
    "NodeFailedEvent",
    "ToolCalledEvent",
    "ToolCompletedEvent",
    "ToolFailedEvent",
    "LLMRequestEvent",
    "LLMResponseEvent",
]
