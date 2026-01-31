---
name: research
description: Search the web, look up information, find facts, gather data. Use when user needs current info or web lookups.
id: research
pathway_module: albus.application.agents.skills.research.pathway
pathway_function: build_research_pathway
inputs:
  message: string - What to research
outputs:
  response: string - Research findings
---

# Research Skill

Information gathering with web tools. Uses AgentLoopNode with web.* and search.* tools.

Use this skill for:
- Web searches
- Information lookup
- Current events
- Fact finding

Tools available:
- web.* - Web fetching and searching
- search.* - Search operations
