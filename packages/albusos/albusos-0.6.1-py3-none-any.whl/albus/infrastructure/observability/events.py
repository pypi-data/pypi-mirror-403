"""Observability Events - Typed events emitted during Albus execution.

Subscribe to these events for debugging, monitoring, analytics, etc.

Usage:
    albus = AlbusService(debug=True)  # Auto-subscribes debug handler
    
    # Or subscribe manually:
    albus.on("state_transition", my_handler)
    albus.on("node_executed", my_handler)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable


class EventType(str, Enum):
    """All event types emitted by Albus."""

    # State machine events
    STATE_TRANSITION = "state_transition"
    STATE_MACHINE_ERROR = "state_machine_error"

    # Turn lifecycle
    TURN_STARTED = "turn_started"
    TURN_COMPLETED = "turn_completed"
    TURN_FAILED = "turn_failed"

    # Pathway lifecycle
    PATHWAY_CREATED = "pathway_created"
    PATHWAY_STARTED = "pathway_started"
    PATHWAY_COMPLETED = "pathway_completed"

    # Node execution
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"

    # Tool calling
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"

    # LLM
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"


@dataclass
class Event:
    """Base event class."""

    type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    thread_id: str | None = None
    turn_id: str | None = None
    # Correlation ID for the underlying execution (PathwayVM execution_id).
    # This is the canonical run identifier for persistence/tracing.
    execution_id: str | None = None
    # Agent that triggered this event (if applicable)
    agent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "thread_id": self.thread_id,
            "turn_id": self.turn_id,
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
        }


@dataclass
class StateTransitionEvent(Event):
    """Emitted when state machine transitions."""

    type: EventType = field(default=EventType.STATE_TRANSITION)
    from_state: str = ""
    to_state: str = ""
    trigger: str = ""
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update(
            {
                "from_state": self.from_state,
                "to_state": self.to_state,
                "trigger": self.trigger,
                "duration_ms": self.duration_ms,
            }
        )
        return d


@dataclass
class TurnEvent(Event):
    """Emitted for turn lifecycle."""

    message: str = ""
    response: str | None = None
    duration_ms: float | None = None
    success: bool = True
    error: str | None = None


@dataclass
class TurnStartedEvent(TurnEvent):
    type: EventType = field(default=EventType.TURN_STARTED)


@dataclass
class TurnCompletedEvent(TurnEvent):
    type: EventType = field(default=EventType.TURN_COMPLETED)


@dataclass
class TurnFailedEvent(TurnEvent):
    type: EventType = field(default=EventType.TURN_FAILED)
    success: bool = False


@dataclass
class NodeInfo:
    """Info about a node in a pathway."""

    id: str
    type: str
    prompt: str | None = None  # For LLM nodes


@dataclass
class PathwayEvent(Event):
    """Emitted for pathway execution."""

    pathway_id: str = ""
    pathway_name: str | None = None
    node_count: int = 0
    duration_ms: float | None = None
    success: bool = True
    outputs: dict[str, Any] = field(default_factory=dict)


@dataclass
class PathwayCreatedEvent(PathwayEvent):
    """Emitted when a pathway is created."""

    type: EventType = field(default=EventType.PATHWAY_CREATED)
    nodes: list[NodeInfo] = field(default_factory=list)
    connections: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class PathwayStartedEvent(PathwayEvent):
    type: EventType = field(default=EventType.PATHWAY_STARTED)
    nodes: list[NodeInfo] = field(default_factory=list)


@dataclass
class PathwayCompletedEvent(PathwayEvent):
    type: EventType = field(default=EventType.PATHWAY_COMPLETED)


@dataclass
class NodeEvent(Event):
    """Emitted for node execution."""

    node_id: str = ""
    node_type: str = ""
    pathway_id: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None
    success: bool = True
    error: str | None = None


@dataclass
class NodeStartedEvent(NodeEvent):
    type: EventType = field(default=EventType.NODE_STARTED)


@dataclass
class NodeCompletedEvent(NodeEvent):
    type: EventType = field(default=EventType.NODE_COMPLETED)


@dataclass
class NodeFailedEvent(NodeEvent):
    type: EventType = field(default=EventType.NODE_FAILED)
    success: bool = False


@dataclass
class ToolEvent(Event):
    """Emitted for tool calls."""

    # Optional linkage for trace trees (when tool calls happen inside nodes).
    pathway_id: str | None = None
    node_id: str | None = None
    call_id: str | None = None

    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    duration_ms: float | None = None
    success: bool = True
    error: str | None = None


@dataclass
class ToolCalledEvent(ToolEvent):
    type: EventType = field(default=EventType.TOOL_CALLED)


@dataclass
class ToolCompletedEvent(ToolEvent):
    type: EventType = field(default=EventType.TOOL_COMPLETED)


@dataclass
class ToolFailedEvent(ToolEvent):
    type: EventType = field(default=EventType.TOOL_FAILED)
    success: bool = False


@dataclass
class LLMEvent(Event):
    """Emitted for LLM calls."""

    # Optional linkage for trace trees (when LLM calls happen inside nodes).
    pathway_id: str | None = None
    node_id: str | None = None
    call_id: str | None = None

    model: str = ""
    prompt: str = ""
    response: str = ""
    tokens_in: int | None = None
    tokens_out: int | None = None
    duration_ms: float | None = None


@dataclass
class LLMRequestEvent(LLMEvent):
    type: EventType = field(default=EventType.LLM_REQUEST)


@dataclass
class LLMResponseEvent(LLMEvent):
    type: EventType = field(default=EventType.LLM_RESPONSE)


# Type alias for event handlers
EventHandler = Callable[[Event], None] | Callable[[Event], Awaitable[None]]


__all__ = [
    "EventType",
    "Event",
    "NodeInfo",
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
    "EventHandler",
]
