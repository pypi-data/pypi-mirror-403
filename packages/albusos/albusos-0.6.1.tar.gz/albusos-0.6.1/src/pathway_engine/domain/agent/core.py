"""Agent - Core agent class with execution logic."""

from __future__ import annotations

import json
import logging
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from .cognitive import CognitiveStyle
from .memory import AgentMemoryConfig, MemoryScope
from .capabilities import AgentCapabilities, ProactiveTrigger
from .state import AgentState
from .skill import Skill, SkillBundle

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


class Agent(BaseModel):
    """A persistent AI agent with identity, memory, and capabilities.

    Agents are the "characters" that use Packs as their skill libraries.
    They maintain state across interactions and can act proactively.

    Usage:
        agent = Agent(
            id="support_agent",
            name="Support Agent",
            persona="Helpful customer support specialist",
            goals=["Resolve issues quickly", "Keep customers happy"],
            capabilities=AgentCapabilities(packs=["support_pack"]),
        )

        result = await agent.turn(
            message="My order hasn't arrived",
            thread_id="conv_123",
            ctx=context,
        )
    """

    # Identity
    id: str
    name: str
    persona: str = ""
    goals: list[str] = Field(default_factory=list)

    # Cognitive style - HOW the agent thinks and communicates
    cognitive_style: CognitiveStyle = Field(default_factory=CognitiveStyle)

    # Capabilities
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)

    # Memory configuration
    memory: AgentMemoryConfig = Field(default_factory=AgentMemoryConfig)

    # Proactive triggers
    proactive_triggers: list[ProactiveTrigger] = Field(default_factory=list)

    # Runtime state (use PrivateAttr to avoid sharing between instances)
    _skills: dict[str, Skill] = PrivateAttr(default_factory=dict)
    _state: AgentState | None = PrivateAttr(default=None)

    model_config = {"arbitrary_types_allowed": True}

    # -------------------------------------------------------------------------
    # CORE EXECUTION
    # -------------------------------------------------------------------------

    async def turn(
        self,
        message: str,
        thread_id: str,
        ctx: "Context",
        *,
        attachments: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run one agent turn - the main interaction loop."""
        from pathway_engine.domain.nodes.agent_loop import AgentLoopNode

        # Inject skills into context so skill.invoke can find them
        if not hasattr(ctx, "extras") or ctx.extras is None:
            ctx.extras = {}
        ctx.extras["skills"] = self._skills
        ctx.extras["agent_id"] = self.id

        state = await self._load_state(thread_id, ctx)
        system = self._build_system_prompt(state, context)
        tools = self._gather_tools(ctx)

        goal = f"""Help the user with their request. Respond naturally and directly to them.

User said: "{message}"

{f"Additional context: {json.dumps(context)}" if context else ""}

Your goals:
{chr(10).join(f"- {g}" for g in self.goals)}

Use tools as needed to help the user. When done, provide a clear, direct response to the user and say DONE."""

        # Get model for tool calling (respects agent overrides + global routing)
        model = self.capabilities.get_model_for_capability("tool_calling")

        agent_loop = AgentLoopNode(
            id="agent_turn",
            goal=goal,
            tools=tools,
            max_steps=self.capabilities.max_steps_per_turn,
            model=model,
            system=system,
            temperature=self.capabilities.temperature,
        )

        state.messages.append({"role": "user", "content": message})

        result = await agent_loop.compute(
            {
                "message": message,
                "history": state.messages[-20:],
                "attachments": attachments or [],
                "context": context or {},
            },
            ctx,
        )

        response_text = result.get("response", "")
        state.messages.append({"role": "assistant", "content": response_text})

        await self._maybe_learn(result, state, ctx)
        await self._save_state(thread_id, state, ctx)

        return {
            "response": response_text,
            "agent_id": self.id,
            "thread_id": thread_id,
            "completed": result.get("completed", False),
            "steps_taken": result.get("steps_taken", 0),
            "step_results": result.get("step_results", []),
        }

    # -------------------------------------------------------------------------
    # SKILLS
    # -------------------------------------------------------------------------

    def add_skill(self, skill: Skill) -> None:
        """Add a skill to this agent."""
        self._skills[skill.id] = skill
        logger.debug(f"Agent {self.id}: added skill {skill.id}")

    def add_bundle(self, bundle: SkillBundle) -> None:
        """Add all skills from a bundle to this agent."""
        for s in bundle.skills:
            self.add_skill(s)

    def get_skill(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def list_skills(self) -> list[str]:
        """List all available skill IDs."""
        return list(self._skills.keys())

    async def invoke_skill(
        self,
        skill_id: str,
        inputs: dict[str, Any],
        ctx: "Context",
    ) -> dict[str, Any]:
        """Invoke a skill by ID."""
        skill = self._skills.get(skill_id)
        if not skill:
            return {"error": f"Skill not found: {skill_id}"}

        return await skill.invoke(inputs, ctx)

    # -------------------------------------------------------------------------
    # MEMORY
    # -------------------------------------------------------------------------

    async def remember(
        self,
        key: str,
        value: Any,
        ctx: "Context",
        *,
        scope: MemoryScope = MemoryScope.AGENT,
        thread_id: str | None = None,
    ) -> None:
        """Store something in memory."""
        memory_set = ctx.tools.get("memory.set")
        if not memory_set:
            return

        if scope == MemoryScope.THREAD:
            if not thread_id:
                raise ValueError("thread_id required for THREAD scope")
            namespace = self.memory.short_term_ns(thread_id)
        else:
            namespace = self.memory.long_term_ns()

        await memory_set({"key": key, "value": value, "namespace": namespace}, ctx)

    async def recall(
        self,
        query: str,
        ctx: "Context",
        *,
        scope: MemoryScope = MemoryScope.AGENT,
        thread_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search memory."""
        memory_search = ctx.tools.get("memory.search")
        if not memory_search:
            return []

        if scope == MemoryScope.THREAD:
            if not thread_id:
                raise ValueError("thread_id required for THREAD scope")
            namespace = self.memory.short_term_ns(thread_id)
        else:
            namespace = self.memory.long_term_ns()

        result = await memory_search(
            {"query": query, "namespace": namespace, "limit": limit}, ctx
        )
        return result.get("results", [])

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent definition."""
        return {
            "id": self.id,
            "name": self.name,
            "persona": self.persona,
            "goals": self.goals,
            "cognitive_style": self.cognitive_style.to_dict(),
            "skills": [s.to_dict() for s in self._skills.values()],
            "capabilities": {
                "tools": self.capabilities.tools,
                "max_steps_per_turn": self.capabilities.max_steps_per_turn,
                "model": self.capabilities.model,
            },
        }

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    def _build_system_prompt(
        self,
        state: AgentState,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Build system prompt with persona, goals, cognitive style, and memory."""
        parts = []

        if self.persona:
            parts.append(f"## Who You Are\n{self.persona}")

        if self.goals:
            goals_text = "\n".join(f"- {g}" for g in self.goals)
            parts.append(f"## Your Goals\n{goals_text}")

        style_instructions = self.cognitive_style.to_system_prompt_section()
        if style_instructions:
            parts.append(f"## How You Work\n{style_instructions}")

        if state.learned:
            recent = state.learned[-5:]
            learnings = "\n".join(f"- {l.get('fact', l)}" for l in recent)
            parts.append(f"## What You've Learned\n{learnings}")

        if state.working_memory:
            parts.append(
                f"## Current Context\n{json.dumps(state.working_memory, indent=2)}"
            )

        if self._skills:
            skills_text = "\n".join(
                f"- {s.id}: {s.description or s.name}" for s in self._skills.values()
            )
            parts.append(
                "## Your Skills\n"
                f"{skills_text}\n\n"
                "To use a skill, call `skill.invoke` with:\n"
                '- `skill_id`: the skill ID from above\n'
                '- `inputs`: {"message": "the task description"}'
            )

        parts.append(
            """## Instructions
- For SIMPLE questions (greetings, math, general knowledge): Answer directly WITHOUT using any tools
- For COMPLEX tasks: Use the appropriate skill via skill.invoke
- When done, include "DONE" in your response with your answer"""
        )

        return "\n\n".join(parts)

    def _gather_tools(self, ctx: "Context") -> list[str]:
        """Gather all available tool patterns for this agent.
        
        Only returns tools the agent explicitly declared.
        Does NOT auto-add llm.*/memory.* - that caused agents to bypass skills.
        """
        tools = list(self.capabilities.tools)

        # Add skill tools (via stdlib `skill.invoke` / `skill.list`)
        if self._skills:
            # Only add if not already present
            if "skill.invoke" not in tools and "skill.*" not in tools:
                tools.append("skill.invoke")
            if "skill.list" not in tools and "skill.*" not in tools:
                tools.append("skill.list")

        return tools

    async def _load_state(self, thread_id: str, ctx: "Context") -> AgentState:
        """Load agent state for a thread."""
        memory_get = ctx.tools.get("memory.get")
        if memory_get:
            result = await memory_get(
                {
                    "key": f"agent_state:{self.id}:{thread_id}",
                    "namespace": self.memory.long_term_ns(),
                },
                ctx,
            )
            if result.get("found") and result.get("value"):
                return AgentState.from_dict(result["value"])
        return AgentState(thread_id=thread_id)

    async def _save_state(
        self, thread_id: str, state: AgentState, ctx: "Context"
    ) -> None:
        """Save agent state for a thread."""
        from datetime import datetime, timezone

        state.last_active = datetime.now(timezone.utc).isoformat()

        memory_set = ctx.tools.get("memory.set")
        if memory_set:
            await memory_set(
                {
                    "key": f"agent_state:{self.id}:{thread_id}",
                    "value": state.to_dict(),
                    "namespace": self.memory.long_term_ns(),
                },
                ctx,
            )

    async def _maybe_learn(
        self, result: dict[str, Any], state: AgentState, ctx: "Context"
    ) -> None:
        """Extract learnings from a turn result for long-term memory."""
        if result.get("completed") and result.get("steps_taken", 0) >= 2:
            step_results = result.get("step_results", [])
            tools_used = []
            for step in step_results:
                # Some providers return `tool_calls: null` in step results.
                for tc in (step.get("tool_calls") or []):
                    if isinstance(tc, dict):
                        tools_used.append(tc.get("function", {}).get("name", ""))

            if tools_used:
                state.learned.append(
                    {
                        "fact": f"Successfully used tools: {', '.join(tools_used[:3])}",
                        "context": result.get("goal", "")[:100],
                    }
                )


__all__ = ["Agent"]
