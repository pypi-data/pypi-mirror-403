"""Agent endpoint handlers.

Provides REST API for Agent CRUD and turn operations.
Host is pre-registered and cannot be deleted.
"""

from __future__ import annotations

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime


async def handle_list_agents(request: web.Request) -> web.Response:
    """GET /api/v1/agents - List all agents."""
    runtime = get_runtime(request)
    
    agents = runtime.agent_service.list()
    
    return web.json_response({
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "persona": agent.persona[:200] + "..." if len(agent.persona) > 200 else agent.persona,
                "goals": agent.goals,
                "tools": agent.capabilities.tools,
                "can_spawn": agent.capabilities.can_spawn,
                "model": agent.capabilities.model,
                "max_steps": agent.capabilities.max_steps_per_turn,
            }
            for agent in agents
        ]
    })


async def handle_get_agent(request: web.Request) -> web.Response:
    """GET /api/v1/agents/{agent_id} - Get agent details."""
    runtime = get_runtime(request)
    agent_id = request.match_info["agent_id"]
    
    agent = runtime.agent_service.get(agent_id)
    
    if agent is None:
        return error_response(
            request,
            f"Agent not found: {agent_id}",
            ErrorCode.NOT_FOUND,
            status=404,
        )
    
    # Get skill details
    skills_info = []
    for skill_id in agent.list_skills():
        skill = agent.get_skill(skill_id)
        if skill:
            skills_info.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "inputs": skill.inputs_schema,
                "outputs": skill.outputs_schema,
            })
    
    return web.json_response({
        "id": agent.id,
        "name": agent.name,
        "persona": agent.persona,
        "goals": agent.goals,
        "cognitive_style": agent.cognitive_style.to_dict() if hasattr(agent.cognitive_style, 'to_dict') else {},
        "capabilities": {
            "tools": agent.capabilities.tools,
            "can_spawn": agent.capabilities.can_spawn,
            "model": agent.capabilities.model,
            "max_steps_per_turn": agent.capabilities.max_steps_per_turn,
            "temperature": agent.capabilities.temperature,
        },
        "skills": skills_info,
        "skill_count": len(skills_info),
    })


async def handle_create_agent(request: web.Request) -> web.Response:
    """POST /api/v1/agents - Create a new agent.
    
    Request body:
        {
            "id": "researcher",
            "name": "Researcher",
            "persona": "You are a research specialist...",
            "goals": ["Find accurate information", "Summarize findings"],
            "tools": ["workspace.*", "web.*"],
            "can_spawn": false,
            "model": "auto",
            "max_steps": 10,
            "preset": "assistant"  // assistant, reasoning_agent, orator, supervisor
        }
    """
    runtime = get_runtime(request)
    
    try:
        body = await request.json()
    except Exception:
        return error_response(
            request,
            "Invalid JSON body",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    # Validate required fields
    agent_id = body.get("id")
    name = body.get("name")
    persona = body.get("persona", "")
    
    if not agent_id:
        return error_response(
            request,
            "Missing 'id' field",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    if not name:
        return error_response(
            request,
            "Missing 'name' field",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    try:
        agent = runtime.agent_service.create(
            id=agent_id,
            name=name,
            persona=persona,
            goals=body.get("goals"),
            tools=body.get("tools"),
            can_spawn=body.get("can_spawn", False),
            model=body.get("model", "auto"),
            max_steps=body.get("max_steps", 10),
            temperature=body.get("temperature", 0.7),
            preset=body.get("preset"),
        )
        
        return web.json_response({
            "id": agent.id,
            "name": agent.name,
            "created": True,
        }, status=201)
        
    except ValueError as e:
        return error_response(
            request,
            str(e),
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    except Exception as e:
        return error_response(
            request,
            str(e),
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )


async def handle_delete_agent(request: web.Request) -> web.Response:
    """DELETE /api/v1/agents/{agent_id} - Delete an agent."""
    runtime = get_runtime(request)
    agent_id = request.match_info["agent_id"]
    
    if agent_id == "host":
        return error_response(
            request,
            "Cannot delete Host agent",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    deleted = runtime.agent_service.delete(agent_id)
    
    return web.json_response({"deleted": deleted})


async def handle_agent_turn(request: web.Request) -> web.Response:
    """POST /api/v1/agents/{agent_id}/turn - Send message, get response.
    
    Request body:
        {
            "message": "What is the capital of France?",
            "thread_id": "optional-thread-id",
            "context": {"key": "value"},
            "attachments": []
        }
    
    Response:
        {
            "success": true,
            "response": "The capital of France is Paris.",
            "completed": true,
            "steps_taken": 1,
            "agent_id": "host",
            "thread_id": "..."
        }
    """
    runtime = get_runtime(request)
    agent_id = request.match_info["agent_id"]
    
    try:
        body = await request.json()
    except Exception:
        return error_response(
            request,
            "Invalid JSON body",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    message = body.get("message")
    if not message:
        return error_response(
            request,
            "Missing 'message' field",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    # Generate thread_id if not provided
    thread_id = body.get("thread_id")
    if not thread_id:
        import uuid
        thread_id = str(uuid.uuid4())
    
    try:
        result = await runtime.agent_service.turn(
            agent_id=agent_id,
            message=message,
            thread_id=thread_id,
            context=body.get("context"),
            attachments=body.get("attachments"),
        )
        
        return web.json_response(result)
        
    except Exception as e:
        return error_response(
            request,
            str(e),
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )


async def handle_list_agent_skills(request: web.Request) -> web.Response:
    """GET /api/v1/agents/{agent_id}/skills - List all skills for an agent."""
    runtime = get_runtime(request)
    agent_id = request.match_info["agent_id"]
    
    agent = runtime.agent_service.get(agent_id)
    
    if agent is None:
        return error_response(
            request,
            f"Agent not found: {agent_id}",
            ErrorCode.NOT_FOUND,
            status=404,
        )
    
    skills_info = []
    for skill_id in agent.list_skills():
        skill = agent.get_skill(skill_id)
        if skill:
            skills_info.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "inputs": skill.inputs_schema,
                "outputs": skill.outputs_schema,
            })
    
    return web.json_response({
        "agent_id": agent_id,
        "skills": skills_info,
        "count": len(skills_info),
    })


__all__ = [
    "handle_list_agents",
    "handle_get_agent",
    "handle_create_agent",
    "handle_delete_agent",
    "handle_agent_turn",
    "handle_list_agent_skills",
]
