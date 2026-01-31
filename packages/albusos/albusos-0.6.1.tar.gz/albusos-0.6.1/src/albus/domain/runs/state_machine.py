"""State Machine primitives - the building blocks of agent behavior.

These are the fundamental types for defining how agents behave over time.
State machines are event-driven and persistent - they don't "exit" like DAGs.

Learning:
- State machines can have learning configs (like pathways)
- Transitions have weights that can be learned
- Learning updates transition weights based on rewards

## Architecture Note

State machines live in albus because they define AGENT behavior.
The PathwayVM (pathway_engine) just executes pathways - it doesn't need to
understand state machines. Albus (the controller) uses state machines to
decide which pathways to run.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pathway_engine.domain.schemas.learning import LearningConfig


class AgentState(BaseModel):
    """A state in an agent's behavior.

    States represent what the agent is currently "doing" or "waiting for".
    Each state can have entry/exit pathways that execute when entering/leaving.

    Example states: idle, thinking, acting, responding, waiting_for_approval
    """

    model_config = {"extra": "allow"}

    id: str = Field(min_length=1, description="Unique state identifier")
    name: str | None = Field(default=None, description="Human-readable name")
    description: str | None = Field(
        default=None, description="What this state represents"
    )

    # Pathways to execute on state entry/exit
    entry_pathway: str | None = Field(
        default=None, description="Pathway ID to execute when entering this state"
    )
    exit_pathway: str | None = Field(
        default=None, description="Pathway ID to execute when leaving this state"
    )

    # State configuration
    timeout_seconds: float | None = Field(
        default=None,
        description="Auto-transition after this many seconds (for time-bounded states)",
    )
    timeout_event: str | None = Field(
        default=None, description="Event to emit on timeout"
    )

    # Auto-emit event when entry pathway completes successfully
    emit_event_on_complete: str | None = Field(
        default=None,
        description="Event to emit when entry pathway finishes successfully",
    )

    # Terminal state - agent lifecycle ends here
    is_terminal: bool = Field(
        default=False, description="If true, agent stops in this state"
    )


class AgentEvent(BaseModel):
    """An event that can trigger state transitions.

    Events are the inputs to the state machine. They can come from:
    - External sources (user messages, webhooks, timers)
    - Internal sources (pathway completion, errors)

    Events carry a payload that can be used by transitions and pathways.
    """

    model_config = {"extra": "allow"}

    id: str = Field(min_length=1, description="Unique event identifier")
    name: str | None = Field(default=None, description="Human-readable name")
    description: str | None = Field(
        default=None, description="What triggers this event"
    )

    # Schema for event payload validation
    payload_schema: dict[str, Any] | None = Field(
        default=None, description="JSON Schema for validating event payloads"
    )

    # Event sources
    internal: bool = Field(
        default=False,
        description="If true, event can only be emitted by the agent itself",
    )


class AgentTransition(BaseModel):
    """A transition from one state to another.

    Transitions define the edges in the state machine graph.
    When an event occurs, the state machine finds matching transitions
    and (if guards pass) moves to the target state.

    Transitions have weights that influence selection when multiple
    transitions match. Weights can be learned from rewards.
    """

    model_config = {"extra": "allow"}

    from_state: str = Field(description="Source state ID")
    event: str = Field(description="Event ID that triggers this transition")
    to_state: str = Field(description="Target state ID")

    # Optional guard condition (expression that must evaluate to true)
    guard: str | None = Field(
        default=None, description="Expression that must be true for transition to fire"
    )

    # Optional pathway to execute during transition (before entering new state)
    action_pathway: str | None = Field(
        default=None, description="Pathway ID to execute during transition"
    )

    # Priority for when multiple transitions match (checked before weight)
    priority: int = Field(
        default=0, description="Higher priority transitions are checked first"
    )

    # Learnable weight for selection (0-1, higher = more likely)
    weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Selection weight (learnable, used when priorities are equal)",
    )


class StateMachine(BaseModel):
    """A complete state machine definition.

    This is the "behavior specification" for an agent. It defines:
    - What states the agent can be in
    - What events the agent responds to
    - How events cause state transitions
    - How the agent learns from experience

    The state machine is declarative - it doesn't execute anything itself.
    Execution is handled by Albus (albus) which uses PathwayVM
    to run the pathways associated with states and transitions.

    Learning:
    - When `learning` is set, transition weights are updated based on rewards
    - Rewards come from pathway execution outcomes
    - Higher-weighted transitions are preferred when multiple match
    """

    model_config = {"extra": "allow"}

    id: str = Field(min_length=1, description="Unique state machine identifier")
    name: str = Field(default="Agent", description="Human-readable name")
    description: str | None = Field(default=None, description="What this agent does")
    version: str = Field(default="1", description="Version for upgrades")

    # State machine structure
    initial_state: str = Field(description="State to start in when spawned")
    states: dict[str, AgentState] = Field(default_factory=dict)
    events: dict[str, AgentEvent] = Field(default_factory=dict)
    transitions: list[AgentTransition] = Field(default_factory=list)

    # Context schema - defines what the agent "remembers"
    context_schema: dict[str, Any] | None = Field(
        default=None, description="JSON Schema for agent's persistent context"
    )

    # Default context values
    initial_context: dict[str, Any] = Field(
        default_factory=dict, description="Initial values for agent context"
    )

    # Learning configuration (same schema as pathways)
    learning: "LearningConfig | None" = Field(
        default=None,
        description="Learning configuration for transition weight optimization",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_transitions_for_state(self, state_id: str) -> list[AgentTransition]:
        """Get all transitions that originate from a state."""
        return [t for t in self.transitions if t.from_state == state_id]

    def get_transition(
        self,
        from_state: str,
        event: str,
        *,
        use_weights: bool = True,
        exploration_rate: float = 0.0,
    ) -> AgentTransition | None:
        """Find a transition matching state and event.

        NOTE: This method does NOT evaluate guards. For guard-aware selection,
        use the Albus controller which filters by guards first, then calls
        select_from_candidates().

        Selection order:
        1. Filter by (from_state, event) match
        2. Use weight-based selection via select_from_candidates()

        Args:
            from_state: Current state ID
            event: Event ID
            use_weights: Whether to use learned weights for selection
            exploration_rate: Probability of random selection (epsilon-greedy)

        Returns:
            Selected transition or None
        """
        matching = [
            t
            for t in self.transitions
            if t.from_state == from_state and t.event == event
        ]
        if not matching:
            return None

        if not use_weights:
            # Simple priority-based selection without weights
            matching.sort(key=lambda t: t.priority, reverse=True)
            return matching[0]

        return self.select_from_candidates(matching, exploration_rate=exploration_rate)

    def get_transition_key(self, transition: AgentTransition) -> str:
        """Get a unique key for a transition (for weight storage)."""
        return f"{transition.from_state}:{transition.event}:{transition.to_state}"

    def select_from_candidates(
        self,
        candidates: list[AgentTransition],
        *,
        exploration_rate: float = 0.0,
    ) -> AgentTransition | None:
        """Select a transition from pre-filtered candidates using weights.

        This is the ALGORITHM for weight-based selection. Guards should be
        evaluated by the caller (Albus controller) before calling this.

        Selection order:
        1. Sort by priority descending
        2. Get top priority group
        3. If exploration_rate > 0, random selection with that probability
        4. Otherwise, probabilistic weight-based selection

        Args:
            candidates: Pre-filtered transitions (guards already evaluated)
            exploration_rate: Probability of random selection (epsilon-greedy)

        Returns:
            Selected transition or None if candidates is empty
        """
        import random

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Sort by priority descending
        sorted_candidates = sorted(candidates, key=lambda t: t.priority, reverse=True)

        # Get highest priority group
        top_priority = sorted_candidates[0].priority
        top_group = [t for t in sorted_candidates if t.priority == top_priority]

        if len(top_group) == 1:
            return top_group[0]

        # Epsilon-greedy exploration
        if exploration_rate > 0 and random.random() < exploration_rate:
            return random.choice(top_group)

        # Weight-based probabilistic selection
        total_weight = sum(t.weight for t in top_group)
        if total_weight > 0:
            r = random.random() * total_weight
            cumulative = 0.0
            for t in top_group:
                cumulative += t.weight
                if r <= cumulative:
                    return t

        # Fallback: first one (shouldn't reach here normally)
        return top_group[0]


__all__ = [
    "AgentEvent",
    "AgentState",
    "AgentTransition",
    "StateMachine",
]
