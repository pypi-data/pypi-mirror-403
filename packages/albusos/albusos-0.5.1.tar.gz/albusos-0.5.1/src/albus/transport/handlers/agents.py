"""Agent endpoints (availability + deployment + execution).

Agents are persistent AI entities with skills, memory, and identity.
They are NOT auto-deployed by default - deployment is explicit.

Endpoints:
    GET  /api/v1/agents           - List available agents
    GET  /api/v1/agents/deployed  - List deployed agents
    POST /api/v1/agents/deploy    - Deploy agents
    GET  /api/v1/agents/{id}      - Get agent details
    POST /api/v1/agents/{id}/turn - Run an agent turn
"""

from __future__ import annotations

import uuid
from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime, parse_json_body


def _get_extras(runtime: Any) -> dict:
    """Get VM context extras."""
    vm = getattr(runtime, "pathway_vm", None)
    ctx = getattr(vm, "ctx", None)
    return getattr(ctx, "extras", {}) if ctx is not None else {}


def _get_agent_service(runtime: Any):
    """Get the AgentService from runtime extras."""
    return _get_extras(runtime).get("agent_service")


async def handle_list_available_agents(request: web.Request) -> web.Response:
    """GET /api/v1/agents - List agents available in this server build.

    Each agent includes a 'deployed' boolean indicating if it's currently active.
    """
    from agents.registry import list_available_agents

    runtime = get_runtime(request)
    agent_service = _get_agent_service(runtime)

    # Get deployed agent IDs
    deployed_ids: set[str] = set()
    if agent_service:
        try:
            for meta in agent_service.list():
                deployed_ids.add(meta.id)
        except Exception:
            pass

    agents = list_available_agents()
    agents_data = []
    for a in agents:
        agents_data.append({
            "id": a.id,
            "name": a.name,
            "persona": a.persona[:200] + "..." if len(a.persona) > 200 else a.persona,
            "goals": a.goals,
            "skills": list(a._skills.keys()),
            "tools": a.capabilities.tools,
            "cognitive_style": a.cognitive_style.to_dict(),
            "deployed": a.id in deployed_ids,
        })

    return web.json_response({
        "success": True,
        "agents": agents_data,
    })


async def handle_list_deployed_agents(request: web.Request) -> web.Response:
    """GET /api/v1/agents/deployed - List deployed agents."""
    runtime = get_runtime(request)
    agent_service = _get_agent_service(runtime)

    if not agent_service:
        return web.json_response({
            "success": True,
            "agents": [],
            "message": "AgentService not initialized",
        })

    metas = agent_service.list()
    return web.json_response({
        "success": True,
        "agents": [m.to_dict() for m in metas],
    })


async def handle_deploy_agents(request: web.Request) -> web.Response:
    """POST /api/v1/agents/deploy - Deploy one or more agents into the runtime.

    Body:
      { "agent_ids": ["<agent_id>", "..."], "force": false }

    Discover available agent IDs via:
      GET /api/v1/agents
    """
    from agents.registry import resolve_agent_ids

    runtime = get_runtime(request)
    agent_service = _get_agent_service(runtime)

    if not agent_service:
        return error_response(
            request,
            "agent_service_not_available",
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )

    body = await parse_json_body(request) or {}
    agent_ids = body.get("agent_ids")
    force = bool(body.get("force", False))

    if isinstance(agent_ids, str):
        agent_ids = [agent_ids]
    if not isinstance(agent_ids, list) or not all(isinstance(x, str) for x in agent_ids):
        return error_response(
            request,
            "agent_ids must be a list of strings",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )

    agents, missing = resolve_agent_ids(agent_ids)
    if missing:
        return error_response(
            request,
            "unknown agent_id(s)",
            ErrorCode.VALIDATION_ERROR,
            status=400,
            details={"missing": missing},
        )

    deployed: list[dict[str, Any]] = []
    deployed_agents: list[str] = []
    skipped_agents: list[str] = []

    # Detect currently deployed agents
    already_deployed: set[str] = set()
    try:
        for meta in agent_service.list():
            already_deployed.add(meta.id)
    except Exception:
        pass

    for a in agents:
        if (a.id in already_deployed) and not force:
            skipped_agents.append(a.id)
            continue

        meta = agent_service.register(a, source=f"code:agents.{a.id}")
        deployed_agents.append(a.id)
        deployed.append(meta.to_dict())

    return web.json_response({
        "success": True,
        "deployed_agents": deployed_agents,
        "skipped_agents": skipped_agents,
        "deployed": deployed,
    })


async def handle_get_agent(request: web.Request) -> web.Response:
    """GET /api/v1/agents/{agent_id} - Get agent details."""
    runtime = get_runtime(request)
    agent_service = _get_agent_service(runtime)
    agent_id = request.match_info["agent_id"]

    if not agent_service:
        return error_response(
            request,
            "agent_service_not_available",
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )

    agent = agent_service.load(agent_id)
    if not agent:
        # Try from registry (not deployed)
        from agents.registry import get_agent_by_id
        agent = get_agent_by_id(agent_id)
        if not agent:
            return error_response(
                request,
                f"Agent not found: {agent_id}",
                ErrorCode.NOT_FOUND,
                status=404,
            )
        deployed = False
    else:
        deployed = True

    return web.json_response({
        "success": True,
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "persona": agent.persona,
            "goals": agent.goals,
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "inputs_schema": s.inputs_schema,
                    "outputs_schema": s.outputs_schema,
                }
                for s in agent._skills.values()
            ],
            "tools": agent.capabilities.tools,
            "cognitive_style": agent.cognitive_style.to_dict(),
            "capabilities": {
                "max_steps_per_turn": agent.capabilities.max_steps_per_turn,
                "model": agent.capabilities.model,
                "temperature": agent.capabilities.temperature,
            },
            "deployed": deployed,
        },
    })


async def handle_agent_turn(request: web.Request) -> web.Response:
    """POST /api/v1/agents/{agent_id}/turn - Run an agent turn.

    Body:
      {
        "message": "What should I research?",
        "thread_id": "conv_123",  // Optional, auto-generated if not provided
        "context": {},            // Optional additional context
        "attachments": []         // Optional attachments
      }

    Returns:
      {
        "success": true,
        "response": "...",
        "thread_id": "conv_123",
        "completed": true,
        "steps_taken": 3,
        "step_results": [...]
      }
    """
    runtime = get_runtime(request)
    agent_service = _get_agent_service(runtime)
    agent_id = request.match_info["agent_id"]

    if not agent_service:
        return error_response(
            request,
            "agent_service_not_available",
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )

    body = await parse_json_body(request) or {}
    message = body.get("message")
    if not message or not isinstance(message, str):
        return error_response(
            request,
            "message is required",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )

    thread_id = body.get("thread_id") or f"thread_{uuid.uuid4().hex[:12]}"
    context = body.get("context") or {}
    attachments = body.get("attachments") or []

    # Get execution context from VM
    vm = getattr(runtime, "pathway_vm", None)
    ctx = getattr(vm, "ctx", None)
    if not ctx:
        return error_response(
            request,
            "execution_context_not_available",
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )

    try:
        result = await agent_service.turn(
            agent_id,
            message=message,
            thread_id=thread_id,
            ctx=ctx,
            attachments=attachments,
            context=context,
        )

        if "error" in result:
            return error_response(
                request,
                result["error"],
                ErrorCode.NOT_FOUND if "not found" in result["error"].lower() else ErrorCode.INTERNAL_ERROR,
                status=404 if "not found" in result["error"].lower() else 500,
            )

        return web.json_response({
            "success": True,
            **result,
        })

    except Exception as e:
        return error_response(
            request,
            str(e),
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )


__all__ = [
    "handle_list_available_agents",
    "handle_list_deployed_agents",
    "handle_deploy_agents",
    "handle_get_agent",
    "handle_agent_turn",
]
