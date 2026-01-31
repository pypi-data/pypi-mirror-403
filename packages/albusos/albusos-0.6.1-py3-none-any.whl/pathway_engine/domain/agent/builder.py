"""Agent builder - Fluent API for constructing agents."""

from __future__ import annotations

from .cognitive import (
    CognitiveStyle,
    CognitivePresets,
    ReasoningMode,
    OrationMode,
    SupervisionMode,
)
from .memory import AgentMemoryConfig
from .capabilities import AgentCapabilities, ProactiveTrigger
from .skill import Skill
from .core import Agent


class AgentBuilder:
    """Fluent builder for Agent construction.

    Example:
        agent = (
            agent_builder()
            .id("assistant")
            .name("Assistant")
            .persona("You are a helpful assistant...")
            .tool("workspace.*")
            .tool("web.search")
            .as_reasoning_agent()
            .build()
        )
    """

    def __init__(self):
        self._id: str = "agent"
        self._name: str = "Agent"
        self._persona: str = ""
        self._goals: list[str] = []
        self._cognitive_style: CognitiveStyle = CognitiveStyle()
        self._skills: list[Skill] = []
        self._tools: list[str] = []
        self._max_steps: int = 10
        self._model: str = "auto"
        self._temperature: float = 0.7
        self._memory_namespace: str = "default"
        self._proactive_triggers: list[ProactiveTrigger] = []
        self._can_spawn: bool = False

    # Identity
    def id(self, agent_id: str) -> "AgentBuilder":
        self._id = agent_id
        self._memory_namespace = agent_id
        return self

    def name(self, name: str) -> "AgentBuilder":
        self._name = name
        return self

    def persona(self, persona: str) -> "AgentBuilder":
        self._persona = persona
        return self

    def goal(self, goal: str) -> "AgentBuilder":
        self._goals.append(goal)
        return self

    # Cognitive style
    def style(self, style: CognitiveStyle) -> "AgentBuilder":
        """Set the cognitive style (use CognitivePresets for common patterns)."""
        self._cognitive_style = style
        return self

    def reasoning(self, mode: ReasoningMode) -> "AgentBuilder":
        """Set reasoning mode (reactive/deliberative/reflective)."""
        self._cognitive_style.reasoning = mode
        return self

    def oration(self, mode: OrationMode) -> "AgentBuilder":
        """Set oration mode (concise/conversational/elaborate/socratic/formal)."""
        self._cognitive_style.oration = mode
        return self

    def supervision(self, mode: SupervisionMode) -> "AgentBuilder":
        """Set supervision mode (autonomous/collaborative/delegating/orchestrating)."""
        self._cognitive_style.supervision = mode
        return self

    # Presets
    def as_reasoning_agent(self) -> "AgentBuilder":
        """Use the reasoning agent preset (deliberate, thorough, self-critical)."""
        self._cognitive_style = CognitivePresets.reasoning_agent()
        return self

    def as_orator(self) -> "AgentBuilder":
        """Use the orator preset (eloquent, engaging, polished)."""
        self._cognitive_style = CognitivePresets.orator()
        return self

    def as_supervisor(self) -> "AgentBuilder":
        """Use the supervisor preset (plans, delegates, synthesizes)."""
        self._cognitive_style = CognitivePresets.supervisor()
        return self

    def as_assistant(self) -> "AgentBuilder":
        """Use the assistant preset (quick, friendly, collaborative)."""
        self._cognitive_style = CognitivePresets.assistant()
        return self

    # Skills and capabilities
    def skill(self, skill: Skill) -> "AgentBuilder":
        """Add a skill to this agent."""
        self._skills.append(skill)
        return self

    def tool(self, tool_pattern: str) -> "AgentBuilder":
        """Add a tool pattern (e.g., 'search.*', 'web.fetch')."""
        self._tools.append(tool_pattern)
        return self

    def max_steps(self, steps: int) -> "AgentBuilder":
        """Max steps per turn."""
        self._max_steps = steps
        return self

    def model(self, model: str) -> "AgentBuilder":
        """LLM model to use."""
        self._model = model
        return self

    def temperature(self, temp: float) -> "AgentBuilder":
        """LLM temperature."""
        self._temperature = temp
        return self

    def can_spawn(self, enabled: bool = True) -> "AgentBuilder":
        """Enable spawning other agents (Host-only capability)."""
        self._can_spawn = enabled
        return self

    # Memory
    def memory_namespace(self, namespace: str) -> "AgentBuilder":
        self._memory_namespace = namespace
        return self

    # Proactive triggers
    def proactive(
        self,
        trigger_id: str,
        description: str,
        condition: str,
        action: str,
        schedule: str = "on_event",
    ) -> "AgentBuilder":
        self._proactive_triggers.append(
            ProactiveTrigger(
                id=trigger_id,
                description=description,
                condition=condition,
                action=action,
                schedule=schedule,
            )
        )
        return self

    def build(self) -> Agent:
        agent = Agent(
            id=self._id,
            name=self._name,
            persona=self._persona,
            goals=self._goals,
            cognitive_style=self._cognitive_style,
            capabilities=AgentCapabilities(
                tools=self._tools,
                max_steps_per_turn=self._max_steps,
                model=self._model,
                temperature=self._temperature,
                can_spawn=self._can_spawn,
            ),
            memory=AgentMemoryConfig(namespace=self._memory_namespace),
            proactive_triggers=self._proactive_triggers,
        )

        # Add skills
        for skill in self._skills:
            agent.add_skill(skill)

        return agent


def agent_builder() -> AgentBuilder:
    """Create a fluent agent builder."""
    return AgentBuilder()


__all__ = ["AgentBuilder", "agent_builder"]
