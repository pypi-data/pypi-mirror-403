"""Infrastructure endpoint handlers (health, help, config, node-types)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiohttp import web

from stdlib.registry import TOOL_HANDLERS
from albus.infrastructure.config import AlbusConfig, get_config
from albus.transport.utils import get_request_id, get_runtime


async def handle_root(_: web.Request) -> web.Response:
    """GET / or GET /api/v1 - API info and endpoint discovery."""
    return web.json_response(
        {
            "name": "AlbusOS",
            "version": "1.0",
            "api_version": "v1",
            "description": "A runtime for AI agents. Build pathways, wire tools, run agents.",
            "base_url": "/api/v1",
            "endpoints": {
                "health": {"GET /api/v1/health": "Health check with dependency status"},
                "config": {
                    "GET /api/v1/config/validate": "Validate configuration",
                    "GET /api/v1/config/models": "Get model routing config",
                    "PATCH /api/v1/config/models": "Update model routing (runtime)",
                },
                "tools": {
                    "GET /api/v1/tools": "List all tools",
                    "POST /api/v1/tools/{name}": "Execute a tool",
                },
                "pathways": {
                    "GET /api/v1/pathways": "List all pathways",
                    "POST /api/v1/pathways": "Create a pathway",
                    "GET /api/v1/pathways/{id}": "Get pathway details",
                    "POST /api/v1/pathways/{id}/run": "Run a pathway",
                    "GET /api/v1/pathways/{id}/export": "Export as JSON",
                    "POST /api/v1/pathways/import": "Import from JSON",
                    "GET /api/v1/pathways/{id}/graph": "Get pathway graph data",
                },
                "threads": {
                    "GET /api/v1/threads": "List threads",
                    "GET /api/v1/threads/{id}": "Get thread",
                    "DELETE /api/v1/threads/{id}": "Delete thread",
                },
                "realtime": {
                    "GET /api/v1/ws": "WebSocket (events/rpc)",
                    "POST /api/v1/webhooks/{topic}": "Publish webhook event",
                },
                "docs": {
                    "GET /api/v1/help": "Comprehensive API help",
                    "GET /api/v1/node-types": "List node types for pathway creation",
                    "GET /api/v1/openapi.json": "OpenAPI 3.0 specification",
                    "GET /api/v1/docs": "Interactive API docs (Swagger UI)",
                },
            },
            "tool_categories": sorted(
                set(name.split(".")[0] for name in TOOL_HANDLERS.keys())
            ),
            "node_types": [
                "llm",
                "tool",
                "transform",
                "gate",
                "router",
                "code",
                "code_generator",
                "memory_read",
                "memory_write",
                "agent_loop",
                "map",
                "retry",
                "timeout",
                "fallback",
            ],
            "docs": "https://github.com/albusstudio/albusOS",
        }
    )


async def handle_health(request: web.Request) -> web.Response:
    """GET /api/v1/health - Enhanced health check with dependency status."""
    request_id = get_request_id(request)
    checks: dict[str, str] = {}
    overall_status = "ok"

    # Check runtime
    runtime = None
    try:
        # Runtime is stored under an AppKey (see albus.transport.utils.RUNTIME_KEY)
        runtime = get_runtime(request)
    except Exception:
        runtime = None

    if runtime is not None:
        checks["runtime"] = "ok"
    else:
        checks["runtime"] = "down"
        overall_status = "down"

    # Check PathwayVM
    vm = None
    if runtime is not None:
        vm = getattr(runtime, "pathway_vm", None)
    if vm is not None:
        checks["pathway_vm"] = "ok"
    else:
        checks["pathway_vm"] = "down"
        overall_status = "down"

    # Check LLM providers
    config = get_config()
    has_llm = bool(
        config.llm.openai_api_key
        or config.llm.anthropic_api_key
        or config.llm.google_api_key
        or config.llm.ollama_host
    )
    if has_llm:
        checks["llm"] = "ok"
    else:
        checks["llm"] = "not_configured"
        if overall_status == "ok":
            overall_status = "degraded"

    # Check persistence
    if config.persistence.database_url:
        checks["persistence"] = "ok"
    else:
        checks["persistence"] = "not_configured"

    return web.json_response(
        {
            "status": overall_status,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
        }
    )


async def handle_config_validate(request: web.Request) -> web.Response:
    """GET /api/v1/config/validate - Validate configuration."""
    request_id = get_request_id(request)
    errors: list[str] = []
    warnings: list[str] = []
    deploy_errors: list[str] = []
    deploy_source: str = "unknown"
    config: AlbusConfig | None = None
    try:
        config = AlbusConfig.from_env(validate_required=False)
        config.validate()
    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Configuration error: {str(e)}")

    # Validate deployment config (albus.yaml)
    try:
        from albus.infrastructure.deployment import DeploymentConfig

        deploy_config = DeploymentConfig.load()
        deploy_source = deploy_config.source
        deploy_errors = deploy_config.validate()
        if deploy_source == "none":
            warnings.append(
                "No deployment config file found (no packs/MCP servers will be deployed)"
            )
    except Exception as e:
        deploy_errors = [f"Deployment configuration error: {str(e)}"]

    # Check for warnings
    if (
        config is not None
        and not config.llm.openai_api_key
        and not config.llm.anthropic_api_key
    ):
        warnings.append("No primary LLM provider configured (OpenAI/Anthropic)")

    if config is not None and not config.persistence.database_url:
        warnings.append("Using file-based persistence (not suitable for production)")

    return web.json_response(
        {
            "valid": len(errors) == 0 and len(deploy_errors) == 0,
            "errors": errors,
            "deployment": {
                "source": deploy_source,
                "errors": deploy_errors,
            },
            "warnings": warnings,
            "config": config.to_dict() if config is not None else {},
            "request_id": request_id,
        }
    )


async def handle_config_models(request: web.Request) -> web.Response:
    """GET /api/v1/config/models - Get current model routing configuration."""
    request_id = get_request_id(request)

    try:
        from stdlib.llm.capability_routing import (
            get_runtime_model_config,
            BATTERY_PACKS,
            get_battery_pack,
        )

        runtime_config = get_runtime_model_config()
        current_pack = get_battery_pack()
        pack_routes = BATTERY_PACKS.get(current_pack, {})

        # Get list of available models from Ollama (if available)
        available_local_models: list[str] = []
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        available_local_models = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass  # Ollama not running or not accessible

        return web.json_response(
            {
                "success": True,
                "config": runtime_config,
                "effective_routes": {k: v for k, v in pack_routes.items() if v},
                "available_profiles": list(BATTERY_PACKS.keys()),
                "available_local_models": available_local_models,
                "request_id": request_id,
            }
        )
    except Exception as e:
        return web.json_response(
            {
                "success": False,
                "error": str(e),
                "request_id": request_id,
            },
            status=500,
        )


async def handle_config_models_update(request: web.Request) -> web.Response:
    """PATCH /api/v1/config/models - Update model routing configuration at runtime.

    Body:
        {
            "default_profile": "local",  // optional
            "routing": {                  // optional
                "tool_calling": "qwen2.5:7b",
                "code": "qwen2.5-coder:7b"
            }
        }

    Note: Changes are runtime-only. To persist, update albus.yaml.
    """
    request_id = get_request_id(request)

    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"success": False, "error": "Invalid JSON", "request_id": request_id},
            status=400,
        )

    try:
        from stdlib.llm.capability_routing import (
            set_runtime_model_config,
            get_runtime_model_config,
            BATTERY_PACKS,
        )

        default_profile = data.get("default_profile")
        routing = data.get("routing")

        # Validate profile if provided
        if default_profile and default_profile not in BATTERY_PACKS:
            return web.json_response(
                {
                    "success": False,
                    "error": f"Invalid profile: {default_profile}. Available: {list(BATTERY_PACKS.keys())}",
                    "request_id": request_id,
                },
                status=400,
            )

        # Apply changes
        set_runtime_model_config(
            default_profile=default_profile,
            routing=routing,
        )

        return web.json_response(
            {
                "success": True,
                "message": "Model routing updated (runtime only, restart to reset)",
                "config": get_runtime_model_config(),
                "request_id": request_id,
            }
        )
    except Exception as e:
        return web.json_response(
            {
                "success": False,
                "error": str(e),
                "request_id": request_id,
            },
            status=500,
        )


async def handle_help(request: web.Request) -> web.Response:
    """GET /api/v1/help - Comprehensive API help."""
    # Count tools by category
    categories: dict[str, int] = {}
    for name in TOOL_HANDLERS.keys():
        cat = name.split(".")[0]
        categories[cat] = categories.get(cat, 0) + 1

    return web.json_response(
        {
            "name": "AlbusOS",
            "version": "1.0",
            "api_version": "v1",
            "description": "A runtime for AI agents. Build pathways, wire tools, run agents.",
            "base_url": "/api/v1",
            "quick_start": {
                "1_health": "curl http://localhost:8080/api/v1/health",
                "2_list_tools": "curl http://localhost:8080/api/v1/tools",
                "3_create_pathway": 'curl -X POST http://localhost:8080/api/v1/pathways -H "Content-Type: application/json" -d \'{"name": "Add", "nodes": [{"id": "x", "type": "transform", "config": {"expr": "a + b"}}]}\'',
                "4_run_pathway": 'curl -X POST http://localhost:8080/api/v1/pathways/{id}/run -d \'{"inputs": {"a": 1, "b": 2}}\'',
            },
            "endpoints": {
                "GET /api/v1": "API overview",
                "GET /api/v1/health": "Health check with dependency status",
                "GET /api/v1/config/validate": "Validate configuration",
                "GET /api/v1/help": "This help page",
                "GET /api/v1/openapi.json": "OpenAPI 3.0 specification",
                "GET /api/v1/docs": "Interactive API docs (Swagger UI)",
                "GET /api/v1/tools": "List tools (?category=X, ?format=grouped)",
                "POST /api/v1/tools/{name}": "Execute tool",
                "GET /api/v1/node-types": "List node types for pathway creation",
                "GET /api/v1/agents": "List all agents",
                "GET /api/v1/agents/{id}": "Get agent details (includes skills)",
                "GET /api/v1/agents/{id}/skills": "List all skills for an agent",
                "POST /api/v1/agents": "Create new agent",
                "POST /api/v1/agents/{id}/turn": "Execute agent turn",
                "DELETE /api/v1/agents/{id}": "Delete agent",
                "GET /api/v1/pathways": "List all pathways",
                "POST /api/v1/pathways": "Create a pathway",
                "GET /api/v1/pathways/{id}": "Get pathway details",
                "POST /api/v1/pathways/{id}/run": "Run pathway",
                "GET /api/v1/pathways/{id}/export": "Export pathway as JSON",
                "POST /api/v1/pathways/import": "Import pathway from JSON",
                "GET /api/v1/pathways/{id}/graph": "Get pathway graph data",
                "GET /api/v1/threads": "List threads",
                "GET /api/v1/threads/{id}": "Get thread",
                "DELETE /api/v1/threads/{id}": "Delete thread",
                "GET /api/v1/ws": "WebSocket (events/rpc)",
                "POST /api/v1/webhooks/{topic}": "Publish webhook event",
            },
            "tools": {
                "total": len(TOOL_HANDLERS),
                "categories": categories,
            },
        }
    )


async def handle_node_types(request: web.Request) -> web.Response:
    """GET /api/v1/node-types - List all node types for pathway creation.

    Query params:
        category: Filter by category (compute, control, memory, composition, streaming, agent)
        type: Get single node type detail
        format: "full" for JSON schemas, "simple" for basic info (default: simple)
    """
    from pathway_engine.domain.nodes.registry import NodeTypeRegistry

    # Check for single type request
    single_type = request.query.get("type")
    if single_type:
        spec = NodeTypeRegistry.get(single_type)
        if spec is None:
            return web.json_response(
                {
                    "error": f"Unknown node type: {single_type}",
                    "available_types": [s.type for s in NodeTypeRegistry.list_all()],
                },
                status=404,
            )
        return web.json_response(spec.to_dict())

    # Filter by category if requested
    category = request.query.get("category")
    if category:
        specs = NodeTypeRegistry.by_category(category)
    else:
        specs = NodeTypeRegistry.list_all()

    # Format: full or simple
    format_type = request.query.get("format", "simple")

    if format_type == "full":
        # Full format with JSON schemas
        node_types = [spec.to_dict() for spec in specs]
    else:
        # Simple format for quick reference
        node_types = [
            {
                "type": spec.type,
                "name": spec.name,
                "description": spec.description,
                "category": spec.category,
                "example": spec.examples[0].config if spec.examples else None,
            }
            for spec in specs
        ]

    return web.json_response(
        {
            "node_types": node_types,
            "count": len(node_types),
            "categories": NodeTypeRegistry.categories(),
            "connection_format": {
                "from_node": "Source node ID",
                "to_node": "Target node ID",
                "from_output": "Output port name (default: 'output')",
                "to_input": "Input port name (default: 'input')",
            },
            "example_pathway": {
                "name": "Calculator",
                "nodes": [
                    {"id": "double", "type": "transform", "config": {"expr": "x * 2"}},
                    {
                        "id": "add_ten",
                        "type": "transform",
                        "config": {"expr": "double + 10"},
                    },
                ],
                "connections": [
                    {"from_node": "double", "to_node": "add_ten"},
                ],
            },
        }
    )


__all__ = [
    "handle_root",
    "handle_health",
    "handle_config_validate",
    "handle_help",
    "handle_node_types",
]
