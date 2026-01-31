"""Competitor Analyst Agent.

One agent, one pack. The canonical example.
"""

from agents.registry import agent
from pathway_engine import agent_builder


@agent
def COMPETITOR_ANALYST():
    """Competitive intelligence agent.

    Uses the competitor_intel pack, which provides:
    - competitor_intel.quick_snapshot.v1
    - competitor_intel.deep_research.v1
    - competitor_intel.comparison.v1

    Usage:
        POST /api/v1/agents/competitor_analyst/turn
        {"message": "Research Notion", "thread_id": "session_1"}
    """
    return (
        agent_builder()
        .id("competitor_analyst")
        .name("Competitor Analyst")
        .persona("""You are a competitive intelligence analyst.
You help teams understand the competitive landscape with accurate, actionable insights.
Cite sources when possible. Ask clarifying questions if needed.""")
        .goal("Provide accurate competitive intelligence")
        .goal("Help users understand competitor strengths and weaknesses")
        .use_pack("competitor_intel")
        .tool("web.*")
        .tool("memory.*")
        .as_reasoning_agent()
        .max_steps(15)
        .build()
    )
