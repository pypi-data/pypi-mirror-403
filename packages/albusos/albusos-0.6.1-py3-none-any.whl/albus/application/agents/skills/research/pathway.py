"""Research pathway - Information gathering."""

from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import TransformNode
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode


def build_research_pathway() -> Pathway:
    """Build the research pathway."""
    return Pathway(
        id="skill.research",
        name="Research",
        description="Information gathering with web tools",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message or query}}\n\nResearch this topic thoroughly. Say DONE when finished.",
                system="You are a research assistant. Find and synthesize information. Use web tools to search and gather information. Summarize findings clearly.",
                tools=["web.*", "search.*", "llm.generate"],
                model="auto",
                reasoning_mode="react",
                max_steps=6,
            ),
            "result": TransformNode(
                id="result",
                expr='{"response": agent.get("response", ""), "completed": agent.get("completed", False), "steps_taken": agent.get("steps_taken", 0), "skill": "research"}',
            ),
        },
        connections=[Connection(from_node="agent", to_node="result")],
    )
