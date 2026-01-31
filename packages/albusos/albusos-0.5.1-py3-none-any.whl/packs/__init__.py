"""Packs - Skill sets for agents.

To build good agents, you build good packs.

A pack bundles:
- Pathways (the actual computation graphs)
- Triggers (webhooks, timers, MCP events)

Agents consume packs:
    agent_builder().use_pack("my_pack")

Example:
    @deployable
    def MY_PACK():
        return (
            pack_builder()
            .id("my_pack")
            .pathway("my.skill.v1", build_skill_pathway)
            .trigger(id="on_request", source="webhook", pathway="my.skill.v1")
            .build()
        )
"""

from packs.registry import (
    deployable,
    register_pack,
    list_available_packs,
    get_pack_by_id,
    resolve_pack_ids,
    clear_registry,
)

__all__ = [
    "deployable",
    "register_pack",
    "list_available_packs",
    "get_pack_by_id",
    "resolve_pack_ids",
    "clear_registry",
]
