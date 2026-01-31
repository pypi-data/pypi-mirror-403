"""Environment abstraction - Where agents live, perceive, and act.

This module defines the core environment abstraction that bridges
agents and their world.

An Environment provides:
- Observation space: What agents can perceive
- Action space: What agents can do
- Event stream: What happens in the world
- Feedback channel: How agents learn

This is the ABSTRACT interface. Concrete implementations live in
persistence (StudioEnvironment) or elsewhere.

The environment abstraction is what allows agents to be portable:
- Same agent can run in different environments
- Same environment can host different agents
- Clear contract between agent and world
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, TypeVar, runtime_checkable

# Type variables for generic environment
ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")
EventType = TypeVar("EventType")
FeedbackType = TypeVar("FeedbackType")


class EnvironmentCapability(str, Enum):
    """Capabilities an environment can provide."""

    # Observation capabilities
    OBSERVE_DOCUMENTS = "observe_documents"
    OBSERVE_STRUCTURE = "observe_structure"
    OBSERVE_EXECUTIONS = "observe_executions"
    OBSERVE_AGENTS = "observe_agents"
    SEMANTIC_SEARCH = "semantic_search"

    # Action capabilities
    CREATE_DOCUMENTS = "create_documents"
    MODIFY_DOCUMENTS = "modify_documents"
    DELETE_DOCUMENTS = "delete_documents"
    EXECUTE_PATHWAYS = "execute_pathways"
    MANAGE_AGENTS = "manage_agents"

    # Learning capabilities
    RECEIVE_FEEDBACK = "receive_feedback"
    UPDATE_WEIGHTS = "update_weights"


@dataclass
class EnvironmentConfig:
    """Configuration for an environment instance.

    Defines what capabilities are available to agents in this environment.
    """

    # Capabilities enabled
    capabilities: set[EnvironmentCapability] = field(default_factory=set)

    # Scope restrictions
    workspace_id: str | None = None  # Restrict to workspace
    allowed_doc_types: list[str] | None = None  # Restrict doc types

    # Resource limits
    max_observations_per_minute: int = 100
    max_actions_per_minute: int = 50

    # Identity
    environment_id: str | None = None
    name: str = "default"

    @classmethod
    def sandboxed(cls, workspace_id: str) -> EnvironmentConfig:
        """Create a sandboxed environment config for user agents."""
        return cls(
            capabilities={
                EnvironmentCapability.OBSERVE_DOCUMENTS,
                EnvironmentCapability.OBSERVE_STRUCTURE,
                EnvironmentCapability.OBSERVE_EXECUTIONS,
                EnvironmentCapability.MODIFY_DOCUMENTS,
                EnvironmentCapability.EXECUTE_PATHWAYS,
                EnvironmentCapability.RECEIVE_FEEDBACK,
            },
            workspace_id=workspace_id,
            name=f"sandbox_{workspace_id}",
        )

    @classmethod
    def privileged(cls) -> EnvironmentConfig:
        """Create a privileged environment config for native agents."""
        return cls(
            capabilities=set(EnvironmentCapability),  # All capabilities
            workspace_id=None,  # No workspace restriction
            name="privileged",
        )


@runtime_checkable
class ObservationSpaceProtocol(Protocol):
    """Protocol for what agents can observe."""

    def observe(self, query: str, **kwargs: Any) -> Any:
        """Make an observation."""
        ...

    def can_observe(self, capability: EnvironmentCapability) -> bool:
        """Check if observation capability is available."""
        ...


@runtime_checkable
class ActionSpaceProtocol(Protocol):
    """Protocol for what agents can do."""

    async def act(self, action: str, **kwargs: Any) -> Any:
        """Perform an action."""
        ...

    def can_act(self, capability: EnvironmentCapability) -> bool:
        """Check if action capability is available."""
        ...


@runtime_checkable
class EventStreamProtocol(Protocol):
    """Protocol for environment events."""

    def subscribe(self, event_type: str, handler: Any) -> Any:
        """Subscribe to events."""
        ...

    async def emit(self, event: Any) -> None:
        """Emit an event."""
        ...


@runtime_checkable
class FeedbackChannelProtocol(Protocol):
    """Protocol for feedback to agents."""

    async def send_feedback(self, feedback: Any) -> None:
        """Send feedback to agent."""
        ...

    async def get_recent_feedback(self, limit: int = 10) -> list[Any]:
        """Get recent feedback."""
        ...


@runtime_checkable
class EnvironmentProtocol(Protocol):
    """Full environment protocol combining all aspects.

    This is what an agent interacts with.
    """

    @property
    def config(self) -> EnvironmentConfig:
        """Get environment configuration."""
        ...

    @property
    def observations(self) -> ObservationSpaceProtocol:
        """Get observation space."""
        ...

    @property
    def actions(self) -> ActionSpaceProtocol:
        """Get action space."""
        ...

    @property
    def events(self) -> EventStreamProtocol:
        """Get event stream."""
        ...

    @property
    def feedback(self) -> FeedbackChannelProtocol:
        """Get feedback channel."""
        ...

    def has_capability(self, capability: EnvironmentCapability) -> bool:
        """Check if environment has a capability."""
        ...


class BaseEnvironment(ABC):
    """Abstract base class for environments.

    Provides the structure that concrete environments implement.
    """

    def __init__(self, config: EnvironmentConfig):
        self._config = config

    @property
    def config(self) -> EnvironmentConfig:
        """Get environment configuration."""
        return self._config

    def has_capability(self, capability: EnvironmentCapability) -> bool:
        """Check if environment has a capability."""
        return capability in self._config.capabilities

    @property
    @abstractmethod
    def observations(self) -> ObservationSpaceProtocol:
        """Get observation space."""
        ...

    @property
    @abstractmethod
    def actions(self) -> ActionSpaceProtocol:
        """Get action space."""
        ...

    @property
    @abstractmethod
    def events(self) -> EventStreamProtocol:
        """Get event stream."""
        ...

    @property
    @abstractmethod
    def feedback(self) -> FeedbackChannelProtocol:
        """Get feedback channel."""
        ...


__all__ = [
    # Enums
    "EnvironmentCapability",
    # Config
    "EnvironmentConfig",
    # Protocols
    "ObservationSpaceProtocol",
    "ActionSpaceProtocol",
    "EventStreamProtocol",
    "FeedbackChannelProtocol",
    "EnvironmentProtocol",
    # Base class
    "BaseEnvironment",
]
