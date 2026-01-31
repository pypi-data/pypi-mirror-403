"""Pathway Tools - Create, run, and manage pathways.

Tools receive dependencies via ToolContext.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


def _require_domain(ctx: ToolContext) -> Any:
    domain = getattr(ctx, "domain", None) if ctx is not None else None
    if domain is None:
        raise RuntimeError("pathway_tools_require_domain")
    return domain


def _ensure_workspace_id(ctx: ToolContext, *, domain: Any) -> str:
    wsid = getattr(ctx, "workspace_id", None)
    if isinstance(wsid, str) and wsid.strip():
        return wsid.strip()
    ws = domain.create_workspace(name=f"Workspace for {ctx.thread_id or 'pathways'}")
    wsid = getattr(ws, "id", None) or getattr(ws, "workspace_id", None)
    if not isinstance(wsid, str) or not wsid.strip():
        raise RuntimeError("failed_to_create_workspace")
    ctx.workspace_id = wsid.strip()
    return wsid.strip()


def _node_from_dict(node_dict: dict[str, Any]) -> Any:
    from pathway_engine.domain.nodes import (
        LLMNode,
        ToolNode,
        CodeNode,
        TransformNode,
        RouterNode,
        GateNode,
        MemoryReadNode,
        MemoryWriteNode,
        MapNode,
        ConditionalNode,
        RouteNode,
        RetryNode,
        TimeoutNode,
        FallbackNode,
        ToolCallingLLMNode,
        ToolExecutorNode,
        AgentLoopNode,
        EventSourceNode,
        IntrospectionNode,
    )

    node_type = (node_dict.get("type") or "transform").strip()
    node_id = (node_dict.get("id") or f"node_{uuid.uuid4().hex[:6]}").strip()

    TYPE_MAP: dict[str, Any] = {
        "llm": LLMNode,
        "tool": ToolNode,
        "code": CodeNode,
        "transform": TransformNode,
        "router": RouterNode,
        "gate": GateNode,
        "memory_read": MemoryReadNode,
        "memory_write": MemoryWriteNode,
        # composition
        "subpathway": lambda **kwargs: kwargs,  # not supported in doc compiler
        "map": MapNode,
        "when": ConditionalNode,
        "conditional": ConditionalNode,
        "route": RouteNode,
        "retry": RetryNode,
        "timeout": TimeoutNode,
        "fallback": FallbackNode,
        # tool calling
        "tool_calling_llm": ToolCallingLLMNode,
        "tool_executor": ToolExecutorNode,
        # agent loop
        "agent_loop": AgentLoopNode,
        # streaming / observation
        "event_source": EventSourceNode,
        "introspection": IntrospectionNode,
    }

    node_class = TYPE_MAP.get(node_type, TransformNode)

    # Common metadata
    kwargs: dict[str, Any] = {"id": node_id}
    if node_dict.get("name"):
        kwargs["name"] = node_dict["name"]
    if node_dict.get("description"):
        kwargs["description"] = node_dict["description"]

    config = (
        node_dict.get("config", {}) if isinstance(node_dict.get("config"), dict) else {}
    )

    if node_type == "llm":
        kwargs["prompt"] = config.get("prompt", "")
        kwargs["model"] = config.get("model", "auto")  # "auto" uses capability routing
        kwargs["temperature"] = config.get("temperature", 0.7)
        if config.get("max_tokens") is not None:
            kwargs["max_tokens"] = config.get("max_tokens")
        if config.get("system") is not None:
            kwargs["system"] = config.get("system")
        if config.get("response_format") is not None:
            kwargs["response_format"] = config.get("response_format")
        if config.get("json_schema") is not None:
            kwargs["json_schema"] = config.get("json_schema")

    elif node_type == "tool":
        kwargs["tool"] = config.get("tool_name", config.get("tool", ""))
        kwargs["args"] = config.get("args", {})

    elif node_type == "code":
        kwargs["code"] = config.get("code", "")
        if config.get("language") is not None:
            kwargs["language"] = config.get("language")

    elif node_type == "transform":
        kwargs["expr"] = config.get("expr", config.get("expression", "input"))

    elif node_type == "router":
        kwargs["condition"] = config.get("condition", "true")
        kwargs["routes"] = config.get("routes", {})
        kwargs["default"] = config.get("default")

    elif node_type == "memory_read":
        kwargs["query"] = config.get("query")
        kwargs["key"] = config.get("key")
        kwargs["namespace"] = config.get("namespace", "default")

    elif node_type == "memory_write":
        kwargs["key"] = config.get("key", "")
        kwargs["value_expr"] = config.get("value_expr", "{{input}}")
        kwargs["namespace"] = config.get("namespace", "default")

    # Instantiate node class
    return node_class(**kwargs)


def _pathway_from_dict(data: dict[str, Any]) -> Any:
    from pathway_engine.domain.pathway import Pathway, Connection

    nodes_data = data.get("nodes", []) if isinstance(data.get("nodes"), list) else []
    connections_data = (
        data.get("connections", []) if isinstance(data.get("connections"), list) else []
    )

    nodes: dict[str, Any] = {}
    for n in nodes_data:
        if isinstance(n, dict):
            node = _node_from_dict(n)
            nodes[str(node.id)] = node

    connections: list[Connection] = []
    for c in connections_data:
        if isinstance(c, str):
            if "→" in c:
                parts = c.split("→")
            elif "->" in c:
                parts = c.split("->")
            else:
                continue
            if len(parts) == 2:
                connections.append(
                    Connection(from_node=parts[0].strip(), to_node=parts[1].strip())
                )
        elif isinstance(c, dict):
            connections.append(
                Connection(
                    from_node=str(c.get("from", c.get("from_node", ""))),
                    to_node=str(c.get("to", c.get("to_node", ""))),
                    from_output=str(c.get("from_output", "output")),
                    to_input=str(c.get("to_input", "input")),
                )
            )

    return Pathway(
        id=str(data.get("id") or f"pathway_{uuid.uuid4().hex[:8]}"),
        name=data.get("name"),
        description=data.get("description"),
        nodes=nodes,
        connections=connections,
        metadata=(
            data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
        ),
    )


def _load_doc_content(*, domain: Any, doc_id: str) -> dict[str, Any]:
    head = domain.get_head_content(doc_id=doc_id)
    if not isinstance(head, dict):
        raise RuntimeError("invalid_pathway_document_content")
    return head


@register_tool("pathway.create")
async def create_pathway(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Create a new pathway.

    Inputs:
        name: Pathway name
        description: What the pathway does
        nodes: List of node definitions (id, type, config, name, description)
        connections: List of connections ("a → b" or {"from": "a", "to": "b"})

    Returns:
        pathway_id: Runtime pathway ID
        doc_id: Stored document ID (if persisted)
        success: Whether creation succeeded
    """
    name = str(inputs.get("name", "")).strip() or "Untitled Pathway"
    description = str(inputs.get("description", "")).strip()
    nodes_raw = inputs.get("nodes", [])
    connections_raw = inputs.get("connections", [])

    if context is None:
        return {"success": False, "error": "missing_tool_context"}

    try:
        domain = _require_domain(context)

        # Ensure a workspace exists (tests and tools expect idempotent auto-workspace).
        workspace_id = _ensure_workspace_id(context, domain=domain)

        pathway_id = (
            str(inputs.get("pathway_id") or "").strip()
            or f"pathway_{uuid.uuid4().hex[:8]}"
        )

        # Fast structural validation (agents often try to create "loops" by wiring back upstream).
        try:
            from pathway_engine.application.validation import find_cycle

            tmp = _pathway_from_dict(
                {
                    "id": pathway_id,
                    "name": name,
                    "description": description,
                    "nodes": nodes_raw,
                    "connections": connections_raw,
                    "metadata": dict(inputs.get("metadata") or {}),
                }
            )
            cycle = find_cycle(tmp)
            if cycle:
                return {
                    "success": False,
                    "error": "pathway_contains_cycles",
                    "cycle": cycle,
                    "message": f"Pathway contains cycles: {' -> '.join(cycle)}",
                }
        except Exception:
            pass

        # Persist as a Studio document (domain-owned).
        # This keeps stdlib runtime-neutral (no Albus PathwayService dependency).
        doc = domain.create_document(
            doc_type="pathway",
            name=name,
            workspace_id=str(workspace_id),
            metadata={
                "pathway_id": pathway_id,
                "source": (
                    f"user:thread:{context.thread_id}"
                    if context.thread_id
                    else "user:tool"
                ),
            },
        )
        doc_id = getattr(doc, "id", None)
        if not isinstance(doc_id, str) or not doc_id.startswith("doc_"):
            raise RuntimeError("failed_to_create_document")

        # Store content as head revision.
        domain.save_revision(
            doc_id=doc_id,
            content={
                "id": pathway_id,
                "name": name,
                "description": description,
                "nodes": nodes_raw,
                "connections": connections_raw,
                "metadata": dict(inputs.get("metadata") or {}),
            },
        )

        return {
            "success": True,
            "pathway_id": pathway_id,
            "doc_id": doc_id,
            "id": doc_id,  # canonical identifier in Studio/hosted environments
            "node_count": len(nodes_raw) if isinstance(nodes_raw, list) else 0,
            "workspace_id": str(workspace_id),
        }

    except Exception as e:
        logger.error("Failed to create pathway: %s", e)
        return {"success": False, "error": str(e)}


@register_tool("pathway.run")
async def run_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Run a pathway with given inputs.

    Inputs:
        pathway_id: Pathway ID (canonical ID or doc_id)
        inputs: Input data for the pathway

    Returns:
        success: Whether execution succeeded
        outputs: Pathway outputs
        execution_id: Execution ID
    """
    pathway_id = str(inputs.get("pathway_id") or inputs.get("doc_id") or "").strip()
    pathway_inputs = inputs.get("inputs", {})

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}
        domain = _require_domain(context)

        # Canonical: doc_id. (If non-doc id is provided, we don't attempt global search.)
        if not pathway_id.startswith("doc_"):
            return {"success": False, "error": "pathway_id_must_be_doc_id"}

        content = _load_doc_content(domain=domain, doc_id=pathway_id)
        pathway = _pathway_from_dict(content)

        executor = context.pathway_executor
        if executor is None:
            return {"success": False, "error": "no_pathway_executor_available"}

        # Pre-validate using executor context (better errors than VM topological sort)
        try:
            from pathway_engine.application.validation import validate_pathway

            engine_ctx = getattr(executor, "ctx", None)
            if engine_ctx is not None:
                validation = validate_pathway(pathway, engine_ctx)
                if not validation.valid:
                    return {
                        "success": False,
                        "error": "pathway_invalid",
                        "validation": validation.to_dict(),
                    }
        except Exception:
            pass

        record = await executor.execute(pathway, pathway_inputs)
        return {
            "success": record.success,
            "outputs": record.outputs,
            "execution_id": record.id,
            "status": record.status.value,
            "error": record.error,
        }

    except Exception as e:
        logger.error("Failed to run pathway %s: %s", pathway_id, e)
        return {"success": False, "error": str(e)}


@register_tool("pathway.list")
async def list_pathways(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """List available pathways.

    Inputs:
        include_pack: Include pack pathways (default: true)
        include_user: Include user pathways (default: true)
        source_filter: Filter by source prefix (optional)

    Returns:
        pathways: List of pathway summaries
        count: Total count
    """
    try:
        if context is None:
            return {"pathways": [], "count": 0}
        domain = _require_domain(context)

        # Limit scope to a workspace (required for deterministic listing).
        wsid = getattr(context, "workspace_id", None)
        if not isinstance(wsid, str) or not wsid.strip():
            return {"pathways": [], "count": 0}

        tree = domain.get_tree(workspace_id=wsid)
        payload = tree.model_dump() if hasattr(tree, "model_dump") else tree
        children = (payload or {}).get("tree") or {}

        out: list[dict[str, Any]] = []

        def _walk(node: dict[str, Any]) -> None:
            docs = node.get("documents") or []
            for d in docs:
                if isinstance(d, dict) and d.get("doc_type") == "pathway":
                    out.append(d)
            folders = node.get("folders") or []
            for f in folders:
                if isinstance(f, dict):
                    _walk(f.get("children") or {})

        if isinstance(children, dict):
            _walk(children)

        return {"pathways": out, "count": len(out)}

    except Exception as e:
        logger.error("Failed to list pathways: %s", e)
        return {"pathways": [], "error": str(e)}


@register_tool("pathway.get")
async def get_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Get details of a pathway.

    Inputs:
        pathway_id: Pathway ID (canonical ID or doc_id)

    Returns:
        pathway: Pathway details
        meta: Pathway metadata
    """
    pathway_id = str(inputs.get("pathway_id") or inputs.get("doc_id") or "").strip()

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}
        domain = _require_domain(context)
        if not pathway_id.startswith("doc_"):
            return {"success": False, "error": "pathway_id_must_be_doc_id"}
        doc = domain.get_document(doc_id=pathway_id)
        head = _load_doc_content(domain=domain, doc_id=pathway_id)
        return {
            "success": True,
            "doc": doc.model_dump() if hasattr(doc, "model_dump") else doc,
            "content": head,
        }

    except Exception as e:
        logger.error("Failed to get pathway %s: %s", pathway_id, e)
        return {"success": False, "error": str(e)}


@register_tool("pathway.export")
async def export_pathway(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Export a pathway as a portable JSON document.

    Inputs:
        pathway_id: Pathway ID to export

    Returns:
        format: Export format identifier
        pathway: Pathway data
        meta: Pathway metadata
    """
    pathway_id = str(inputs.get("pathway_id") or "").strip()

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}
        domain = _require_domain(context)
        if not pathway_id.startswith("doc_"):
            return {"success": False, "error": "pathway_id_must_be_doc_id"}
        doc = domain.get_document(doc_id=pathway_id)
        head = _load_doc_content(domain=domain, doc_id=pathway_id)
        return {
            "success": True,
            "format": "albus.pathway.v1",
            "doc": doc.model_dump() if hasattr(doc, "model_dump") else doc,
            "pathway": head,
        }

    except Exception as e:
        logger.error("Failed to export pathway %s: %s", pathway_id, e)
        return {"success": False, "error": str(e)}


@register_tool("pathway.import")
async def import_pathway(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Import a pathway from an export.

    Inputs:
        data: Export data (from pathway.export)
        new_id: Optional new ID for the imported pathway

    Returns:
        pathway: Imported pathway metadata
    """
    data = inputs.get("data", {})
    new_id = inputs.get("new_id")
    workspace_id = context.workspace_id if context else None

    if not data:
        return {"success": False, "error": "data is required"}

    if data.get("format") != "albus.pathway.v1":
        return {"success": False, "error": f"Unsupported format: {data.get('format')}"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}
        domain = _require_domain(context)
        wsid = _ensure_workspace_id(context, domain=domain)

        pathway_data = data.get("pathway") or data.get("content") or {}
        if not isinstance(pathway_data, dict):
            return {"success": False, "error": "invalid_import_payload"}

        # Apply optional ID override
        if new_id:
            pathway_data = dict(pathway_data)
            pathway_data["id"] = str(new_id)

        # Persist
        name = str(pathway_data.get("name") or "Imported Pathway").strip()
        doc = domain.create_document(
            doc_type="pathway",
            name=name,
            workspace_id=str(wsid),
            metadata={"source": "import:tool"},
        )
        doc_id = getattr(doc, "id", None)
        if not isinstance(doc_id, str) or not doc_id.startswith("doc_"):
            raise RuntimeError("failed_to_create_document")
        domain.save_revision(doc_id=doc_id, content=pathway_data)

        return {
            "success": True,
            "doc_id": doc_id,
            "id": doc_id,
            "workspace_id": str(wsid),
        }

    except Exception as e:
        logger.error("Failed to import pathway: %s", e)
        return {"success": False, "error": str(e)}


__all__ = [
    "create_pathway",
    "run_pathway",
    "list_pathways",
    "get_pathway",
    "export_pathway",
    "import_pathway",
]
