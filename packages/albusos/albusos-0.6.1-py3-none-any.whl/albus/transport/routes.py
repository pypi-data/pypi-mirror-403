"""Route registration for Albus API.

All routes are versioned under /api/v1/ prefix.
"""

from __future__ import annotations

from typing import Any, Callable

from aiohttp import web


def register_route(
    router: web.UrlDispatcher,
    method: str,
    path: str,
    handler: Callable[[web.Request], Any],
) -> None:
    """Register a versioned route.

    Args:
        router: aiohttp router
        method: HTTP method (get, post, delete, etc.)
        path: Route path (will be prefixed with /api/v1/)
        handler: Handler function
    """
    method_lower = method.lower()
    add_method = getattr(router, f"add_{method_lower}")

    # Ensure path starts with /api/v1
    if path.startswith("/api/v1"):
        versioned_path = path
    elif path == "/":
        # Root endpoint is special - keep it at root for discovery
        versioned_path = "/"
    else:
        versioned_path = f"/api/v1{path}"

    add_method(versioned_path, handler)


def register_routes(app: web.Application) -> None:
    """Register all versioned routes for the application.

    All routes are under /api/v1/ except root (/) for API discovery.

    Args:
        app: aiohttp Application
    """
    from albus.transport.handlers import (
        agents,
        chat,
        docs,
        infrastructure,
        pathways,
        runs,
        threads,
        tools,
        webhooks,
        websocket,
    )

    router = app.router

    # Root endpoint (for API discovery)
    router.add_get("/", infrastructure.handle_root)
    router.add_get("/api/v1", infrastructure.handle_root)

    # Docs endpoints
    register_route(router, "get", "/openapi.json", docs.handle_openapi)
    register_route(router, "get", "/docs", docs.handle_docs)

    # Chat endpoint (convenience wrapper for Host agent - recommended entry point)
    # Provides pathway editor, agent editor, and co-creator capabilities
    register_route(router, "post", "/chat", chat.handle_chat)

    # Agent endpoints (Agent is THE primitive)
    register_route(router, "get", "/agents", agents.handle_list_agents)
    register_route(router, "post", "/agents", agents.handle_create_agent)
    register_route(router, "get", "/agents/{agent_id}", agents.handle_get_agent)
    register_route(router, "delete", "/agents/{agent_id}", agents.handle_delete_agent)
    register_route(router, "post", "/agents/{agent_id}/turn", agents.handle_agent_turn)
    register_route(router, "get", "/agents/{agent_id}/skills", agents.handle_list_agent_skills)

    # Pathway endpoints
    register_route(router, "get", "/pathways", pathways.handle_list_pathways)
    register_route(router, "post", "/pathways", pathways.handle_create_pathway)
    register_route(router, "post", "/pathways/import", pathways.handle_import_pathway)
    register_route(router, "get", "/pathways/{pathway_id}", pathways.handle_get_pathway)
    register_route(
        router, "patch", "/pathways/{pathway_id}", pathways.handle_update_pathway
    )
    register_route(
        router, "delete", "/pathways/{pathway_id}", pathways.handle_delete_pathway
    )
    register_route(
        router, "post", "/pathways/{pathway_id}/run", pathways.handle_run_pathway
    )
    register_route(
        router,
        "post",
        "/pathways/{pathway_id}/validate",
        pathways.handle_validate_pathway,
    )
    register_route(
        router, "get", "/pathways/{pathway_id}/graph", pathways.handle_pathway_graph
    )
    register_route(
        router, "get", "/pathways/{pathway_id}/export", pathways.handle_export_pathway
    )
    register_route(
        router, "get", "/pathways/{pathway_id}/viz", pathways.handle_pathway_viz
    )
    register_route(
        router, "get", "/pathways/{pathway_id}/mermaid", pathways.handle_pathway_mermaid
    )

    # Pathway node endpoints
    register_route(
        router, "get", "/pathways/{pathway_id}/nodes", pathways.handle_list_nodes
    )
    register_route(
        router, "post", "/pathways/{pathway_id}/nodes", pathways.handle_add_node
    )
    register_route(
        router,
        "get",
        "/pathways/{pathway_id}/nodes/{node_id}",
        pathways.handle_get_node,
    )
    register_route(
        router,
        "patch",
        "/pathways/{pathway_id}/nodes/{node_id}",
        pathways.handle_update_node,
    )
    register_route(
        router,
        "delete",
        "/pathways/{pathway_id}/nodes/{node_id}",
        pathways.handle_delete_node,
    )

    # Pathway connection endpoints
    register_route(
        router,
        "get",
        "/pathways/{pathway_id}/connections",
        pathways.handle_list_connections,
    )
    register_route(
        router,
        "post",
        "/pathways/{pathway_id}/connections",
        pathways.handle_add_connection,
    )
    register_route(
        router,
        "delete",
        "/pathways/{pathway_id}/connections/{connection_id}",
        pathways.handle_delete_connection,
    )

    # Tool endpoints
    register_route(router, "get", "/tools", tools.handle_list_tools)
    register_route(router, "post", "/tools/{tool_name}", tools.handle_tool_call)

    # WebSocket & webhook endpoints
    register_route(router, "get", "/ws", websocket.handle_ws)
    register_route(router, "post", "/webhooks/{topic}", webhooks.handle_webhook)

    # Thread endpoints
    register_route(router, "get", "/threads", threads.handle_list_threads)
    register_route(router, "get", "/threads/{thread_id}", threads.handle_get_thread)
    register_route(
        router, "delete", "/threads/{thread_id}", threads.handle_delete_thread
    )
    register_route(
        router, "post", "/threads/{thread_id}/events", threads.handle_send_event
    )

    # Run inspection endpoints (for Studio debugging)
    register_route(router, "get", "/runs", runs.handle_list_runs)
    register_route(router, "get", "/runs/{run_id}", runs.handle_get_run)
    register_route(router, "get", "/runs/{run_id}/spans", runs.handle_get_run_spans)
    register_route(router, "get", "/runs/{run_id}/events", runs.handle_get_run_events)
    register_route(
        router, "get", "/runs/{run_id}/timeline", runs.handle_get_run_timeline
    )

    # Infrastructure endpoints
    register_route(router, "get", "/health", infrastructure.handle_health)
    register_route(
        router, "get", "/config/validate", infrastructure.handle_config_validate
    )
    register_route(router, "get", "/config/models", infrastructure.handle_config_models)
    register_route(
        router, "patch", "/config/models", infrastructure.handle_config_models_update
    )
    register_route(router, "get", "/help", infrastructure.handle_help)
    register_route(router, "get", "/node-types", infrastructure.handle_node_types)


__all__ = [
    "register_route",
    "register_routes",
]
