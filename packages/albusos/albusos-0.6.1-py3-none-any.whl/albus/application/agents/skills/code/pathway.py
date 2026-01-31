"""Code pathway - Programming tasks."""

from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import TransformNode
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode


def build_code_pathway() -> Pathway:
    """Build the code pathway."""
    return Pathway(
        id="skill.code",
        name="Code",
        description="Programming tasks with code tools",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nComplete the coding task. Say DONE when finished.",
                system="You are a coding assistant. Help with programming tasks. Be concise and focus on the code.",
                tools=["code.*", "workspace.*"],
                model="auto",  # Routes to code-capable model
                reasoning_mode="react",
                max_steps=8,
            ),
            "result": TransformNode(
                id="result",
                expr='{"response": agent.get("response", ""), "skill": "code"}',
            ),
        },
        connections=[Connection(from_node="agent", to_node="result")],
    )
