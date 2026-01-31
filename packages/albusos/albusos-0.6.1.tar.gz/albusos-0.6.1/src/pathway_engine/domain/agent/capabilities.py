"""Agent capabilities and proactive triggers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentCapabilities:
    """What the agent can do.

    Capabilities come from:
    - Skills: Discrete actions (wired via agent.add_skill())
    - Tools: Direct tool access patterns (e.g., memory.*, search.*)

    Model selection:
    - model="auto": Use capability routing (recommended)
    - model="<specific>": Use a specific model for all operations
    - model_overrides: Per-capability model overrides (highest priority)

    Spawning:
    - can_spawn: Whether this agent can create/invoke other agents
      (Only Host has this by default - enables agent.spawn, agent.turn tools)

    Example:
        capabilities = AgentCapabilities(
            model="auto",  # Use routing
            can_spawn=True,  # Can create other agents (Host only)
            model_overrides={
                "code": "qwen2.5-coder:7b",  # Override for code tasks
            }
        )
    """

    tools: list[str] = field(default_factory=list)
    max_steps_per_turn: int = 10
    model: str = "auto"  # "auto" = use capability routing, or specific model name
    temperature: float = 0.7
    model_overrides: dict[str, str] = field(default_factory=dict)  # capability → model
    can_spawn: bool = False  # Can create/invoke other agents (Host has True)

    def get_model_for_capability(self, capability: str = "tool_calling") -> str:
        """Get the model to use for a specific capability.

        Resolution order:
        1. model_overrides (per-agent)
        2. If model != "auto", use that model
        3. Otherwise, use global capability routing

        Args:
            capability: The capability needed (e.g., "tool_calling", "code", "reasoning")

        Returns:
            Model name to use
        """
        # Check agent-level overrides first
        if capability in self.model_overrides:
            return self.model_overrides[capability]

        # Check parent capability
        if "." in capability:
            parent = capability.rsplit(".", 1)[0]
            if parent in self.model_overrides:
                return self.model_overrides[parent]

        # If model is not "auto", use it directly
        if self.model != "auto":
            return self.model

        # Use global routing hook (registered by higher layers), with safe fallback.
        from pathway_engine.domain.model_routing import get_default_model

        return get_default_model(capability)


@dataclass
class ProactiveTrigger:
    """Condition that causes the agent to initiate action.

    Unlike Pack triggers (reactive), these are agent-initiated checks
    that the agent evaluates to decide whether to act.
    """

    id: str
    description: str
    condition: str  # Natural language, evaluated by LLM
    action: str  # What to do if condition is true
    schedule: str = "on_event"  # Cron expression or "on_event"
    enabled: bool = True


__all__ = [
    "AgentCapabilities",
    "ProactiveTrigger",
]
