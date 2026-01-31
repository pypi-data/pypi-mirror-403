"""Agents - What you ship.

An agent is a stateful AI entity with:
- Persona (how it behaves)
- Goals (what it tries to achieve)
- Skills (from packs)
- Memory (persists across conversations)

Agents consume packs to get skills:
    agent_builder().use_pack("competitor_intel")

Example:
    @agent
    def MY_AGENT():
        return (
            agent_builder()
            .id("my_agent")
            .persona("You are a helpful analyst...")
            .goal("Help users understand topics deeply")
            .use_pack("research_skills")
            .as_reasoning_agent()
            .build()
        )
"""

from agents.registry import (
    agent,
    register_agent,
    list_available_agents,
    get_agent_by_id,
    resolve_agent_ids,
    clear_registry,
)

__all__ = [
    "agent",
    "register_agent",
    "list_available_agents",
    "get_agent_by_id",
    "resolve_agent_ids",
    "clear_registry",
]
