"""Agent runtime state - persisted between interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Runtime state for an agent instance.

    This is what gets persisted between interactions.
    """

    thread_id: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    working_memory: dict[str, Any] = field(default_factory=dict)
    learned: list[dict[str, Any]] = field(default_factory=list)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    last_active: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "messages": self.messages,
            "working_memory": self.working_memory,
            "learned": self.learned,
            "pending_actions": self.pending_actions,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        return cls(
            thread_id=data.get("thread_id"),
            messages=data.get("messages", []),
            working_memory=data.get("working_memory", {}),
            learned=data.get("learned", []),
            pending_actions=data.get("pending_actions", []),
            last_active=data.get("last_active"),
        )


__all__ = ["AgentState"]
