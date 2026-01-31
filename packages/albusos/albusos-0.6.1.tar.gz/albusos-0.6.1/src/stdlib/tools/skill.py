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


@register_tool(
    "skill.load",
    description="Load external skills from a directory path. Skills are discovered from directories containing SKILL.md files. By default loads into the current agent, but can target a specific agent.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Path to directory containing skills (with SKILL.md files)",
            },
            "recursive": {
                "type": "boolean",
                "description": "Search subdirectories recursively (default: true)",
                "default": True,
            },
            "agent_id": {
                "type": "string",
                "description": "Optional agent ID to load skills into. If not specified, loads into the current agent (the one calling this tool).",
            },
        },
        "required": ["directory"],
    },
)
async def skill_load(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """Load skills from a directory and add them to the current agent.
    
    This allows dynamic skill loading at runtime. Skills are loaded from
    directories containing SKILL.md files (Agent Skills format).
    """
    from pathlib import Path
    from pathway_engine.infrastructure.skill_loader import load_skills_from_directory
    
    directory = inputs.get("directory", "")
    recursive = inputs.get("recursive", True)
    target_agent_id = inputs.get("agent_id")  # Optional: load into specific agent
    
    if not directory:
        return {"success": False, "error": "directory parameter is required"}
    
    # Resolve path
    skill_dir = Path(directory)
    if not skill_dir.exists():
        return {"success": False, "error": f"Directory does not exist: {directory}"}
    
    if not skill_dir.is_dir():
        return {"success": False, "error": f"Not a directory: {directory}"}
    
    # Get agent service
    if not context:
        return {"success": False, "error": "No context - cannot determine agent"}
    
    agent_service = context.extras.get("agent_service")
    if not agent_service:
        return {"success": False, "error": "No agent_service in context - cannot load skills"}
    
    # Determine target agent: explicit agent_id or current agent
    if target_agent_id:
        agent_id = target_agent_id
    else:
        agent_id = context.extras.get("agent_id")
        if not agent_id:
            return {"success": False, "error": "No agent_id in context and no agent_id parameter - cannot load skills"}
    
    try:
        # Load skills from directory
        skills = await load_skills_from_directory(skill_dir, recursive=recursive)
        
        if not skills:
            return {
                "success": False,
                "error": f"No skills found in directory: {directory}",
                "hint": "Make sure the directory contains subdirectories with SKILL.md files",
            }
        
        # Get agent and add skills
        agent = agent_service.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent not found: {agent_id}"}
        
        loaded_skill_ids = []
        for skill_obj in skills:
            # Check if skill already exists
            if skill_obj.id in agent.list_skills():
                logger.info(f"Skill {skill_obj.id} already exists, skipping")
                continue
            
            agent.add_skill(skill_obj)
            loaded_skill_ids.append(skill_obj.id)
            logger.info(f"Loaded skill: {skill_obj.id} ({skill_obj.name})")
        
        return {
            "success": True,
            "loaded": loaded_skill_ids,
            "count": len(loaded_skill_ids),
            "agent_id": agent_id,
            "total_skills": len(agent.list_skills()),
            "message": f"Loaded {len(loaded_skill_ids)} skill(s) into agent {agent_id}",
        }
        
    except Exception as e:
        logger.error(f"Failed to load skills from {directory}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@register_tool(
    "skill.share",
    description="Share skills from one agent (typically Host) with another agent. This allows spawned agents to access Host's OSS skills.",
    parameters={
        "type": "object",
        "properties": {
            "from_agent_id": {
                "type": "string",
                "description": "Agent ID to copy skills from (default: 'host')",
                "default": "host",
            },
            "to_agent_id": {
                "type": "string",
                "description": "Agent ID to add skills to",
            },
            "skill_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific skill IDs to share (default: all skills)",
            },
        },
        "required": ["to_agent_id"],
    },
)
async def skill_share(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """Share skills from one agent to another.
    
    Typically used to share Host's OSS skills with spawned agents.
    """
    if not context:
        return {"success": False, "error": "No context"}
    
    agent_service = context.extras.get("agent_service")
    if not agent_service:
        return {"success": False, "error": "Agent service not available"}
    
    from_agent_id = inputs.get("from_agent_id", "host")
    to_agent_id = inputs.get("to_agent_id", "")
    skill_ids = inputs.get("skill_ids")  # None = all skills
    
    if not to_agent_id:
        return {"success": False, "error": "to_agent_id is required"}
    
    # Get source agent
    from_agent = agent_service.get(from_agent_id)
    if not from_agent:
        return {"success": False, "error": f"Source agent not found: {from_agent_id}"}
    
    # Get target agent
    to_agent = agent_service.get(to_agent_id)
    if not to_agent:
        return {"success": False, "error": f"Target agent not found: {to_agent_id}"}
    
    # Get skills to share
    if skill_ids:
        skills_to_share = [from_agent.get_skill(sid) for sid in skill_ids if from_agent.get_skill(sid)]
    else:
        # Share all skills
        skills_to_share = [from_agent.get_skill(sid) for sid in from_agent.list_skills() if from_agent.get_skill(sid)]
    
    # Add skills to target agent
    shared_count = 0
    skipped_count = 0
    shared_ids = []
    
    for skill_obj in skills_to_share:
        if skill_obj.id in to_agent.list_skills():
            skipped_count += 1
            continue
        
        to_agent.add_skill(skill_obj)
        shared_ids.append(skill_obj.id)
        shared_count += 1
        logger.info(f"Shared skill {skill_obj.id} from {from_agent_id} to {to_agent_id}")
    
    return {
        "success": True,
        "from_agent": from_agent_id,
        "to_agent": to_agent_id,
        "shared": shared_ids,
        "shared_count": shared_count,
        "skipped_count": skipped_count,
        "total_skills": len(to_agent.list_skills()),
        "message": f"Shared {shared_count} skill(s) from {from_agent_id} to {to_agent_id}",
    }


__all__ = ["skill_invoke", "skill_list", "skill_load", "skill_share"]
