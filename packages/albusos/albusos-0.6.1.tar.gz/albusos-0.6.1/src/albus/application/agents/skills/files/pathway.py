"""Files pathway - Workspace operations."""

from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import TransformNode
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode


def build_files_pathway() -> Pathway:
    """Build the files pathway."""
    return Pathway(
        id="skill.files",
        name="Files",
        description="Workspace file operations",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nComplete the file task. Say DONE when finished.",
                system="You are a file assistant. Help with workspace operations. Use workspace tools to read, write, and manage files. Be careful with file operations.",
                tools=["workspace.*"],
                model="auto",
                reasoning_mode="react",
                max_steps=6,
            ),
            "result": TransformNode(
                id="result",
                expr='{"response": agent.get("response", ""), "skill": "files"}',
            ),
        },
        connections=[Connection(from_node="agent", to_node="result")],
    )
