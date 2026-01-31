"""Skill tools - invoke agent skills (pathways) as tools.

Simple approach: skills are stored on the agent, passed via context.
No global registry, no complex lookup.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from stdlib.registry import register_tool

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


@register_tool(
    "skill.invoke",
    description="Invoke a skill by ID. Skills are pathways the agent can execute.",
    parameters={
        "type": "object",
        "properties": {
            "skill_id": {
                "type": "string",
                "description": "The skill ID to invoke",
            },
            "inputs": {
                "type": "object",
                "description": "Inputs to pass to the skill",
            },
        },
        "required": ["skill_id"],
    },
)
async def skill_invoke(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """Invoke a skill by ID.

    Skills are looked up from context.extras["skills"] (set by AgentLoop).
    """
    skill_id = inputs.get("skill_id", "")
    skill_inputs = inputs.get("inputs", {})

    # Get skills from context
    if not context:
        return {"success": False, "error": "No context - cannot find skills"}

    skills = getattr(context, "extras", {}).get("skills", {})

    if skill_id not in skills:
        return {
            "success": False,
            "error": f"Skill not found: {skill_id}",
            "available": list(skills.keys()),
        }

    skill = skills[skill_id]

    try:
        result = await skill.invoke(skill_inputs, context)
        return {"success": True, "skill_id": skill_id, **result}
    except Exception as e:
        logger.error(f"Skill {skill_id} failed: {e}", exc_info=True)
        return {"success": False, "skill_id": skill_id, "error": str(e)}


@register_tool(
    "skill.list",
    description="List available skills.",
    parameters={"type": "object", "properties": {}},
)
async def skill_list(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """List available skills from context."""
    if not context:
        return {"skills": [], "count": 0}

    skills = getattr(context, "extras", {}).get("skills", {})

    return {
        "skills": [
            {"id": sid, "name": s.name, "description": s.description}
            for sid, s in skills.items()
        ],
        "count": len(skills),
    }


__all__ = ["skill_invoke", "skill_list"]
