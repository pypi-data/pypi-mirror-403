"""Host pathways - Fast single-agent execution.

One pathway: host.work
- Direct tool access (workspace, code, web, pathway tools)
- ReAct reasoning for speed
- No planning overhead

The Host Agent uses these pathways for state machine transitions.
For direct agent interaction, use AgentService.turn() instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode
from pathway_engine.domain.nodes.core import TransformNode

if TYPE_CHECKING:
    from albus.application.pathways import PathwayService


# Host persona used in pathways (matches AgentService.HOST_PERSONA)
HOST_SYSTEM_PROMPT = """You are Host, the primary AI assistant in AlbusOS. You are intelligent, fast, and adaptable.

You have access to ALL tools: workspace.*, code.*, web.*, search.*, memory.*, llm.*, vector.*, kg.*, vision.*, speech.*, skill.*, pathway.*, agent.*, mcp.*

STRATEGY:
- SIMPLE → Execute directly with tools (fast)
- COMPLEX → Create pathways or spawn agents (orchestrate)
- NOVEL → Load skills, create pathways, spawn agents (adapt)

Be proactive, fast, and adaptive. Use the right tool for each task."""


def build_host_work_pathway() -> Pathway:
    """Build the main work pathway - fast single agent with all tools.
    
    This pathway is used by the state machine for Host execution.
    It provides direct tool access with ReAct reasoning.
    """
    return Pathway(
        id="host.work",
        name="Host Work",
        description="Fast single-agent execution with direct tool access",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="""{{task}}

Use tools to complete the task. Say DONE when finished.""",
                system=HOST_SYSTEM_PROMPT,
                tools=[
                    # Skills, pathways, agents
                    "skill.*",
                    "pathway.*",
                    "agent.*",
                    # Core capabilities
                    "workspace.*",
                    "code.*",
                    "web.*",
                    "search.*",
                    "memory.*",
                    "llm.*",
                    "vector.*",
                    "kg.*",
                    "vision.*",
                    "speech.*",
                    "mcp.*",
                    # Introspection
                    "env.list_tools",
                ],
                reasoning_mode="react",  # Fast, direct execution
                max_steps=10,  # Balanced: complex tasks + fast responses
                model="auto",  # Uses capability routing
            ),
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": agent.get("response", ""),
                    "completed": agent.get("completed", False),
                    "steps_taken": agent.get("steps_taken", 0)
                }""",
            ),
        },
        connections=[
            Connection(from_node="agent", to_node="result"),
        ],
    )


# =============================================================================
# REGISTRATION
# =============================================================================

HOST_PATHWAY_BUILDERS = {
    "host.work": build_host_work_pathway,
}


def register_host_pathways(pathway_service: "PathwayService") -> None:
    """Register all Host pathways with the pathway service."""
    for pathway_id, builder in HOST_PATHWAY_BUILDERS.items():
        pathway_service.deploy(
            builder,
            pathway_id=pathway_id,
            source="builtin:host",
            version="1",
        )


__all__ = [
    "HOST_PATHWAY_BUILDERS",
    "HOST_SYSTEM_PROMPT",
    "register_host_pathways",
]
