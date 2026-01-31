"""Pathway Tools - Create, run, and manage pathways.

Tools receive dependencies via ToolContext.

DSL Tools (for agents to build pathways step-by-step):
    pathway.new      - Create empty pathway
    pathway.add_node - Add a node
    pathway.connect  - Connect two nodes  
    pathway.update_node - Update node config
    pathway.remove_node - Remove a node
    pathway.save     - Persist to storage
    pathway.run      - Execute pathway

Legacy/Batch Tools:
    pathway.create   - Create from JSON or natural language
    pathway.get      - Get pathway details
    pathway.list     - List pathways
    pathway.export   - Export pathway
    pathway.import   - Import pathway
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)

# =============================================================================
# IN-MEMORY WORKING PATHWAYS (for DSL-style editing)
# =============================================================================
# Key: pathway_id, Value: Pathway object being edited
_WORKING_PATHWAYS: dict[str, Any] = {}


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
        # Sandbox configuration (matches CodeNode + code.execute)
        if config.get("profile") is not None:
            kwargs["profile"] = config.get("profile")
        if config.get("allow_site_packages") is not None:
            kwargs["allow_site_packages"] = bool(config.get("allow_site_packages"))
        if config.get("timeout_ms") is not None:
            kwargs["timeout_ms"] = int(config.get("timeout_ms"))
        if config.get("memory_mb") is not None:
            kwargs["memory_mb"] = int(config.get("memory_mb"))

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


# =============================================================================
# DSL TOOLS (Fluent API for Agents)
# =============================================================================

@register_tool(
    "pathway.new",
    description="""Create a new empty pathway for editing.

Returns a pathway_id you can use with pathway.add_node, pathway.connect, etc.
The pathway stays in memory until you pathway.save or pathway.run it.

Example:
    result = pathway.new({"name": "My Research Pipeline"})
    # result.pathway_id = "pathway_abc123"
""",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Pathway name"},
            "description": {"type": "string", "description": "What the pathway does"},
        },
    },
)
async def new_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Create a new empty pathway in the working registry."""
    from pathway_engine.domain.pathway import Pathway
    
    name = str(inputs.get("name", "")).strip() or "Untitled Pathway"
    description = str(inputs.get("description", "")).strip()
    pathway_id = f"pathway_{uuid.uuid4().hex[:8]}"
    
    pathway = Pathway(
        id=pathway_id,
        name=name,
        description=description,
    )
    
    _WORKING_PATHWAYS[pathway_id] = pathway
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "name": name,
        "description": description,
        "message": f"Created pathway '{name}'. Use pathway.add_node to add nodes.",
    }


@register_tool(
    "pathway.add_node",
    description="""Add a node to a pathway.

Node types:
- llm: Text generation (config: prompt, system, model, temperature)
- tool: Call a tool (config: tool_name, args)
- code: Run Python (config: code, language)
- transform: Data transform (config: expr)
- agent_loop: Autonomous agent (config: goal, tools, max_steps)

Example:
    pathway.add_node({
        "pathway_id": "pathway_abc123",
        "node_id": "search",
        "type": "tool",
        "config": {"tool_name": "web.search", "args": {"query": "{{input}}"}}
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to modify"},
            "node_id": {"type": "string", "description": "Unique ID for the node"},
            "type": {
                "type": "string",
                "enum": ["llm", "tool", "code", "transform", "router", "agent_loop"],
                "description": "Node type",
            },
            "config": {"type": "object", "description": "Node configuration"},
            "name": {"type": "string", "description": "Human-readable name"},
        },
        "required": ["pathway_id", "node_id", "type"],
    },
)
async def add_node(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Add a node to a working pathway."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    node_id = str(inputs.get("node_id", "")).strip()
    node_type = str(inputs.get("type", "")).strip()
    config = inputs.get("config", {})
    node_name = inputs.get("name")
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}. Use pathway.new first."}
    
    if not node_id:
        return {"success": False, "error": "node_id is required"}
    
    if not node_type:
        return {"success": False, "error": "type is required"}
    
    pathway = _WORKING_PATHWAYS[pathway_id]
    
    # Check for duplicate
    if node_id in pathway.nodes:
        return {"success": False, "error": f"Node '{node_id}' already exists. Use pathway.update_node to modify."}
    
    # Build node
    node_dict = {"id": node_id, "type": node_type, "config": config}
    if node_name:
        node_dict["name"] = node_name
    
    try:
        node = _node_from_dict(node_dict)
        pathway.add_node(node)
    except Exception as e:
        return {"success": False, "error": f"Failed to create node: {e}"}
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "node_id": node_id,
        "node_count": len(pathway.nodes),
        "nodes": list(pathway.nodes.keys()),
    }


@register_tool(
    "pathway.connect",
    description="""Connect two nodes in a pathway.

Example:
    pathway.connect({
        "pathway_id": "pathway_abc123",
        "from": "search",
        "to": "summarize"
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to modify"},
            "from": {"type": "string", "description": "Source node ID"},
            "to": {"type": "string", "description": "Target node ID"},
        },
        "required": ["pathway_id", "from", "to"],
    },
)
async def connect_nodes(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Connect two nodes in a working pathway."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    from_node = str(inputs.get("from", "")).strip()
    to_node = str(inputs.get("to", "")).strip()
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}"}
    
    if not from_node or not to_node:
        return {"success": False, "error": "'from' and 'to' are required"}
    
    pathway = _WORKING_PATHWAYS[pathway_id]
    
    # Validate nodes exist
    if from_node not in pathway.nodes:
        return {"success": False, "error": f"Node '{from_node}' not found"}
    if to_node not in pathway.nodes:
        return {"success": False, "error": f"Node '{to_node}' not found"}
    
    pathway.connect(from_node, to_node)
    
    # Check for cycles
    try:
        from pathway_engine.application.validation import find_cycle
        cycle = find_cycle(pathway)
        if cycle:
            # Remove the connection we just added
            pathway.connections = [c for c in pathway.connections 
                                   if not (c.from_node == from_node and c.to_node == to_node)]
            return {
                "success": False,
                "error": f"Connection would create cycle: {' -> '.join(cycle)}",
            }
    except Exception:
        pass
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "connection": f"{from_node} → {to_node}",
        "connection_count": len(pathway.connections),
    }


@register_tool(
    "pathway.update_node",
    description="""Update a node's configuration.

Example:
    pathway.update_node({
        "pathway_id": "pathway_abc123",
        "node_id": "llm",
        "config": {"temperature": 0.9}
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to modify"},
            "node_id": {"type": "string", "description": "Node to update"},
            "config": {"type": "object", "description": "Config values to update (merged with existing)"},
        },
        "required": ["pathway_id", "node_id", "config"],
    },
)
async def update_node(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Update a node's configuration in a working pathway."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    node_id = str(inputs.get("node_id", "")).strip()
    new_config = inputs.get("config", {})
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}"}
    
    if not node_id:
        return {"success": False, "error": "node_id is required"}
    
    pathway = _WORKING_PATHWAYS[pathway_id]
    
    if node_id not in pathway.nodes:
        return {"success": False, "error": f"Node '{node_id}' not found"}
    
    node = pathway.nodes[node_id]
    
    # Update node attributes from config
    for key, value in new_config.items():
        if hasattr(node, key):
            setattr(node, key, value)
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "node_id": node_id,
        "updated": list(new_config.keys()),
    }


@register_tool(
    "pathway.remove_node",
    description="""Remove a node from a pathway (also removes its connections).

Example:
    pathway.remove_node({
        "pathway_id": "pathway_abc123",
        "node_id": "old_node"
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to modify"},
            "node_id": {"type": "string", "description": "Node to remove"},
        },
        "required": ["pathway_id", "node_id"],
    },
)
async def remove_node(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Remove a node from a working pathway."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    node_id = str(inputs.get("node_id", "")).strip()
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}"}
    
    if not node_id:
        return {"success": False, "error": "node_id is required"}
    
    pathway = _WORKING_PATHWAYS[pathway_id]
    
    if node_id not in pathway.nodes:
        return {"success": False, "error": f"Node '{node_id}' not found"}
    
    # Remove node
    del pathway.nodes[node_id]
    
    # Remove connections involving this node
    pathway.connections = [
        c for c in pathway.connections
        if c.from_node != node_id and c.to_node != node_id
    ]
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "removed": node_id,
        "node_count": len(pathway.nodes),
        "nodes": list(pathway.nodes.keys()),
    }


@register_tool(
    "pathway.show",
    description="""Show the current state of a working pathway.

Example:
    pathway.show({"pathway_id": "pathway_abc123"})
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to show"},
        },
        "required": ["pathway_id"],
    },
)
async def show_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Show the current state of a working pathway."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}"}
    
    pathway = _WORKING_PATHWAYS[pathway_id]
    
    nodes_info = []
    for nid, node in pathway.nodes.items():
        node_info = {
            "id": nid,
            "type": getattr(node, "type", "unknown"),
        }
        # Add key config fields
        if hasattr(node, "prompt"):
            node_info["prompt"] = str(node.prompt)[:100]
        if hasattr(node, "tool"):
            node_info["tool"] = node.tool
        if hasattr(node, "goal"):
            node_info["goal"] = str(node.goal)[:100]
        nodes_info.append(node_info)
    
    connections_info = [f"{c.from_node} → {c.to_node}" for c in pathway.connections]
    
    return {
        "success": True,
        "pathway_id": pathway_id,
        "name": pathway.name,
        "description": pathway.description,
        "nodes": nodes_info,
        "connections": connections_info,
        "node_count": len(pathway.nodes),
    }


@register_tool(
    "pathway.save",
    description="""Persist a working pathway to storage.

Example:
    pathway.save({"pathway_id": "pathway_abc123"})
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to save"},
        },
        "required": ["pathway_id"],
    },
)
async def save_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Persist a working pathway to document storage."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    
    if not pathway_id or pathway_id not in _WORKING_PATHWAYS:
        return {"success": False, "error": f"Pathway not found: {pathway_id}"}
    
    if context is None:
        return {"success": False, "error": "missing_tool_context"}
    
    try:
        domain = _require_domain(context)
        workspace_id = _ensure_workspace_id(context, domain=domain)
        
        pathway = _WORKING_PATHWAYS[pathway_id]
        
        # Serialize nodes back to dict format
        nodes_raw = []
        for nid, node in pathway.nodes.items():
            node_dict = {"id": nid, "type": getattr(node, "type", "transform")}
            # Serialize node config based on type
            if hasattr(node, "prompt"):
                node_dict["config"] = {"prompt": node.prompt}
                if hasattr(node, "system") and node.system:
                    node_dict["config"]["system"] = node.system
                if hasattr(node, "model"):
                    node_dict["config"]["model"] = node.model
                if hasattr(node, "temperature"):
                    node_dict["config"]["temperature"] = node.temperature
            elif hasattr(node, "tool"):
                node_dict["config"] = {"tool_name": node.tool, "args": getattr(node, "args", {})}
            elif hasattr(node, "code"):
                node_dict["config"] = {
                    "code": node.code,
                    "language": getattr(node, "language", "python"),
                }
                # Sandbox configuration
                if getattr(node, "profile", None) is not None:
                    node_dict["config"]["profile"] = getattr(node, "profile")
                if getattr(node, "allow_site_packages", None) is not None:
                    node_dict["config"]["allow_site_packages"] = getattr(
                        node, "allow_site_packages"
                    )
                if getattr(node, "timeout_ms", None) is not None:
                    node_dict["config"]["timeout_ms"] = getattr(node, "timeout_ms")
                if getattr(node, "memory_mb", None) is not None:
                    node_dict["config"]["memory_mb"] = getattr(node, "memory_mb")
            elif hasattr(node, "goal"):
                node_dict["config"] = {
                    "goal": node.goal,
                    "tools": getattr(node, "tools", []),
                    "max_steps": getattr(node, "max_steps", 5),
                }
            elif hasattr(node, "expr"):
                node_dict["config"] = {"expr": node.expr}
            nodes_raw.append(node_dict)
        
        connections_raw = [f"{c.from_node} → {c.to_node}" for c in pathway.connections]
        
        # Create document
        doc = domain.create_document(
            doc_type="pathway",
            name=pathway.name or "Saved Pathway",
            workspace_id=str(workspace_id),
            metadata={"pathway_id": pathway_id, "source": "pathway.save"},
        )
        doc_id = getattr(doc, "id", None)
        if not isinstance(doc_id, str) or not doc_id.startswith("doc_"):
            raise RuntimeError("failed_to_create_document")
        
        domain.save_revision(
            doc_id=doc_id,
            content={
                "id": pathway_id,
                "name": pathway.name,
                "description": pathway.description,
                "nodes": nodes_raw,
                "connections": connections_raw,
            },
        )
        
        return {
            "success": True,
            "pathway_id": pathway_id,
            "doc_id": doc_id,
            "workspace_id": str(workspace_id),
            "node_count": len(pathway.nodes),
        }
        
    except Exception as e:
        logger.error("Failed to save pathway: %s", e)
        return {"success": False, "error": str(e)}


@register_tool(
    "pathway.discard",
    description="""Discard a working pathway without saving.

Example:
    pathway.discard({"pathway_id": "pathway_abc123"})
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway to discard"},
        },
        "required": ["pathway_id"],
    },
)
async def discard_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Discard a working pathway without saving."""
    pathway_id = str(inputs.get("pathway_id", "")).strip()
    
    if pathway_id and pathway_id in _WORKING_PATHWAYS:
        del _WORKING_PATHWAYS[pathway_id]
        return {"success": True, "discarded": pathway_id}
    
    return {"success": False, "error": f"Pathway not found: {pathway_id}"}


# =============================================================================
# PATHWAY BUILDER (Natural Language → Pathway using Fluent API)
# =============================================================================

PATHWAY_ARCHITECT_SYSTEM = """You are a pathway architect for AlbusOS. Generate a pathway definition.

## Node Types (USE ONLY THESE)

1. **llm**: Text generation/reasoning (MOST COMMON)
   Config: prompt (use {{variable}}), model ("auto"), temperature (0-1)

2. **tool**: Call an external tool
   Config: tool_name ("web.search", "web.fetch", "workspace.write_file"), args (object)
   
3. **agent_loop**: Autonomous multi-step reasoning
   Config: goal (string), tools (list), max_steps (int)

## IMPORTANT RULES
- Use "llm" nodes for ANY text processing, analysis, extraction, summarization
- Use "tool" nodes ONLY for web.search, web.fetch, workspace.* operations  
- DO NOT use "transform" or "code" nodes - use "llm" instead
- Input variable is always {{topic}}, {{query}}, {{message}}, or {{input}}
- Reference previous node output as {{node_id.response}} for llm, {{node_id.results}} for tool

## Output (JSON only, no markdown):
{"name": "Name", "nodes": [{"id": "x", "type": "llm|tool", "config": {...}}], "connections": ["a → b"]}

## Examples

Search+Summarize:
{"name": "Search", "nodes": [
  {"id": "search", "type": "tool", "config": {"tool_name": "web.search", "args": {"query": "{{topic}}"}}},
  {"id": "summarize", "type": "llm", "config": {"prompt": "Summarize these results about {{topic}}:\\n{{search.results}}", "model": "auto"}}
], "connections": ["search → summarize"]}

Multi-step Analysis:
{"name": "Analyzer", "nodes": [
  {"id": "search", "type": "tool", "config": {"tool_name": "web.search", "args": {"query": "{{topic}}"}}},
  {"id": "extract", "type": "llm", "config": {"prompt": "Extract key facts from:\\n{{search.results}}", "model": "auto"}},
  {"id": "report", "type": "llm", "config": {"prompt": "Write report based on:\\n{{extract.response}}", "model": "auto"}}
], "connections": ["search → extract", "extract → report"]}
"""


def _build_pathway_fluent(spec: dict[str, Any]) -> Any:
    """Build a Pathway using the fluent API from a spec dict."""
    from pathway_engine.domain.pathway import Pathway
    
    pathway = Pathway(
        id=str(spec.get("id") or f"pathway_{uuid.uuid4().hex[:8]}"),
        name=spec.get("name"),
        description=spec.get("description"),
        trigger=spec.get("trigger"),  # Optional trigger config
    )
    
    # Add nodes using fluent API
    nodes_data = spec.get("nodes", [])
    for n in nodes_data:
        if isinstance(n, dict):
            node = _node_from_dict(n)
            pathway.add_node(node)
    
    # Add connections using fluent API
    connections_data = spec.get("connections", [])
    for c in connections_data:
        if isinstance(c, str):
            if "→" in c:
                parts = c.split("→")
            elif "->" in c:
                parts = c.split("->")
            else:
                continue
            if len(parts) == 2:
                pathway.connect(parts[0].strip(), parts[1].strip())
        elif isinstance(c, dict):
            pathway.connect(
                str(c.get("from", c.get("from_node", ""))),
                str(c.get("to", c.get("to_node", ""))),
            )
    
    return pathway


async def _generate_pathway_from_description(
    description: str,
    name: str | None = None,
) -> dict[str, Any]:
    """Use LLM to generate a pathway spec from natural language."""
    import json as json_module
    
    from stdlib.llm import get_provider
    from stdlib.llm.capability_routing import get_model_for_capability
    
    model = get_model_for_capability("json_output") or get_model_for_capability("reasoning")
    if not model:
        model = "llama3.1:8b"
    
    provider = get_provider(model)
    if provider is None:
        raise RuntimeError(f"No provider for model {model}")
    
    user_prompt = f"Create a pathway for: {description}"
    if name:
        user_prompt += f"\n\nName it: {name}"
    
    result = await provider.generate(
        prompt=user_prompt,
        system=PATHWAY_ARCHITECT_SYSTEM,
        model=model,
        temperature=0.3,
        max_tokens=2000,
        response_format="json",
    )
    
    # Handle LLMGenerateResult object
    content = result.content if hasattr(result, "content") else result.get("content", "")
    if not content:
        raise RuntimeError("LLM returned empty response")
    
    # Strip markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    spec = json_module.loads(content.strip())
    spec["_model_used"] = model
    return spec


@register_tool(
    "pathway.create",
    description="""Create a pathway - either from structured nodes OR natural language.

Mode 1 - Structured (provide nodes):
    pathway.create({
        "name": "My Pathway",
        "nodes": [{"id": "llm", "type": "llm", "config": {"prompt": "{{message}}"}}],
        "connections": []
    })

Mode 2 - Natural Language (provide description, no nodes):
    pathway.create({
        "description": "Search the web and summarize results",
        "run": true,
        "inputs": {"query": "AI news"}
    })

The second mode uses an LLM to architect the pathway for you.
""",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Pathway name"},
            "description": {"type": "string", "description": "What the pathway does (if no nodes, uses LLM to generate)"},
            "nodes": {"type": "array", "description": "Node definitions (id, type, config)"},
            "connections": {"type": "array", "description": "Connections ('a → b' or {from, to})"},
            "trigger": {
                "type": "object",
                "description": "When to auto-run this pathway. Examples: {type: 'timer', schedule: '0 9 * * *'} for daily at 9am, {type: 'webhook', topic: 'github-events'} for webhook, {type: 'event', channel: 'user-signup'} for internal events",
            },
            "run": {"type": "boolean", "description": "Run immediately after creation (default: false)"},
            "inputs": {"type": "object", "description": "Inputs to pass if running"},
        },
    },
)
async def create_pathway(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Create a pathway - structured OR natural language."""
    name = str(inputs.get("name", "")).strip()
    description = str(inputs.get("description", "")).strip()
    nodes_raw = inputs.get("nodes")
    connections_raw = inputs.get("connections", [])
    trigger_config = inputs.get("trigger")  # Optional trigger configuration
    should_run = bool(inputs.get("run", False))
    run_inputs = inputs.get("inputs", {})

    if context is None:
        return {"success": False, "error": "missing_tool_context"}

    try:
        domain = _require_domain(context)
        workspace_id = _ensure_workspace_id(context, domain=domain)

        # Mode 2: Natural language - use LLM to generate pathway spec
        model_used = None
        if not nodes_raw and description:
            try:
                spec = await _generate_pathway_from_description(description, name)
                nodes_raw = spec.get("nodes", [])
                connections_raw = spec.get("connections", [])
                name = name or spec.get("name", "Generated Pathway")
                description = spec.get("description", description)
                model_used = spec.get("_model_used")
            except Exception as e:
                return {"success": False, "error": f"LLM generation failed: {e}"}

        # Require nodes at this point
        if not nodes_raw:
            return {
                "success": False,
                "error": "Either 'nodes' (structured) or 'description' (natural language) is required",
            }

        name = name or "Untitled Pathway"
        pathway_id = str(inputs.get("pathway_id") or "").strip() or f"pathway_{uuid.uuid4().hex[:8]}"

        # Build pathway using fluent API
        pathway = _build_pathway_fluent({
            "id": pathway_id,
            "name": name,
            "description": description,
            "nodes": nodes_raw,
            "connections": connections_raw,
            "trigger": trigger_config,
        })

        # Validate for cycles
        try:
            from pathway_engine.application.validation import find_cycle
            cycle = find_cycle(pathway)
            if cycle:
                return {
                    "success": False,
                    "error": "pathway_contains_cycles",
                    "cycle": cycle,
                }
        except Exception:
            pass

        # Persist as document
        doc = domain.create_document(
            doc_type="pathway",
            name=name,
            workspace_id=str(workspace_id),
            metadata={
                "pathway_id": pathway_id,
                "source": "pathway.create" + (":llm" if model_used else ""),
            },
        )
        doc_id = getattr(doc, "id", None)
        if not isinstance(doc_id, str) or not doc_id.startswith("doc_"):
            raise RuntimeError("failed_to_create_document")

        # Store content as head revision
        content = {
            "id": pathway_id,
            "name": name,
            "description": description,
            "nodes": nodes_raw,
            "connections": connections_raw,
            "metadata": dict(inputs.get("metadata") or {}),
        }
        if trigger_config:
            content["trigger"] = trigger_config
        domain.save_revision(doc_id=doc_id, content=content)

        result: dict[str, Any] = {
            "success": True,
            "pathway_id": pathway_id,
            "doc_id": doc_id,
            "name": name,
            "description": description,
            "node_count": len(nodes_raw) if isinstance(nodes_raw, list) else 0,
            "nodes": [n.get("id") for n in nodes_raw if isinstance(n, dict)],
            "workspace_id": str(workspace_id),
        }
        
        if trigger_config:
            result["trigger"] = trigger_config
        
        if model_used:
            result["model_used"] = model_used
            result["generated"] = True

        # Optionally run the pathway
        if should_run:
            try:
                executor = context.pathway_executor
                if executor is None:
                    result["run_error"] = "no_pathway_executor_available"
                else:
                    record = await executor.execute(pathway, run_inputs)
                    result["execution"] = {
                        "success": record.success,
                        "outputs": record.outputs,
                        "execution_id": record.id,
                        "status": record.status.value,
                        "error": record.error,
                    }
            except Exception as e:
                result["run_error"] = str(e)

        return result

    except Exception as e:
        logger.error("Failed to create pathway: %s", e)
        return {"success": False, "error": str(e)}


@register_tool(
    "pathway.run",
    description="""Run a pathway with given inputs.

Works with:
- Working pathways (from pathway.new + pathway.add_node)
- Saved pathways (doc_id from pathway.save or pathway.create)

Example:
    pathway.run({
        "pathway_id": "pathway_abc123",
        "inputs": {"message": "Hello world"}
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {"type": "string", "description": "Pathway ID or doc_id"},
            "inputs": {"type": "object", "description": "Inputs to pass to the pathway"},
        },
        "required": ["pathway_id"],
    },
)
async def run_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Run a pathway with given inputs."""
    pathway_id = str(inputs.get("pathway_id") or inputs.get("doc_id") or "").strip()
    pathway_inputs = inputs.get("inputs", {})

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}
        
        pathway = None
        source = None
        
        # Check working pathways first (in-memory)
        if pathway_id in _WORKING_PATHWAYS:
            pathway = _WORKING_PATHWAYS[pathway_id]
            source = "working"
        # Then try doc_id from domain
        elif pathway_id.startswith("doc_"):
            domain = _require_domain(context)
            content = _load_doc_content(domain=domain, doc_id=pathway_id)
            pathway = _pathway_from_dict(content)
            source = "document"
        else:
            return {
                "success": False,
                "error": f"Pathway '{pathway_id}' not found. Use pathway.new to create or provide a doc_id.",
            }

        executor = context.pathway_executor
        if executor is None:
            return {"success": False, "error": "no_pathway_executor_available"}

        # Pre-validate
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
            "source": source,
            "error": record.error,
        }

    except Exception as e:
        logger.error("Failed to run pathway %s: %s", pathway_id, e)
        return {"success": False, "error": str(e)}


@register_tool(
    "pathway.invoke",
    description="""Invoke a registered pathway by ID.

Use this to invoke built-in pathways like:
- host.chat: Simple conversation (no tools)
- host.code: Coding tasks  
- host.research: Information gathering
- host.files: File operations
- host.complex: Multi-step tasks

Example:
    pathway.invoke({
        "pathway_id": "host.research",
        "inputs": {"message": "Find info about quantum computing"}
    })
""",
    parameters={
        "type": "object",
        "properties": {
            "pathway_id": {
                "type": "string",
                "description": "Registered pathway ID (e.g., 'host.chat', 'host.code')",
            },
            "inputs": {
                "type": "object",
                "description": "Inputs to pass to the pathway",
            },
        },
        "required": ["pathway_id"],
    },
)
async def invoke_pathway(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Invoke a registered pathway by ID (not doc_id).
    
    This works with pathways registered via PathwayService (like host.chat, host.code).
    For document-based pathways, use pathway.run with doc_id.
    """
    pathway_id = str(inputs.get("pathway_id") or "").strip()
    pathway_inputs = inputs.get("inputs", {})

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    try:
        if context is None:
            return {"success": False, "error": "missing_tool_context"}

        # Get pathway_service from context extras
        extras = getattr(context, "extras", None) or {}
        pathway_service = extras.get("pathway_service")
        
        # Also try to get executor
        executor = context.pathway_executor
        
        pathway = None
        
        # Try PathwayService first (for registered pathways)
        if pathway_service is not None:
            pathway = pathway_service.load(pathway_id)
        
        if pathway is None:
            return {
                "success": False,
                "error": f"Pathway not found: {pathway_id}",
                "hint": "Use pathway.list to see available pathways",
            }

        if executor is None:
            return {"success": False, "error": "no_pathway_executor_available"}

        record = await executor.execute(pathway, pathway_inputs)
        return {
            "success": record.success,
            "outputs": record.outputs,
            "pathway_id": pathway_id,
            "execution_id": record.id,
            "status": record.status.value,
            "error": record.error,
        }

    except Exception as e:
        logger.error("Failed to invoke pathway %s: %s", pathway_id, e)
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
    # DSL tools (fluent API for agents)
    "new_pathway",
    "add_node",
    "connect_nodes",
    "update_node",
    "remove_node",
    "show_pathway",
    "save_pathway",
    "discard_pathway",
    # Batch/Legacy tools
    "create_pathway",
    "run_pathway",
    "invoke_pathway",
    "list_pathways",
    "get_pathway",
    "export_pathway",
    "import_pathway",
]
