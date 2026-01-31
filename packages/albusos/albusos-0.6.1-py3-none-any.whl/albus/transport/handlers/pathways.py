"""Pathway endpoint handlers."""

from __future__ import annotations

import logging
import time
from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode, sanitize_error_message
from albus.transport.utils import (
    error_response,
    get_request_id,
    get_runtime,
    jsonable,
    parse_json_body,
)

logger = logging.getLogger(__name__)


async def handle_list_pathways(request: web.Request) -> web.Response:
    """GET /api/v1/pathways - List ALL pathways (pack + user)."""
    source_filter = request.query.get("source")
    include_pack = request.query.get("include_pack", "true").lower() != "false"
    include_user = request.query.get("include_user", "true").lower() != "false"

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathways = service.list(
        source_filter=source_filter,
        include_pack=include_pack,
        include_user=include_user,
    )

    return web.json_response(
        {
            "success": True,
            "pathways": [p.to_dict() for p in pathways],
            "count": len(pathways),
        }
    )


async def handle_create_pathway(request: web.Request) -> web.Response:
    """POST /api/v1/pathways - Create a new pathway."""
    request_id = get_request_id(request)

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    name = str(body.get("name", "")).strip() or "Untitled Pathway"
    description = str(body.get("description", "")).strip()
    nodes_raw = body.get("nodes", [])
    connections_raw = body.get("connections", [])
    workspace_id = body.get("workspace_id")

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway = service._pathway_from_dict(
            {
                "name": name,
                "description": description,
                "nodes": nodes_raw,
                "connections": connections_raw,
            }
        )

        meta = service.create(
            pathway,
            source=f"user:api",
            workspace_id=workspace_id,
        )

        return web.json_response(
            {
                "success": True,
                "pathway": meta.to_dict(),
                "doc_id": meta.doc_id,
                "pathway_id": meta.id,
            }
        )

    except Exception as e:
        logger.error("Failed to create pathway: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_get_pathway(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id} - Get pathway details."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    meta = service.get_meta(pathway_id)

    nodes = [service._serialize_node(node) for node in pathway.nodes.values()]
    connections = [{"from": c.from_node, "to": c.to_node} for c in pathway.connections]

    return web.json_response(
        {
            "success": True,
            "pathway": {
                "id": pathway.id,
                "name": pathway.name,
                "description": pathway.description,
                "nodes": nodes,
                "connections": connections,
                "metadata": dict(pathway.metadata),
            },
            "meta": meta.to_dict() if meta else None,
        }
    )


async def handle_run_pathway(request: web.Request) -> web.Response:
    """POST /api/v1/pathways/{pathway_id}/run - Run any pathway."""
    request_id = get_request_id(request)

    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)
    if body is None:
        body = {}

    inputs = body.get("inputs", {})
    if not isinstance(inputs, dict):
        return error_response(
            request, "inputs must be an object", ErrorCode.VALIDATION_ERROR, status=400
        )

    start = time.time()

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )
    
    # Log pathway details for debugging
    meta = service.get_meta(pathway_id)
    logger.info(
        f"[PathwayRun] Executing pathway_id={pathway_id}, name={pathway.name}, "
        f"source={meta.source if meta else 'unknown'}, nodes={len(pathway.nodes)}"
    )
    
    # Log agent loop configuration if present
    for node_id, node in pathway.nodes.items():
        if hasattr(node, "type") and node.type == "agent_loop":
            max_steps = getattr(node, "max_steps", None)
            logger.info(
                f"[PathwayRun] Agent node '{node_id}': max_steps={max_steps}, "
                f"reasoning_mode={getattr(node, 'reasoning_mode', 'react')}"
            )

    vm = getattr(runtime, "pathway_vm", None)

    if vm is None:
        return error_response(
            request,
            "No pathway executor available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    try:
        # Get pathway metadata for diagnostics
        meta = service.get_meta(pathway_id)
        
        # Extract max_steps from agent nodes for debugging
        agent_max_steps = None
        for node in pathway.nodes.values():
            if hasattr(node, "type") and node.type == "agent_loop":
                agent_max_steps = getattr(node, "max_steps", None)
                break
        
        record = await vm.execute(pathway, inputs)
        duration_ms = (time.time() - start) * 1000

        response_data = {
            "success": record.success,
            "outputs": record.outputs,
            "execution_id": record.id,
            "status": record.status.value,
            "duration_ms": duration_ms,
            "error": record.error,
        }
        
        # Add diagnostics in debug mode or when pathway info is available
        if meta or agent_max_steps is not None:
            response_data["_diagnostics"] = {
                "pathway_id": pathway_id,
                "pathway_name": pathway.name,
                "source": meta.source if meta else None,
                "agent_max_steps": agent_max_steps,
            }
        
        return web.json_response(response_data)

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(
            request,
            error_msg,
            ErrorCode.PATHWAY_EXECUTION_FAILED,
            status=500,
            details={"duration_ms": duration_ms},
        )


async def handle_export_pathway(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/export - Export pathway as JSON."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    export_data = service.export(pathway_id)

    if export_data is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    return web.json_response(export_data)


async def handle_import_pathway(request: web.Request) -> web.Response:
    """POST /api/v1/pathways/import - Import pathway from JSON."""
    request_id = get_request_id(request)

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    if body.get("format") != "albus.pathway.v1":
        return error_response(
            request,
            f"Unsupported format: {body.get('format')}",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )

    new_id = body.get("new_id")
    workspace_id = body.get("workspace_id")

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        meta = service.import_pathway(
            body,
            new_id=new_id,
            workspace_id=workspace_id,
        )

        return web.json_response(
            {
                "success": True,
                "pathway": meta.to_dict(),
            }
        )

    except Exception as e:
        logger.error("Failed to import pathway: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_pathway_graph(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/graph - Return compact graph payload."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    meta = service.get_meta(pathway_id)

    nodes = []
    for nid, node in (pathway.nodes or {}).items():
        ntype = getattr(node, "type", node.__class__.__name__)
        prompt = getattr(node, "prompt", None)
        if isinstance(prompt, str) and len(prompt) > 160:
            prompt = prompt[:157] + "..."
        nodes.append({"id": str(nid), "type": str(ntype), "prompt": prompt})

    conns = [(c.from_node, c.to_node) for c in (pathway.connections or [])]
    return web.json_response(
        {
            "success": True,
            "pathway_id": pathway.id,
            "source": meta.source if meta else None,
            "node_count": len(nodes),
            "nodes": nodes,
            "connections": conns,
        }
    )


async def handle_update_pathway(request: web.Request) -> web.Response:
    """PATCH /api/v1/pathways/{pathway_id} - Update pathway metadata."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        meta = service.update(
            pathway_id,
            name=body.get("name"),
            description=body.get("description"),
            metadata=body.get("metadata"),
        )

        return web.json_response(
            {
                "success": True,
                "pathway": meta.to_dict(),
            }
        )

    except ValueError as e:
        return error_response(request, str(e), ErrorCode.PATHWAY_NOT_FOUND, status=404)
    except Exception as e:
        logger.error("Failed to update pathway: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_delete_pathway(request: web.Request) -> web.Response:
    """DELETE /api/v1/pathways/{pathway_id} - Delete a pathway."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    deleted = service.delete(pathway_id)

    if not deleted:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    return web.json_response(
        {
            "success": True,
            "deleted": pathway_id,
        }
    )


# =============================================================================
# NODE CRUD
# =============================================================================


async def handle_list_nodes(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/nodes - List nodes in a pathway."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    nodes = [service._serialize_node(node) for node in pathway.nodes.values()]

    return web.json_response(
        {
            "success": True,
            "nodes": nodes,
            "count": len(nodes),
            "pathway_id": pathway_id,
        }
    )


async def handle_add_node(request: web.Request) -> web.Response:
    """POST /api/v1/pathways/{pathway_id}/nodes - Add a node to a pathway."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    # Validate required fields
    node_type = body.get("type")
    if not node_type:
        return error_response(
            request, "Node type is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway, node = service.add_node(pathway_id, body)

        return web.json_response(
            {
                "success": True,
                "node": service._serialize_node(node),
                "pathway_id": pathway_id,
                "node_count": len(pathway.nodes),
            }
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return error_response(
                request, error_msg, ErrorCode.PATHWAY_NOT_FOUND, status=404
            )
        return error_response(
            request, error_msg, ErrorCode.VALIDATION_ERROR, status=400
        )
    except Exception as e:
        logger.error("Failed to add node: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_get_node(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/nodes/{node_id} - Get a specific node."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    node_id = str(request.match_info.get("node_id") or "").strip()

    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )
    if not node_id:
        return error_response(
            request, "node_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    node = pathway.nodes.get(node_id)
    if node is None:
        return error_response(
            request, f"Node not found: {node_id}", ErrorCode.NOT_FOUND, status=404
        )

    # Get connections involving this node
    incoming = [
        {"from": c.from_node, "from_output": c.from_output, "to_input": c.to_input}
        for c in pathway.connections
        if c.to_node == node_id
    ]
    outgoing = [
        {"to": c.to_node, "from_output": c.from_output, "to_input": c.to_input}
        for c in pathway.connections
        if c.from_node == node_id
    ]

    return web.json_response(
        {
            "success": True,
            "node": service._serialize_node(node),
            "connections": {
                "incoming": incoming,
                "outgoing": outgoing,
            },
        }
    )


async def handle_update_node(request: web.Request) -> web.Response:
    """PATCH /api/v1/pathways/{pathway_id}/nodes/{node_id} - Update a node."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    node_id = str(request.match_info.get("node_id") or "").strip()

    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )
    if not node_id:
        return error_response(
            request, "node_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway, node = service.update_node(pathway_id, node_id, body)

        return web.json_response(
            {
                "success": True,
                "node": service._serialize_node(node),
                "pathway_id": pathway_id,
            }
        )

    except ValueError as e:
        error_msg = str(e)
        if "pathway not found" in error_msg.lower():
            return error_response(
                request, error_msg, ErrorCode.PATHWAY_NOT_FOUND, status=404
            )
        if "node not found" in error_msg.lower():
            return error_response(request, error_msg, ErrorCode.NOT_FOUND, status=404)
        return error_response(
            request, error_msg, ErrorCode.VALIDATION_ERROR, status=400
        )
    except Exception as e:
        logger.error("Failed to update node: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_delete_node(request: web.Request) -> web.Response:
    """DELETE /api/v1/pathways/{pathway_id}/nodes/{node_id} - Delete a node."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    node_id = str(request.match_info.get("node_id") or "").strip()

    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )
    if not node_id:
        return error_response(
            request, "node_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway = service.delete_node(pathway_id, node_id)

        return web.json_response(
            {
                "success": True,
                "deleted": node_id,
                "pathway_id": pathway_id,
                "node_count": len(pathway.nodes),
            }
        )

    except ValueError as e:
        error_msg = str(e)
        if "pathway not found" in error_msg.lower():
            return error_response(
                request, error_msg, ErrorCode.PATHWAY_NOT_FOUND, status=404
            )
        if "node not found" in error_msg.lower():
            return error_response(request, error_msg, ErrorCode.NOT_FOUND, status=404)
        return error_response(
            request, error_msg, ErrorCode.VALIDATION_ERROR, status=400
        )
    except Exception as e:
        logger.error("Failed to delete node: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


# =============================================================================
# CONNECTION CRUD
# =============================================================================


async def handle_list_connections(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/connections - List connections in a pathway."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    connections = [
        {
            "id": f"{c.from_node}:{c.to_node}",
            "from_node": c.from_node,
            "to_node": c.to_node,
            "from_output": c.from_output,
            "to_input": c.to_input,
        }
        for c in pathway.connections
    ]

    return web.json_response(
        {
            "success": True,
            "connections": connections,
            "count": len(connections),
            "pathway_id": pathway_id,
        }
    )


async def handle_add_connection(request: web.Request) -> web.Response:
    """POST /api/v1/pathways/{pathway_id}/connections - Add a connection."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)
    if body is None:
        return error_response(
            request, "Invalid JSON body", ErrorCode.BAD_REQUEST, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway, connection = service.add_connection(pathway_id, body)

        return web.json_response(
            {
                "success": True,
                "connection": {
                    "id": f"{connection.from_node}:{connection.to_node}",
                    "from_node": connection.from_node,
                    "to_node": connection.to_node,
                    "from_output": connection.from_output,
                    "to_input": connection.to_input,
                },
                "pathway_id": pathway_id,
                "connection_count": len(pathway.connections),
            }
        )

    except ValueError as e:
        error_msg = str(e)
        if "pathway not found" in error_msg.lower():
            return error_response(
                request, error_msg, ErrorCode.PATHWAY_NOT_FOUND, status=404
            )
        return error_response(
            request, error_msg, ErrorCode.VALIDATION_ERROR, status=400
        )
    except Exception as e:
        logger.error("Failed to add connection: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


async def handle_delete_connection(request: web.Request) -> web.Response:
    """DELETE /api/v1/pathways/{pathway_id}/connections/{connection_id} - Delete a connection."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    connection_id = str(request.match_info.get("connection_id") or "").strip()

    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )
    if not connection_id:
        return error_response(
            request, "connection_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    # Parse connection_id (format: "from_node:to_node")
    if ":" not in connection_id:
        return error_response(
            request,
            "Invalid connection_id format. Expected 'from_node:to_node'",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )

    parts = connection_id.split(":", 1)
    from_node = parts[0]
    to_node = parts[1]

    runtime = get_runtime(request)
    service = runtime.pathway_service

    try:
        pathway = service.delete_connection(pathway_id, from_node, to_node)

        return web.json_response(
            {
                "success": True,
                "deleted": connection_id,
                "pathway_id": pathway_id,
                "connection_count": len(pathway.connections),
            }
        )

    except ValueError as e:
        error_msg = str(e)
        if "pathway not found" in error_msg.lower():
            return error_response(
                request, error_msg, ErrorCode.PATHWAY_NOT_FOUND, status=404
            )
        if "connection not found" in error_msg.lower():
            return error_response(request, error_msg, ErrorCode.NOT_FOUND, status=404)
        return error_response(
            request, error_msg, ErrorCode.VALIDATION_ERROR, status=400
        )
    except Exception as e:
        logger.error("Failed to delete connection: %s", e)
        error_msg = sanitize_error_message(str(e), is_production=None)
        return error_response(request, error_msg, ErrorCode.PATHWAY_INVALID, status=500)


# =============================================================================
# VALIDATION
# =============================================================================


async def handle_validate_pathway(request: web.Request) -> web.Response:
    """POST /api/v1/pathways/{pathway_id}/validate - Validate a pathway before running."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    # Get VM context for tool validation
    vm = getattr(runtime, "pathway_vm", None)
    if vm is None:
        return error_response(
            request,
            "No pathway executor available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    from pathway_engine.application.validation import validate_pathway

    result = validate_pathway(pathway, vm.ctx)

    return web.json_response(
        {
            "valid": result.valid,
            "errors": [e.to_dict() for e in result.errors],
            "warnings": [w.to_dict() for w in result.warnings],
            "pathway_id": pathway_id,
            "node_count": len(pathway.nodes),
            "connection_count": len(pathway.connections),
        }
    )


# =============================================================================
# VISUALIZATION ENDPOINTS
# =============================================================================


async def handle_pathway_viz(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/viz - Render pathway as interactive D3 visualization."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    # Generate D3 JSON data
    from stdlib.tools.viz import pathway_to_d3_json
    import json

    d3_data = pathway_to_d3_json(pathway)

    # Generate interactive HTML page
    html = _generate_d3_html(pathway_id, d3_data)
    return web.Response(text=html, content_type="text/html")


async def handle_pathway_mermaid(request: web.Request) -> web.Response:
    """GET /api/v1/pathways/{pathway_id}/mermaid - Return pathway as Mermaid diagram."""
    pathway_id = str(request.match_info.get("pathway_id") or "").strip()
    if not pathway_id:
        return error_response(
            request, "pathway_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    runtime = get_runtime(request)
    service = runtime.pathway_service
    pathway = service.load(pathway_id)

    if pathway is None:
        return error_response(
            request,
            f"Pathway not found: {pathway_id}",
            ErrorCode.PATHWAY_NOT_FOUND,
            status=404,
        )

    from stdlib.tools.viz import pathway_to_mermaid

    # Get query params
    show_types = request.query.get("types", "true").lower() == "true"
    show_prompts = request.query.get("prompts", "false").lower() == "true"
    direction = request.query.get("direction", "LR").upper()

    mermaid_code = pathway_to_mermaid(
        pathway,
        direction=direction,
        show_types=show_types,
        show_prompts=show_prompts,
    )

    # Check if HTML wrapper is requested
    if request.query.get("html", "false").lower() == "true":
        html = _generate_mermaid_html(pathway_id, mermaid_code)
        return web.Response(text=html, content_type="text/html")

    return web.Response(text=mermaid_code, content_type="text/plain")


def _generate_d3_html(pathway_id: str, d3_data: dict) -> str:
    """Generate interactive D3 visualization HTML."""
    import json

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pathway: {pathway_id}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }}
        header {{ padding: 16px 24px; background: #16213e; border-bottom: 1px solid #0f3460; }}
        header h1 {{ font-size: 18px; font-weight: 500; }}
        header span {{ color: #888; font-size: 14px; margin-left: 12px; }}
        #graph {{ width: 100vw; height: calc(100vh - 60px); }}
        .node {{ cursor: pointer; }}
        .node rect {{ stroke-width: 2px; rx: 8; ry: 8; }}
        .node.llm rect {{ fill: #e1f5fe; stroke: #01579b; }}
        .node.tool rect {{ fill: #f3e5f5; stroke: #4a148c; }}
        .node.transform rect {{ fill: #fff3e0; stroke: #e65100; }}
        .node.router rect {{ fill: #fce4ec; stroke: #880e4f; }}
        .node.agent rect {{ fill: #e8f5e9; stroke: #1b5e20; }}
        .node.input rect {{ fill: #f5f5f5; stroke: #424242; }}
        .node text {{ font-size: 12px; fill: #333; }}
        .link {{ fill: none; stroke: #666; stroke-width: 2px; marker-end: url(#arrow); }}
        .tooltip {{ position: absolute; background: #16213e; border: 1px solid #0f3460; padding: 12px; border-radius: 8px; font-size: 13px; max-width: 300px; pointer-events: none; }}
        .tooltip h4 {{ margin-bottom: 8px; color: #4fc3f7; }}
        .tooltip p {{ color: #aaa; margin: 4px 0; }}
    </style>
</head>
<body>
    <header>
        <h1>{pathway_id}</h1>
        <span>{d3_data.get('pathway_name', '')}</span>
    </header>
    <div id="graph"></div>
    <div id="tooltip" class="tooltip" style="display: none;"></div>
    <script>
        const data = {json.dumps(d3_data)};
        
        const width = window.innerWidth;
        const height = window.innerHeight - 60;
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // Arrow marker
        svg.append("defs").append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#666");
        
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(60));
        
        const link = svg.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("class", "link");
        
        const node = svg.append("g")
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .attr("class", d => "node " + (d.group || "input"))
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        node.append("rect")
            .attr("width", 100)
            .attr("height", 40)
            .attr("x", -50)
            .attr("y", -20);
        
        node.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", 5)
            .text(d => d.label);
        
        const tooltip = d3.select("#tooltip");
        
        node.on("mouseover", (event, d) => {{
            let html = `<h4>${{d.label}}</h4><p>Type: ${{d.type}}</p>`;
            if (d.prompt) html += `<p>Prompt: ${{d.prompt.substring(0, 100)}}...</p>`;
            if (d.tool) html += `<p>Tool: ${{d.tool}}</p>`;
            if (d.model) html += `<p>Model: ${{d.model}}</p>`;
            tooltip.html(html)
                .style("display", "block")
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY + 10) + "px");
        }})
        .on("mouseout", () => tooltip.style("display", "none"));
        
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});
        
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>"""


def _generate_mermaid_html(pathway_id: str, mermaid_code: str) -> str:
    """Generate HTML page with Mermaid diagram."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pathway: {pathway_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 24px; }}
        header {{ margin-bottom: 24px; }}
        header h1 {{ font-size: 24px; font-weight: 500; color: #333; }}
        .mermaid {{ background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        pre {{ margin-top: 24px; background: #1a1a2e; color: #eee; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        code {{ font-family: 'SF Mono', Monaco, monospace; font-size: 13px; }}
    </style>
</head>
<body>
    <header>
        <h1>Pathway: {pathway_id}</h1>
    </header>
    <div class="mermaid">
{mermaid_code}
    </div>
    <pre><code>{mermaid_code}</code></pre>
    <script>mermaid.initialize({{ startOnLoad: true, theme: 'default' }});</script>
</body>
</html>"""


__all__ = [
    # Pathway CRUD
    "handle_list_pathways",
    "handle_create_pathway",
    "handle_get_pathway",
    "handle_update_pathway",
    "handle_delete_pathway",
    "handle_run_pathway",
    "handle_export_pathway",
    "handle_import_pathway",
    "handle_pathway_graph",
    # Node CRUD
    "handle_list_nodes",
    "handle_add_node",
    "handle_get_node",
    "handle_update_node",
    "handle_delete_node",
    # Connection CRUD
    "handle_list_connections",
    "handle_add_connection",
    "handle_delete_connection",
    # Validation
    "handle_validate_pathway",
    # Visualization
    "handle_pathway_viz",
    "handle_pathway_mermaid",
]
