"""Pack endpoints (availability + deployment).

Packs are a library of business logic bundles. They are NOT auto-deployed by default.
Deployment is explicit, and includes wiring triggers via TriggerManager.
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime, parse_json_body
from packs.registry import list_available_packs, resolve_pack_ids


def _get_extras(runtime: Any) -> dict:
    """Get VM context extras (where we store trigger_manager, deployment_config, etc.)."""
    vm = getattr(runtime, "pathway_vm", None)
    ctx = getattr(vm, "ctx", None)
    return getattr(ctx, "extras", {}) if ctx is not None else {}


def _get_trigger_manager(runtime: Any):
    return _get_extras(runtime).get("trigger_manager")


def _get_deployment_config(runtime: Any):
    return _get_extras(runtime).get("deployment_config")


async def handle_list_available_packs(request: web.Request) -> web.Response:
    """GET /api/v1/packs - List packs available in this server build.

    Each pack includes a 'deployed' boolean indicating if it's currently active.
    """
    runtime = get_runtime(request)

    # "Deployed" should reflect runtime state (PathwayService metadata),
    # not just what the config *wants* deployed.
    deployed_ids: set[str] = set()
    try:
        metas = runtime.pathway_service.list(source_filter="pack:")
        for m in metas:
            src = getattr(m, "source", "") or ""
            if isinstance(src, str) and src.startswith("pack:"):
                deployed_ids.add(src.split("pack:", 1)[1])
    except Exception:
        deployed_ids = set()

    packs = list_available_packs()
    packs_data = []
    for p in packs:
        d = p.to_dict()
        d["deployed"] = p.id in deployed_ids
        packs_data.append(d)

    return web.json_response(
        {
            "success": True,
            "packs": packs_data,
        }
    )


async def handle_list_deployed_packs(request: web.Request) -> web.Response:
    """GET /api/v1/packs/deployed - List deployed pack pathways."""
    runtime = get_runtime(request)
    service = runtime.pathway_service
    metas = service.list(source_filter="pack:")
    return web.json_response(
        {
            "success": True,
            "pathways": [m.to_dict() for m in metas],
        }
    )


async def handle_deploy_packs(request: web.Request) -> web.Response:
    """POST /api/v1/packs/deploy - Deploy one or more packs into the runtime.

    Body:
      { "pack_ids": ["<pack_id>", "..."], "force": false }

    Discover available pack IDs via:
      GET /api/v1/packs
    """
    runtime = get_runtime(request)
    body = await parse_json_body(request) or {}
    pack_ids = body.get("pack_ids")
    force = bool(body.get("force", False))
    if isinstance(pack_ids, str):
        pack_ids = [pack_ids]
    if not isinstance(pack_ids, list) or not all(isinstance(x, str) for x in pack_ids):
        return error_response(
            request,
            "pack_ids must be a list of strings",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )

    packs, missing = resolve_pack_ids(pack_ids)
    if missing:
        return error_response(
            request,
            "unknown pack_id(s)",
            ErrorCode.VALIDATION_ERROR,
            status=400,
            details={"missing": missing},
        )

    trigger_manager = _get_trigger_manager(runtime)
    if trigger_manager is None:
        return error_response(
            request,
            "trigger_manager_not_available",
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )

    deployed: list[dict[str, Any]] = []
    deployed_packs: list[str] = []
    skipped_packs: list[str] = []

    # Detect currently deployed packs (runtime state)
    already_deployed: set[str] = set()
    try:
        metas = runtime.pathway_service.list(source_filter="pack:")
        for m in metas:
            src = getattr(m, "source", "") or ""
            if isinstance(src, str) and src.startswith("pack:"):
                already_deployed.add(src.split("pack:", 1)[1])
    except Exception:
        already_deployed = set()

    for p in packs:
        # Ensure triggers are wired even if pathways are already deployed.
        await trigger_manager.setup_pack(p)

        if (p.id in already_deployed) and not force:
            skipped_packs.append(p.id)
            continue

        metas = runtime.pathway_service.deploy_pack(p)
        deployed_packs.append(p.id)
        deployed.extend([m.to_dict() for m in metas])

    return web.json_response(
        {
            "success": True,
            "deployed_packs": deployed_packs,
            "skipped_packs": skipped_packs,
            "deployed_pathways": deployed,
            # Return a safe summary (no asyncio.Task objects)
            "trigger_subscriptions": trigger_manager.list_subscriptions(),
        }
    )


async def handle_get_deployment_config(request: web.Request) -> web.Response:
    """GET /api/v1/packs/config - Get the effective deployment configuration.

    Returns the deployment config after env var substitution + defaults,
    including 'source' field showing where it was loaded from (file path or "none").
    """
    runtime = get_runtime(request)
    deploy_config = _get_deployment_config(runtime)

    if deploy_config is None:
        return web.json_response(
            {
                "success": True,
                "config": {
                    "source": "none",
                    "packs": [],
                    "mcp_servers": [],
                    "bindings": [],
                },
            }
        )

    return web.json_response(
        {
            "success": True,
            "config": deploy_config.to_dict(),
        }
    )


__all__ = [
    "handle_list_available_packs",
    "handle_list_deployed_packs",
    "handle_deploy_packs",
    "handle_get_deployment_config",
]
