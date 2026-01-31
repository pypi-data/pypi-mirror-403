"""Agent tools - spawn, invoke, and list agents.

These tools enable agent-to-agent communication:
- agent.spawn: Create a new specialist agent
- agent.turn: Send a message to another agent and get response
- agent.list: List available agents

Only agents with can_spawn=True (Host by default) can use agent.spawn.
All agents can use agent.turn and agent.list.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from stdlib.registry import register_tool

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


def _get_agent_service(context: "Context | None"):
    """Get AgentService from context.
    
    The service is injected via context.extras["agent_service"]
    by the runtime when setting up execution.
    """
    if not context:
        return None
    
    extras = getattr(context, "extras", None)
    if not extras:
        return None
    
    return extras.get("agent_service")


def _can_spawn(context: "Context | None") -> bool:
    """Check if the current agent has spawn capability."""
    if not context:
        return False
    
    extras = getattr(context, "extras", None)
    if not extras:
        return False
    
    # Check if current agent has can_spawn capability
    agent_service = extras.get("agent_service")
    current_agent_id = extras.get("agent_id")
    
    if agent_service and current_agent_id:
        agent = agent_service.get(current_agent_id)
        if agent and agent.capabilities.can_spawn:
            return True
    
    return False


@register_tool(
    "agent.spawn",
    description="""Create a new specialist agent. Only Host can spawn agents.

Use this to create workers for specific tasks:
- Researcher: for finding and synthesizing information
- Writer: for creating content
- Coder: for writing and reviewing code
- Analyst: for data analysis

Example:
    agent.spawn({
        "id": "researcher_1",
        "name": "Researcher",
        "persona": "You are a research specialist who finds accurate information.",
        "goals": ["Find relevant information", "Verify facts"],
        "tools": ["web.*", "workspace.*"]
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique identifier for the agent",
            },
            "name": {
                "type": "string",
                "description": "Display name",
            },
            "persona": {
                "type": "string",
                "description": "System prompt / identity description",
            },
            "goals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of goals for the agent",
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tool patterns (e.g., 'workspace.*', 'web.*')",
            },
            "model": {
                "type": "string",
                "description": "Model to use (default: 'auto')",
            },
            "max_steps": {
                "type": "integer",
                "description": "Max steps per turn (default: 10)",
            },
            "share_host_skills": {
                "type": "boolean",
                "description": "Share Host's OSS skills with this agent (default: false). Set to true to give spawned agent access to Host's skills like pdf, spreadsheet, etc.",
                "default": False,
            },
            "skills_directory": {
                "type": "string",
                "description": "Optional directory path to load skills from into this agent. Skills are discovered from directories containing SKILL.md files. If share_host_skills is also true, both Host's skills and skills from this directory will be loaded.",
            },
        },
        "required": ["id", "name", "persona"],
    },
)
async def agent_spawn(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """Create a new specialist agent.
    
    Only agents with can_spawn=True can use this tool.
    
    If share_host_skills=true, the spawned agent will have access to Host's OSS skills.
    """
    if not _can_spawn(context):
        return {
            "success": False,
            "error": "Permission denied: only Host can spawn agents",
        }
    
    agent_service = _get_agent_service(context)
    if not agent_service:
        return {
            "success": False,
            "error": "Agent service not available",
        }
    
    try:
        agent = agent_service.create(
            id=inputs["id"],
            name=inputs["name"],
            persona=inputs["persona"],
            goals=inputs.get("goals"),
            tools=inputs.get("tools"),
            can_spawn=False,  # Workers cannot spawn
            model=inputs.get("model", "auto"),
            max_steps=inputs.get("max_steps", 10),
        )
        
        # Optionally load skills from directory
        skills_dir = inputs.get("skills_directory")
        loaded_from_dir = []
        if skills_dir:
            from pathlib import Path
            from pathway_engine.infrastructure.skill_loader import load_skills_from_directory
            
            skill_dir_path = Path(skills_dir)
            if skill_dir_path.exists() and skill_dir_path.is_dir():
                try:
                    dir_skills = await load_skills_from_directory(skill_dir_path, recursive=True)
                    for skill_obj in dir_skills:
                        if skill_obj.id not in agent.list_skills():
                            agent.add_skill(skill_obj)
                            loaded_from_dir.append(skill_obj.id)
                            logger.info(f"Loaded skill {skill_obj.id} from {skills_dir} into {agent.id}")
                except Exception as e:
                    logger.warning(f"Failed to load skills from {skills_dir}: {e}", exc_info=True)
        
        # Optionally share Host's skills
        share_skills = inputs.get("share_host_skills", False)
        shared_from_host = []
        if share_skills:
            host = agent_service.get("host")
            if host:
                # Share all Host's skills (except domain-specific ones if needed)
                host_skills = host.list_skills()
                for skill_id in host_skills:
                    skill_obj = host.get_skill(skill_id)
                    if skill_obj and skill_id not in agent.list_skills():
                        agent.add_skill(skill_obj)
                        shared_from_host.append(skill_id)
                
                logger.info(f"Shared {len(shared_from_host)} skills from Host to {agent.id}")
        
        total_skills = len(agent.list_skills())
        messages = []
        if loaded_from_dir:
            messages.append(f"{len(loaded_from_dir)} skill(s) from {skills_dir}")
        if shared_from_host:
            messages.append(f"{len(shared_from_host)} skill(s) from Host")
        
        return {
            "success": True,
            "agent_id": agent.id,
            "name": agent.name,
            "skills_loaded_from_directory": loaded_from_dir,
            "skills_shared_from_host": shared_from_host,
            "total_skills": total_skills,
            "message": f"Created agent '{agent.name}' ({agent.id})" + (f" with {', '.join(messages)}" if messages else ""),
        }
        
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception("Failed to spawn agent")
        return {"success": False, "error": str(e)}


@register_tool(
    "agent.turn",
    description="""Send a message to another agent and get their response.

Use this to delegate tasks to specialist agents:
    agent.turn({
        "agent_id": "researcher_1",
        "message": "Find information about quantum computing applications"
    })
    
The agent will process the message and return their response.
""",
    parameters={
        "type": "object",
        "properties": {
            "agent_id": {
                "type": "string",
                "description": "ID of the agent to invoke",
            },
            "message": {
                "type": "string",
                "description": "Message / task for the agent",
            },
            "context": {
                "type": "object",
                "description": "Additional context to pass",
            },
        },
        "required": ["agent_id", "message"],
    },
)
async def agent_turn(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """Send a message to another agent and get response."""
    agent_service = _get_agent_service(context)
    if not agent_service:
        return {
            "success": False,
            "error": "Agent service not available",
        }
    
    agent_id = inputs.get("agent_id", "")
    message = inputs.get("message", "")
    extra_context = inputs.get("context", {})
    
    if not agent_id:
        return {"success": False, "error": "Missing agent_id"}
    if not message:
        return {"success": False, "error": "Missing message"}
    
    # Generate a thread_id for this interaction
    import uuid
    thread_id = f"agent_turn_{uuid.uuid4().hex[:8]}"
    
    try:
        result = await agent_service.turn(
            agent_id=agent_id,
            message=message,
            thread_id=thread_id,
            context=extra_context,
        )
        
        return {
            "success": result.get("success", False),
            "agent_id": agent_id,
            "response": result.get("response", ""),
            "completed": result.get("completed", False),
            "steps_taken": result.get("steps_taken", 0),
            "error": result.get("error"),
        }
        
    except Exception as e:
        logger.exception("Failed to invoke agent %s", agent_id)
        return {"success": False, "error": str(e)}


@register_tool(
    "agent.list",
    description="List all available agents.",
    parameters={
        "type": "object",
        "properties": {
            "include_host": {
                "type": "boolean",
                "description": "Include Host in the list (default: true)",
            },
        },
    },
)
async def agent_list(inputs: dict[str, Any], context: "Context | None" = None) -> dict[str, Any]:
    """List all available agents."""
    agent_service = _get_agent_service(context)
    if not agent_service:
        return {
            "agents": [],
            "count": 0,
            "error": "Agent service not available",
        }
    
    include_host = inputs.get("include_host", True)
    
    agents = agent_service.list()
    
    agent_list = []
    for agent in agents:
        if not include_host and agent.id == "host":
            continue
        agent_list.append({
            "id": agent.id,
            "name": agent.name,
            "goals": agent.goals,
            "can_spawn": agent.capabilities.can_spawn,
        })
    
    return {
        "agents": agent_list,
        "count": len(agent_list),
    }


__all__ = [
    "agent_spawn",
    "agent_turn",
    "agent_list",
]
