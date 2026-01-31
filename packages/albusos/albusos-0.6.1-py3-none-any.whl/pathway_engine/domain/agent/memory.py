"""Agent memory configuration and scoping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MemoryScope(str, Enum):
    """Where memory is scoped."""

    TURN = "turn"  # Single turn only
    THREAD = "thread"  # Conversation session
    AGENT = "agent"  # All conversations for this agent
    GLOBAL = "global"  # Shared across agents


@dataclass
class AgentMemoryConfig:
    """Configuration for agent memory layers.

    Agents have multiple memory scopes:
    - short_term: Within a conversation (thread-scoped)
    - long_term: Across conversations (agent-scoped)
    - working: Current task state (turn-scoped)

    Each scope maps to a namespace in the memory store.
    """

    short_term: MemoryScope = MemoryScope.THREAD
    long_term: MemoryScope = MemoryScope.AGENT
    namespace: str = "default"
    short_term_limit: int = 50
    auto_summarize: bool = True

    def short_term_ns(self, thread_id: str) -> str:
        """Get namespace for short-term memory."""
        return f"{self.namespace}:thread:{thread_id}"

    def long_term_ns(self) -> str:
        """Get namespace for long-term memory."""
        return f"{self.namespace}:agent"


__all__ = [
    "MemoryScope",
    "AgentMemoryConfig",
]
