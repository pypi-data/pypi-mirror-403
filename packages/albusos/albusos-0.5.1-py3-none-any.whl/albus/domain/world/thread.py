"""Agent runtime thread state.

This module defines the runtime state of an agent (AgentInstance) and its
associated context (AgentContext).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentInstanceStatus(str, Enum):
    """Status of an agent instance."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    TERMINATED = "terminated"
    ERROR = "error"


class AgentContext(BaseModel):
    """Persistent context for an agent instance.

    This is the agent's "memory" - it persists across events and restarts.
    The context is updated by pathway executions and state transitions.
    """

    model_config = {"extra": "allow"}

    # Core context data (agent-specific)
    data: dict[str, Any] = Field(default_factory=dict)

    # System-managed context
    last_event: str | None = Field(
        default=None, description="Last event that was processed"
    )
    last_event_at: datetime | None = Field(default=None)
    transition_count: int = Field(
        default=0, description="Total transitions since spawn"
    )

    # Conversation context (for chat-based agents)
    messages: list[dict[str, Any]] = Field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in context data."""
        self.data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        """Update context data with multiple values."""
        self.data.update(values)


class AgentInstance(BaseModel):
    """A running instance of a state machine.

    This represents a "live" agent. It has:
    - A unique identity
    - A reference to its state machine definition
    - Current state
    - Persistent context

    AgentInstance is what gets persisted to persistence.
    """

    model_config = {"extra": "allow"}

    # Identity
    id: str = Field(min_length=1, description="Unique instance identifier")
    state_machine_id: str = Field(
        description="ID of the StateMachine this instance runs"
    )

    # Current state
    current_state: str = Field(description="ID of the current state")
    status: AgentInstanceStatus = Field(default=AgentInstanceStatus.RUNNING)

    # Persistent context
    context: AgentContext = Field(default_factory=AgentContext)

    # Workspace/ownership
    workspace_id: str | None = Field(default=None)
    created_by: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_event_at: datetime | None = Field(default=None)

    # Error tracking
    error: str | None = Field(default=None)
    error_count: int = Field(default=0)


__all__ = [
    "AgentContext",
    "AgentInstance",
    "AgentInstanceStatus",
]
