"""Agent builder - Fluent API for constructing agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from pathway_engine.domain.pack import Pack


class AgentBuilder:
    """Fluent builder for Agent construction.

    Example - Using packs as skill sets:
        agent = (
            agent_builder()
            .id("analyst")
            .name("Analyst")
            .persona("You are a thorough analyst...")
            .use_pack("competitor_intel")  # Pack pathways become skills
            .as_reasoning_agent()
            .build()
        )

    Example - Custom skills:
        agent = (
            agent_builder()
            .id("assistant")
            .skill(my_custom_skill)
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
        self._pack_ids: list[str] = []
        self._tools: list[str] = []
        self._max_steps: int = 10
        self._model: str = "auto"
        self._temperature: float = 0.7
        self._memory_namespace: str = "default"
        self._proactive_triggers: list[ProactiveTrigger] = []

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
    def use_pack(self, pack_id: str) -> "AgentBuilder":
        """Use a pack's pathways as this agent's skill set.

        This is the primary way to give agents capabilities.
        All pathways in the pack become callable skills.

        Example:
            agent_builder()
                .use_pack("competitor_intel")  # Gets all competitor_intel pathways
                .use_pack("research")          # Also gets research pathways
                .build()

        Args:
            pack_id: ID of a registered pack (from @deployable)
        """
        self._pack_ids.append(pack_id)
        return self

    def use_packs(self, *pack_ids: str) -> "AgentBuilder":
        """Use multiple packs as skill sets.

        Example:
            agent_builder().use_packs("competitor_intel", "research", "analysis")
        """
        self._pack_ids.extend(pack_ids)
        return self

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
            ),
            memory=AgentMemoryConfig(namespace=self._memory_namespace),
            proactive_triggers=self._proactive_triggers,
        )

        # Resolve packs into skills
        for pack_id in self._pack_ids:
            for skill in self._resolve_pack_to_skills(pack_id):
                agent.add_skill(skill)

        # Add custom skills
        for skill in self._skills:
            agent.add_skill(skill)

        return agent

    def _resolve_pack_to_skills(self, pack_id: str) -> list[Skill]:
        """Convert a pack's pathways into skills.

        This is the key bridge: Packs define pathways, Agents consume them as skills.
        """
        try:
            from packs.registry import get_pack_by_id
        except ImportError:
            # Packs registry not available (e.g., in tests)
            return []

        pack = get_pack_by_id(pack_id)
        if not pack:
            import logging
            logging.getLogger(__name__).warning(f"Pack not found: {pack_id}")
            return []

        skills = []
        for pathway_id, builder_fn in pack.get_pathways().items():
            name = pathway_id.replace(".", " ").replace("_", " ").title()
            description = f"Skill from {pack_id}"

            # Try to get better metadata from the pathway itself
            try:
                pathway = builder_fn()
                if pathway.name:
                    name = pathway.name
                if pathway.description:
                    description = pathway.description
            except Exception:
                pass

            skills.append(Skill(
                id=pathway_id,
                name=name,
                description=description,
                pathway_builder=builder_fn,
            ))

        return skills


def agent_builder() -> AgentBuilder:
    """Create a fluent agent builder."""
    return AgentBuilder()


__all__ = ["AgentBuilder", "agent_builder"]
