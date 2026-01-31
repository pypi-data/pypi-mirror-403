"""Competitor Intel Pack - Skills for competitive analysis.

Agents consume this pack:
    agent_builder().use_pack("competitor_intel")

Skills (pathways):
    - quick_snapshot.v1   Fast competitor overview (30 sec)
    - deep_research.v1    Thorough research (2-5 min)
    - comparison.v1       Multi-competitor comparison

Tools used:
    web.search, web.fetch, web.news, llm.generate, code.execute
"""

from packs.registry import deployable
from pathway_engine import (
    pack_builder,
    Pathway,
    Connection,
    LLMNode,
    ToolNode,
    CodeNode,
)
from pathway_engine.domain.nodes import AgentLoopNode


# =============================================================================
# PATHWAY 1: Quick competitor snapshot
# =============================================================================
# Simple pipeline: search → synthesize
# This shows basic node chaining

def build_quick_snapshot_pathway() -> Pathway:
    """Quick competitor snapshot - search and summarize."""
    return Pathway(
        id="competitor_intel.quick_snapshot.v1",
        name="Quick Competitor Snapshot",
        description="Fast overview of a competitor from web search",
        nodes={
            # Step 1: Search for competitor info
            # ToolNode calls ctx.tools["web.search"] from stdlib
            "search": ToolNode(
                id="search",
                tool="web.search",  # → stdlib/tools/web.py
                args={
                    "query": "{{competitor}} company overview products funding",
                    "max_results": 5,
                },
            ),
            # Step 2: Search news
            "news": ToolNode(
                id="news",
                tool="web.news",  # → stdlib/tools/web.py
                args={
                    "query": "{{competitor}} news announcements",
                    "max_results": 3,
                },
            ),
            # Step 3: Synthesize with LLM
            # LLMNode calls ctx.tools["llm.generate"] from stdlib
            "synthesize": LLMNode(
                id="synthesize",
                prompt="""Create a competitor snapshot for {{competitor}}.

## Search Results
{{search.output.results}}

## Recent News
{{news.output.results}}

Provide a structured summary:
1. **Company Overview** (what they do, target market)
2. **Key Products/Services**
3. **Recent News & Announcements**
4. **Competitive Position**

Keep it concise but actionable.""",
                model="auto",  # Routes to configured LLM
                temperature=0.3,
            ),
        },
        connections=[
            # Input flows to both search nodes (parallel)
            Connection(from_node="input", to_node="search"),
            Connection(from_node="input", to_node="news"),
            # Both feed into synthesize
            Connection(from_node="search", to_node="synthesize"),
            Connection(from_node="news", to_node="synthesize"),
            # Output
            Connection(from_node="synthesize", to_node="output"),
        ],
    )


# =============================================================================
# PATHWAY 2: Deep research with agent loop
# =============================================================================
# Uses AgentLoopNode for autonomous research
# The agent decides which tools to call

def build_deep_research_pathway() -> Pathway:
    """Deep competitor research using agentic loop."""
    return Pathway(
        id="competitor_intel.deep_research.v1",
        name="Deep Competitor Research",
        description="Thorough research using autonomous agent",
        nodes={
            # AgentLoopNode: autonomous research agent
            # It gets access to specified tools and decides how to use them
            "research_agent": AgentLoopNode(
                id="research_agent",
                goal="""Research {{competitor}} thoroughly. Gather:
1. Company background (founded, HQ, funding, employees)
2. Products and services with pricing if available
3. Target customers and market positioning
4. Recent news, partnerships, product launches
5. Leadership team and key hires
6. Technology stack if mentioned
7. Customer reviews or testimonials

Be thorough. Search multiple times with different queries.
Fetch important pages for details. Say DONE when complete.""",
                # Tools the agent can use (patterns from stdlib)
                tools=[
                    "web.search",   # Search the web
                    "web.fetch",    # Fetch page content
                    "web.news",     # Search news
                ],
                reasoning_mode="react",  # Reason-Act-Observe loop
                max_steps=12,
                model="auto",
            ),
            # Format the output
            "format": LLMNode(
                id="format",
                prompt="""Format this research into a professional competitor intelligence report:

{{research_agent.response}}

Structure as:
# Competitor Intelligence: {{competitor}}

## Executive Summary
(2-3 sentences)

## Company Profile
- Founded:
- Headquarters:
- Employees:
- Funding:

## Products & Services
(bullet points)

## Market Position
(who they target, how they position)

## Recent Developments
(news, launches, partnerships)

## Key Takeaways
(3-5 actionable insights)
""",
                model="auto",
                temperature=0.2,
            ),
        },
        connections=[
            Connection(from_node="input", to_node="research_agent"),
            Connection(from_node="research_agent", to_node="format"),
            Connection(from_node="format", to_node="output"),
        ],
    )


# =============================================================================
# PATHWAY 3: Competitive analysis with code execution
# =============================================================================
# Uses CodeNode to process data

def build_comparison_pathway() -> Pathway:
    """Compare multiple competitors using structured analysis."""
    return Pathway(
        id="competitor_intel.comparison.v1",
        name="Competitor Comparison",
        description="Compare competitors on key dimensions",
        nodes={
            # Research each competitor
            "research": AgentLoopNode(
                id="research",
                goal="""Research these competitors: {{competitors}}

For EACH competitor, find:
- Pricing (if available)
- Key features
- Target market
- Company size

Output as structured JSON like:
{
  "competitor_name": {
    "pricing": "...",
    "features": ["...", "..."],
    "target_market": "...",
    "size": "..."
  }
}

Say DONE when you have data on all competitors.""",
                tools=["web.search", "web.fetch"],
                reasoning_mode="plan_execute",  # Plan first for multi-competitor
                max_steps=15,
            ),
            # Process with Python code
            # CodeNode calls ctx.tools["code.execute"] → runs in Docker sandbox
            "analyze": CodeNode(
                id="analyze",
                code='''
import json

def main(input):
    """Analyze competitor data and create comparison matrix."""
    research_text = input.get("research_response", "")
    
    # Try to extract JSON from research
    # In production, you'd use more robust parsing
    try:
        # Find JSON in the response
        start = research_text.find("{")
        end = research_text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(research_text[start:end])
        else:
            data = {}
    except:
        data = {}
    
    # Build comparison matrix
    dimensions = ["pricing", "features", "target_market", "size"]
    matrix = {"dimensions": dimensions, "competitors": {}}
    
    for name, info in data.items():
        matrix["competitors"][name] = {
            dim: info.get(dim, "Unknown") for dim in dimensions
        }
    
    return {
        "matrix": matrix,
        "competitor_count": len(data),
        "raw_data": data
    }
''',
                profile="datascience",  # Uses pandas/numpy image if configured
                timeout_ms=10000,
            ),
            # Final report
            "report": LLMNode(
                id="report",
                prompt="""Create a competitive comparison report.

## Analysis Data
{{analyze.output}}

Create a clear comparison with:
1. **Comparison Table** (markdown table)
2. **Strengths & Weaknesses** per competitor
3. **Recommendations** for our positioning

Make it actionable for product and sales teams.""",
                model="auto",
            ),
        },
        connections=[
            Connection(from_node="input", to_node="research"),
            Connection(
                from_node="research",
                to_node="analyze",
                from_output="response",
                to_input="research_response",
            ),
            Connection(from_node="analyze", to_node="report"),
            Connection(from_node="report", to_node="output"),
        ],
    )


# =============================================================================
# PACK DEFINITION
# =============================================================================
# The @deployable decorator registers this pack at import time

@deployable
def COMPETITOR_INTEL_PACK():
    """Competitor Intelligence Pack.
    
    Provides three pathways:
    - quick_snapshot: Fast overview (30 sec)
    - deep_research: Thorough analysis (2-5 min)
    - comparison: Multi-competitor comparison
    
    Triggers:
    - Webhook: POST /api/v1/webhooks/competitor-intel
    - Manual: POST /api/v1/pathways/{id}/run
    """
    return (
        pack_builder()
        .id("competitor_intel")
        .name("Competitor Intelligence")
        .description("Research and analyze competitors")
        .version("1.0.0")
        .author("Your Company")
        .tag("research", "sales", "competitive")
        
        # Triggers: How the pack gets invoked
        .trigger(
            id="webhook_snapshot",
            source="webhook",  # POST /api/v1/webhooks/competitor-snapshot
            pathway="competitor_intel.quick_snapshot.v1",
            description="Webhook trigger for quick snapshot",
        )
        .trigger(
            id="webhook_research",
            source="webhook",
            pathway="competitor_intel.deep_research.v1",
            description="Webhook trigger for deep research",
        )
        
        # Register pathways
        .pathway("competitor_intel.quick_snapshot.v1", build_quick_snapshot_pathway)
        .pathway("competitor_intel.deep_research.v1", build_deep_research_pathway)
        .pathway("competitor_intel.comparison.v1", build_comparison_pathway)
        
        # Tool requirements (documentation, not enforcement)
        .requires_tool("web.search")
        .requires_tool("web.fetch")
        .requires_tool("llm.generate")
        .requires_tool("code.execute")
        
        .build()
    )
