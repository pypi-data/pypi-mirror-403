"""Pathway Visualization Tools - Generate diagrams from pathways.

Supports multiple output formats:
- mermaid: Mermaid diagram syntax (for Markdown/GitHub)
- ascii: ASCII art box diagram (for terminal)
- dot: Graphviz DOT format
- d3_json: D3.js-compatible JSON

Usage:
    from stdlib.tools.viz import pathway_to_mermaid, pathway_to_ascii

    mermaid_code = pathway_to_mermaid(pathway)
    ascii_art = pathway_to_ascii(pathway)

Stdlib Tools:
    pathway.visualize - Generate diagram from pathway ID
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

if TYPE_CHECKING:
    from pathway_engine.domain.pathway import Pathway

logger = logging.getLogger(__name__)

# =============================================================================
# MERMAID FORMAT
# =============================================================================


def pathway_to_mermaid(
    pathway: "Pathway",
    *,
    direction: str = "LR",
    show_types: bool = True,
    show_prompts: bool = False,
) -> str:
    """Convert a pathway to Mermaid diagram syntax.

    Args:
        pathway: The pathway to visualize
        direction: Graph direction (LR, TB, RL, BT)
        show_types: Include node type in label
        show_prompts: Include truncated prompt in label

    Returns:
        Mermaid diagram code
    """
    lines = [f"graph {direction}"]

    # Style definitions
    lines.append("    %% Node styles")
    lines.append("    classDef llm fill:#e1f5fe,stroke:#01579b")
    lines.append("    classDef tool fill:#f3e5f5,stroke:#4a148c")
    lines.append("    classDef transform fill:#fff3e0,stroke:#e65100")
    lines.append("    classDef router fill:#fce4ec,stroke:#880e4f")
    lines.append("    classDef agent fill:#e8f5e9,stroke:#1b5e20")
    lines.append("    classDef input fill:#f5f5f5,stroke:#424242")
    lines.append("")

    # Track node types for styling
    node_classes: dict[str, str] = {}

    # Add nodes
    for nid, node in (pathway.nodes or {}).items():
        ntype = _get_node_type(node)
        label_parts = [_escape_mermaid(nid)]

        if show_types:
            label_parts.append(f"<i>{ntype}</i>")

        if show_prompts:
            prompt = getattr(node, "prompt", None)
            if prompt and isinstance(prompt, str):
                truncated = prompt[:40].replace("\n", " ")
                if len(prompt) > 40:
                    truncated += "..."
                label_parts.append(f"<small>{_escape_mermaid(truncated)}</small>")

        label = "<br/>".join(label_parts)

        # Choose shape based on type
        shape = _get_mermaid_shape(ntype)
        lines.append(f"    {nid}{shape[0]}{label}{shape[1]}")

        # Track class
        node_classes[nid] = _get_node_class(ntype)

    lines.append("")

    # Add virtual input/output nodes if referenced
    conn_sources = {c.from_node for c in (pathway.connections or [])}
    conn_targets = {c.to_node for c in (pathway.connections or [])}
    node_ids = set(pathway.nodes.keys()) if pathway.nodes else set()

    if "input" in conn_sources and "input" not in node_ids:
        lines.append("    input([input])")
        node_classes["input"] = "input"

    if "output" in conn_targets and "output" not in node_ids:
        lines.append("    output([output])")
        node_classes["output"] = "input"

    # Add connections
    lines.append("")
    for conn in pathway.connections or []:
        lines.append(f"    {conn.from_node} --> {conn.to_node}")

    # Apply classes
    lines.append("")
    for nid, cls in node_classes.items():
        lines.append(f"    class {nid} {cls}")

    return "\n".join(lines)


def _escape_mermaid(text: str) -> str:
    """Escape special characters for Mermaid labels."""
    return (
        text.replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def _get_node_type(node: Any) -> str:
    """Get human-readable node type."""
    if hasattr(node, "type"):
        return str(node.type)
    return node.__class__.__name__.replace("Node", "")


def _get_mermaid_shape(ntype: str) -> tuple[str, str]:
    """Return Mermaid shape brackets based on node type."""
    ntype_lower = ntype.lower()
    if "llm" in ntype_lower:
        return ("[", "]")  # Rectangle
    if "tool" in ntype_lower:
        return ("[[", "]]")  # Subroutine
    if "router" in ntype_lower or "gate" in ntype_lower:
        return ("{", "}")  # Diamond
    if "transform" in ntype_lower:
        return ("(", ")")  # Stadium
    if "agent" in ntype_lower:
        return ("((", "))")  # Circle
    return ("[", "]")  # Default rectangle


def _get_node_class(ntype: str) -> str:
    """Get CSS class for node type."""
    ntype_lower = ntype.lower()
    if "llm" in ntype_lower:
        return "llm"
    if "tool" in ntype_lower:
        return "tool"
    if "transform" in ntype_lower:
        return "transform"
    if "router" in ntype_lower or "gate" in ntype_lower:
        return "router"
    if "agent" in ntype_lower:
        return "agent"
    return "input"


# =============================================================================
# ASCII FORMAT
# =============================================================================


def pathway_to_ascii(
    pathway: "Pathway",
    *,
    show_types: bool = True,
    max_width: int = 80,
) -> str:
    """Convert a pathway to ASCII art diagram.

    Args:
        pathway: The pathway to visualize
        show_types: Include node type in box
        max_width: Maximum width of output

    Returns:
        ASCII art diagram
    """
    if not pathway.nodes:
        return "(empty pathway)"

    # Build adjacency for topological layers
    adj: dict[str, list[str]] = {nid: [] for nid in pathway.nodes}
    in_degree: dict[str, int] = {nid: 0 for nid in pathway.nodes}

    # Add virtual nodes
    conn_sources = {c.from_node for c in (pathway.connections or [])}
    conn_targets = {c.to_node for c in (pathway.connections or [])}

    if "input" in conn_sources and "input" not in pathway.nodes:
        adj["input"] = []
        in_degree["input"] = 0

    if "output" in conn_targets and "output" not in pathway.nodes:
        adj["output"] = []
        in_degree["output"] = 0

    for conn in pathway.connections or []:
        if conn.from_node in adj:
            adj[conn.from_node].append(conn.to_node)
        if conn.to_node in in_degree:
            in_degree[conn.to_node] = in_degree.get(conn.to_node, 0) + 1

    # Assign layers using topological sort
    layers: list[list[str]] = []
    remaining = set(adj.keys())

    while remaining:
        # Find nodes with no incoming edges from remaining
        layer = [n for n in remaining if in_degree.get(n, 0) == 0]
        if not layer:
            # Cycle detected, just add remaining
            layer = list(remaining)
        layers.append(sorted(layer))
        remaining -= set(layer)
        # Decrease in-degree for successors
        for n in layer:
            for succ in adj.get(n, []):
                if succ in in_degree:
                    in_degree[succ] -= 1

    # Build ASCII representation
    lines: list[str] = []
    lines.append(f"Pathway: {pathway.id}")
    lines.append("=" * min(len(pathway.id) + 9, max_width))
    lines.append("")

    for layer_idx, layer in enumerate(layers):
        # Draw boxes for this layer
        box_lines = _draw_boxes(layer, pathway.nodes, show_types)
        lines.extend(box_lines)

        # Draw arrows to next layer if not last
        if layer_idx < len(layers) - 1:
            next_layer = layers[layer_idx + 1]
            arrow_lines = _draw_arrows(layer, next_layer, adj)
            lines.extend(arrow_lines)
            lines.append("")

    return "\n".join(lines)


def _draw_boxes(
    node_ids: list[str],
    nodes: dict[str, Any] | None,
    show_types: bool,
) -> list[str]:
    """Draw ASCII boxes for a layer of nodes."""
    boxes: list[list[str]] = []
    nodes = nodes or {}

    for nid in node_ids:
        node = nodes.get(nid)
        if node:
            ntype = _get_node_type(node) if show_types else ""
        else:
            ntype = "virtual" if show_types else ""

        # Build box content
        label = nid
        if ntype:
            label = f"{nid} [{ntype}]"

        width = max(len(label) + 2, 10)
        box = [
            "┌" + "─" * width + "┐",
            "│" + label.center(width) + "│",
            "└" + "─" * width + "┘",
        ]
        boxes.append(box)

    # Combine boxes horizontally
    if not boxes:
        return []

    result: list[str] = []
    for row in range(3):
        line = "  ".join(box[row] for box in boxes)
        result.append("  " + line)

    return result


def _draw_arrows(
    from_layer: list[str],
    to_layer: list[str],
    adj: dict[str, list[str]],
) -> list[str]:
    """Draw arrows between layers."""
    # Simple: just draw vertical arrows
    arrows = []
    for from_node in from_layer:
        for to_node in adj.get(from_node, []):
            if to_node in to_layer:
                arrows.append(f"  {from_node} ──▶ {to_node}")

    if arrows:
        return ["      │", "      ▼"] + arrows
    return ["      │", "      ▼"]


# =============================================================================
# DOT (GRAPHVIZ) FORMAT
# =============================================================================


def pathway_to_dot(
    pathway: "Pathway",
    *,
    show_types: bool = True,
    rankdir: str = "LR",
) -> str:
    """Convert a pathway to Graphviz DOT format.

    Args:
        pathway: The pathway to visualize
        show_types: Include node type in label
        rankdir: Graph direction (LR, TB, RL, BT)

    Returns:
        DOT format string
    """
    lines = [
        f'digraph "{pathway.id}" {{',
        f"    rankdir={rankdir};",
        '    node [shape=box, style="rounded,filled"];',
        "",
    ]

    # Node colors by type
    colors = {
        "llm": "#e1f5fe",
        "tool": "#f3e5f5",
        "transform": "#fff3e0",
        "router": "#fce4ec",
        "agent": "#e8f5e9",
        "input": "#f5f5f5",
    }

    # Add nodes
    for nid, node in (pathway.nodes or {}).items():
        ntype = _get_node_type(node)
        label = f"{nid}\\n{ntype}" if show_types else nid
        color = colors.get(_get_node_class(ntype), "#ffffff")
        lines.append(f'    "{nid}" [label="{label}", fillcolor="{color}"];')

    # Add virtual nodes
    conn_sources = {c.from_node for c in (pathway.connections or [])}
    conn_targets = {c.to_node for c in (pathway.connections or [])}
    node_ids = set(pathway.nodes.keys()) if pathway.nodes else set()

    if "input" in conn_sources and "input" not in node_ids:
        lines.append(f'    "input" [label="input", shape=ellipse, fillcolor="{colors["input"]}"];')

    if "output" in conn_targets and "output" not in node_ids:
        lines.append(f'    "output" [label="output", shape=ellipse, fillcolor="{colors["input"]}"];')

    lines.append("")

    # Add edges
    for conn in pathway.connections or []:
        lines.append(f'    "{conn.from_node}" -> "{conn.to_node}";')

    lines.append("}")
    return "\n".join(lines)


# =============================================================================
# D3 JSON FORMAT
# =============================================================================


def pathway_to_d3_json(
    pathway: "Pathway",
    *,
    include_metadata: bool = True,
) -> dict[str, Any]:
    """Convert a pathway to D3.js-compatible JSON.

    Returns a dict with:
    - nodes: list of {id, type, label, ...}
    - links: list of {source, target}

    Args:
        pathway: The pathway to visualize
        include_metadata: Include node metadata (prompt, args, etc.)

    Returns:
        D3-compatible graph structure
    """
    nodes: list[dict[str, Any]] = []
    links: list[dict[str, str]] = []

    # Add nodes
    for nid, node in (pathway.nodes or {}).items():
        ntype = _get_node_type(node)
        node_data: dict[str, Any] = {
            "id": nid,
            "type": ntype,
            "label": nid,
            "group": _get_node_class(ntype),
        }
        if include_metadata:
            if hasattr(node, "prompt"):
                node_data["prompt"] = str(node.prompt)[:200]
            if hasattr(node, "tool"):
                node_data["tool"] = str(node.tool)
            if hasattr(node, "model"):
                node_data["model"] = str(node.model)
        nodes.append(node_data)

    # Add virtual nodes
    conn_sources = {c.from_node for c in (pathway.connections or [])}
    conn_targets = {c.to_node for c in (pathway.connections or [])}
    node_ids = set(pathway.nodes.keys()) if pathway.nodes else set()

    if "input" in conn_sources and "input" not in node_ids:
        nodes.append({"id": "input", "type": "virtual", "label": "input", "group": "input"})

    if "output" in conn_targets and "output" not in node_ids:
        nodes.append({"id": "output", "type": "virtual", "label": "output", "group": "input"})

    # Add links
    for conn in pathway.connections or []:
        links.append({"source": conn.from_node, "target": conn.to_node})

    return {
        "pathway_id": pathway.id,
        "pathway_name": pathway.name,
        "nodes": nodes,
        "links": links,
    }


# =============================================================================
# PACK VISUALIZATION
# =============================================================================
# NOTE: Pack visualization removed - Pack concept was removed from the codebase

def _get_trigger_icon(source: str) -> str:
    """Get emoji icon for trigger source."""
    icons = {
        "webhook": "🌐",
        "timer": "⏰",
        "mcp": "🔌",
        "event": "📨",
        "manual": "👆",
    }
    for key, icon in icons.items():
        if key in source.lower():
            return icon
    return "⚡"


def _safe_id(text: str) -> str:
    """Make text safe for Mermaid node IDs."""
    return text.replace(".", "_").replace("-", "_")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def visualize(
    obj: Any,
    format: str = "mermaid",
    **kwargs: Any,
) -> str:
    """Visualize a pathway or pack in the specified format.

    Args:
        obj: Pathway to visualize
        format: Output format (mermaid, ascii, dot, d3_json)
        **kwargs: Format-specific options

    Returns:
        Visualization string (or dict for d3_json)
    """
    from pathway_engine.domain.pathway import Pathway

    if isinstance(obj, Pathway):
        if format == "mermaid":
            return pathway_to_mermaid(obj, **kwargs)
        if format == "ascii":
            return pathway_to_ascii(obj, **kwargs)
        if format == "dot":
            return pathway_to_dot(obj, **kwargs)
        if format == "d3_json":
            import json
            return json.dumps(pathway_to_d3_json(obj, **kwargs), indent=2)
        raise ValueError(f"Unknown format: {format}")

    raise TypeError(f"Cannot visualize {type(obj).__name__}")


# =============================================================================
# STDLIB TOOLS - Albus-callable visualization tools
# =============================================================================


@register_tool("pathway.visualize")
async def visualize_pathway_tool(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Generate a visualization diagram for a pathway.

    Inputs:
        pathway_id: Pathway ID to visualize (pack pathway or doc_id)
        format: Output format (mermaid, ascii, dot, d3) - default: mermaid
        show_types: Include node types in labels (default: true)
        show_prompts: Include truncated prompts (default: false, mermaid only)

    Returns:
        diagram: The diagram code/data
        format: The format used
        pathway_id: The pathway visualized
    """
    pathway_id = str(inputs.get("pathway_id") or "").strip()
    fmt = str(inputs.get("format") or "mermaid").strip().lower()
    show_types = inputs.get("show_types", True)
    show_prompts = inputs.get("show_prompts", False)

    if not pathway_id:
        return {"success": False, "error": "pathway_id is required"}

    valid_formats = {"mermaid", "ascii", "dot", "d3", "d3_json"}
    if fmt not in valid_formats:
        return {"success": False, "error": f"Invalid format. Use: {', '.join(valid_formats)}"}

    try:
        # Try to load pathway
        pathway = None
        source = None

        # Try doc pathway
        if pathway is None and context is not None:
            try:
                domain = getattr(context, "domain", None)
                if domain and pathway_id.startswith("doc_"):
                    from pathway_engine.domain.pathway import Pathway, Connection

                    head = domain.get_head_content(doc_id=pathway_id)
                    if isinstance(head, dict):
                        pathway = _pathway_from_dict(head)
                        source = "doc"
            except Exception as e:
                logger.debug("Failed to load doc pathway: %s", e)

        if pathway is None:
            return {
                "success": False,
                "error": f"Pathway not found: {pathway_id}",
                "hint": "Use pack pathway ID (e.g., 'quickstart.echo.v1') or doc_id",
            }

        # Generate diagram
        if fmt == "mermaid":
            diagram = pathway_to_mermaid(
                pathway, show_types=show_types, show_prompts=show_prompts
            )
        elif fmt == "ascii":
            diagram = pathway_to_ascii(pathway, show_types=show_types)
        elif fmt == "dot":
            diagram = pathway_to_dot(pathway, show_types=show_types)
        elif fmt in ("d3", "d3_json"):
            import json
            diagram = json.dumps(pathway_to_d3_json(pathway), indent=2)
        else:
            diagram = pathway_to_mermaid(pathway)

        return {
            "success": True,
            "diagram": diagram,
            "format": fmt,
            "pathway_id": pathway_id,
            "source": source,
        }

    except Exception as e:
        logger.error("Failed to visualize pathway %s: %s", pathway_id, e)
        return {"success": False, "error": str(e)}


@register_tool("viz.list_pathways")
async def list_visualizable_pathways(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """List all pathways that can be visualized.

    Returns:
        pathways: List of pathway IDs with their sources
    """
    # Packs removed - return empty list, pathways come from PathwayService
    return {
        "success": True,
        "pathways": [],
        "total_pathways": 0,
        "hint": "Use PathwayService to list pathways",
    }


def _pathway_from_dict(data: dict[str, Any]) -> "Pathway":
    """Convert dict to Pathway for visualization."""
    from pathway_engine.domain.pathway import Pathway, Connection
    from pathway_engine.domain.nodes.core import LLMNode, ToolNode, TransformNode

    nodes: dict[str, Any] = {}
    for n in data.get("nodes", []):
        if isinstance(n, dict):
            nid = n.get("id", "unknown")
            ntype = str(n.get("type", "")).lower()
            config = n.get("config", {})

            if "llm" in ntype:
                nodes[nid] = LLMNode(
                    id=nid,
                    prompt=config.get("prompt", ""),
                    model=config.get("model", "auto"),
                )
            elif "tool" in ntype:
                nodes[nid] = ToolNode(
                    id=nid,
                    tool=config.get("tool", "unknown"),
                    args=config.get("args", {}),
                )
            else:
                nodes[nid] = TransformNode(id=nid, expression="input")

    connections = []
    for c in data.get("connections", []):
        if isinstance(c, dict):
            from_n = c.get("from") or c.get("from_node")
            to_n = c.get("to") or c.get("to_node")
            if from_n and to_n:
                connections.append(Connection(from_node=from_n, to_node=to_n))
        elif isinstance(c, str) and "->" in c:
            parts = c.split("->")
            if len(parts) == 2:
                connections.append(
                    Connection(from_node=parts[0].strip(), to_node=parts[1].strip())
                )

    return Pathway(
        id=data.get("id", "unknown"),
        name=data.get("name", "Unknown"),
        nodes=nodes,
        connections=connections,
    )


# =============================================================================
# KNOWLEDGE GRAPH VISUALIZATION
# =============================================================================


def kg_to_mermaid(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    direction: str = "TB",
    show_types: bool = True,
    title: str | None = None,
) -> str:
    """Convert knowledge graph nodes/edges to Mermaid diagram.

    Args:
        nodes: List of node dicts with id, type, label
        edges: List of edge dicts with subject, predicate, object
        direction: Graph direction (TB, LR, RL, BT)
        show_types: Include node type in label
        title: Optional title for the diagram

    Returns:
        Mermaid diagram code
    """
    lines = [f"graph {direction}"]

    # Style definitions for different node types
    lines.append("    %% Node styles")
    lines.append("    classDef concept fill:#e3f2fd,stroke:#1565c0")
    lines.append("    classDef philosopher fill:#fff3e0,stroke:#e65100")
    lines.append("    classDef argument fill:#f3e5f5,stroke:#4a148c")
    lines.append("    classDef work fill:#e8f5e9,stroke:#1b5e20")
    lines.append("    classDef position fill:#fce4ec,stroke:#880e4f")
    lines.append("    classDef entity fill:#f5f5f5,stroke:#424242")
    lines.append("")

    if title:
        lines.append(f"    subgraph title[\"{_escape_mermaid(title)}\"]")
        lines.append("    direction " + direction)

    # Track node types for styling (keyed by safe_id)
    node_classes: dict[str, str] = {}
    safe_ids_seen: set[str] = set()

    # Add nodes
    for node in nodes:
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        safe_id = _safe_kg_id(nid)
        if safe_id in safe_ids_seen:
            continue
        safe_ids_seen.add(safe_id)
        ntype = str(node.get("type", "entity")).strip().lower()
        label = str(node.get("label") or nid).strip()

        if show_types and ntype and ntype != "entity":
            display_label = f"{_escape_mermaid(label)}<br/><i>{ntype}</i>"
        else:
            display_label = _escape_mermaid(label)

        # Choose shape based on type
        shape = _get_kg_shape(ntype)
        indent = "        " if title else "    "
        lines.append(f"{indent}{safe_id}{shape[0]}{display_label}{shape[1]}")

        # Track class for styling
        node_classes[safe_id] = _get_kg_class(ntype)

    # Add edges
    lines.append("")
    edge_labels_used: set[str] = set()

    for edge in edges:
        subj = str(edge.get("subject", "")).strip()
        pred = str(edge.get("predicate", "")).strip()
        obj = str(edge.get("object", "")).strip()

        if not (subj and pred and obj):
            continue

        safe_subj = _safe_kg_id(subj)
        safe_obj = _safe_kg_id(obj)

        # Ensure nodes exist (create implicit nodes if needed)
        indent = "        " if title else "    "
        if safe_subj not in safe_ids_seen:
            safe_ids_seen.add(safe_subj)
            lines.insert(-1, f"{indent}{safe_subj}[{_escape_mermaid(subj)}]")
            node_classes[safe_subj] = "entity"

        if safe_obj not in safe_ids_seen:
            safe_ids_seen.add(safe_obj)
            lines.insert(-1, f"{indent}{safe_obj}[{_escape_mermaid(obj)}]")
            node_classes[safe_obj] = "entity"

        # Edge with label
        edge_key = f"{safe_subj}-{safe_obj}"
        if edge_key not in edge_labels_used:
            edge_labels_used.add(edge_key)
            lines.append(f"{indent}{safe_subj} -->|\"{_escape_mermaid(pred)}\"| {safe_obj}")

    if title:
        lines.append("    end")

    # Apply classes
    lines.append("")
    for nid, cls in node_classes.items():
        lines.append(f"    class {nid} {cls}")

    return "\n".join(lines)


def kg_to_dot(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    show_types: bool = True,
    rankdir: str = "TB",
    title: str | None = None,
) -> str:
    """Convert knowledge graph to Graphviz DOT format.

    Args:
        nodes: List of node dicts with id, type, label
        edges: List of edge dicts with subject, predicate, object
        show_types: Include node type in label
        rankdir: Graph direction (LR, TB, RL, BT)
        title: Optional title for the graph

    Returns:
        DOT format string
    """
    graph_name = _safe_kg_id(title) if title else "knowledge_graph"
    lines = [
        f'digraph "{graph_name}" {{',
        f"    rankdir={rankdir};",
        '    node [shape=box, style="rounded,filled"];',
        "",
    ]

    if title:
        lines.append(f'    label="{_escape_dot(title)}";')
        lines.append("    labelloc=t;")
        lines.append("")

    # Node colors by type
    colors = {
        "concept": "#e3f2fd",
        "philosopher": "#fff3e0",
        "argument": "#f3e5f5",
        "work": "#e8f5e9",
        "position": "#fce4ec",
        "entity": "#f5f5f5",
    }

    node_ids_seen: set[str] = set()

    # Add nodes
    for node in nodes:
        nid = str(node.get("id", "")).strip()
        if not nid or nid in node_ids_seen:
            continue
        node_ids_seen.add(nid)

        safe_id = _safe_kg_id(nid)
        ntype = str(node.get("type", "entity")).strip().lower()
        label = str(node.get("label") or nid).strip()

        if show_types and ntype and ntype != "entity":
            display_label = f"{label}\\n({ntype})"
        else:
            display_label = label

        color = colors.get(ntype, colors["entity"])
        lines.append(f'    "{safe_id}" [label="{_escape_dot(display_label)}", fillcolor="{color}"];')

    lines.append("")

    # Add edges
    for edge in edges:
        subj = str(edge.get("subject", "")).strip()
        pred = str(edge.get("predicate", "")).strip()
        obj = str(edge.get("object", "")).strip()

        if not (subj and pred and obj):
            continue

        safe_subj = _safe_kg_id(subj)
        safe_obj = _safe_kg_id(obj)

        lines.append(f'    "{safe_subj}" -> "{safe_obj}" [label="{_escape_dot(pred)}"];')

    lines.append("}")
    return "\n".join(lines)


def kg_to_ascii(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    show_types: bool = True,
    title: str | None = None,
) -> str:
    """Convert knowledge graph to ASCII art.

    Args:
        nodes: List of node dicts with id, type, label
        edges: List of edge dicts with subject, predicate, object
        show_types: Include node type in label
        title: Optional title

    Returns:
        ASCII diagram
    """
    lines: list[str] = []

    if title:
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")

    lines.append("NODES:")
    lines.append("-" * 40)

    for node in nodes:
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        ntype = str(node.get("type", "entity")).strip()
        label = str(node.get("label") or nid).strip()

        if show_types and ntype:
            lines.append(f"  [{ntype}] {label}")
        else:
            lines.append(f"  {label}")

    lines.append("")
    lines.append("RELATIONS:")
    lines.append("-" * 40)

    for edge in edges:
        subj = str(edge.get("subject", "")).strip()
        pred = str(edge.get("predicate", "")).strip()
        obj = str(edge.get("object", "")).strip()
        conf = edge.get("confidence", 1.0)

        if not (subj and pred and obj):
            continue

        try:
            conf_f = float(conf)
        except (ValueError, TypeError):
            conf_f = 1.0

        lines.append(f"  {subj} --[{pred}]--> {obj}  ({conf_f:.0%})")

    return "\n".join(lines)


def _safe_kg_id(text: str) -> str:
    """Make text safe for Mermaid/DOT node IDs."""
    import re
    # Replace non-alphanumeric with underscore, collapse multiple underscores
    safe = re.sub(r"[^a-zA-Z0-9]", "_", text)
    safe = re.sub(r"_+", "_", safe).strip("_")
    # Ensure it starts with a letter
    if safe and not safe[0].isalpha():
        safe = "n_" + safe
    return safe[:64] if len(safe) > 64 else (safe or "node")


def _escape_dot(text: str) -> str:
    """Escape special characters for DOT labels."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _get_kg_shape(ntype: str) -> tuple[str, str]:
    """Return Mermaid shape brackets based on node type."""
    ntype_lower = ntype.lower()
    if ntype_lower in ("concept", "idea", "term"):
        return ("([", "])")  # Stadium
    if ntype_lower in ("philosopher", "person", "author"):
        return ("((", "))")  # Circle
    if ntype_lower in ("argument", "claim", "thesis"):
        return ("{", "}")  # Diamond
    if ntype_lower in ("work", "text", "book"):
        return ("[[", "]]")  # Subroutine
    if ntype_lower in ("position", "view", "school"):
        return ("[/", "/]")  # Parallelogram
    return ("[", "]")  # Default rectangle


def _get_kg_class(ntype: str) -> str:
    """Get CSS class for KG node type."""
    ntype_lower = ntype.lower()
    if ntype_lower in ("concept", "idea", "term"):
        return "concept"
    if ntype_lower in ("philosopher", "person", "author"):
        return "philosopher"
    if ntype_lower in ("argument", "claim", "thesis"):
        return "argument"
    if ntype_lower in ("work", "text", "book"):
        return "work"
    if ntype_lower in ("position", "view", "school"):
        return "position"
    return "entity"


@register_tool("kg.visualize")
async def visualize_kg_tool(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Generate a visualization diagram for a knowledge graph.

    Inputs:
        namespace: KG namespace to visualize (default: "default")
        query: Optional query to filter nodes/edges (if omitted, shows recent)
        entity_id: Optional entity to center visualization on
        depth: Traversal depth from entity_id (default: 2)
        limit: Max nodes/edges to include (default: 30)
        format: Output format (mermaid, dot, ascii) - default: mermaid
        direction: Graph direction for mermaid/dot (TB, LR) - default: TB
        title: Optional title for the diagram
        show_types: Include node types in labels (default: true)

    Returns:
        diagram: The diagram code
        format: The format used
        node_count: Number of nodes included
        edge_count: Number of edges included
    """
    namespace = str(inputs.get("namespace") or "default").strip()
    query = inputs.get("query")
    entity_id = inputs.get("entity_id")
    # Handle empty strings for integer params
    depth_raw = inputs.get("depth")
    depth = int(depth_raw) if depth_raw not in (None, "", "None") else 2
    limit_raw = inputs.get("limit")
    limit = int(limit_raw) if limit_raw not in (None, "", "None") else 30
    fmt = str(inputs.get("format") or "mermaid").strip().lower()
    direction_raw = inputs.get("direction")
    direction = str(direction_raw).strip().upper() if direction_raw not in (None, "", "None") else "TB"
    title = inputs.get("title")
    show_types = inputs.get("show_types", True)

    valid_formats = {"mermaid", "dot", "ascii"}
    if fmt not in valid_formats:
        return {"success": False, "error": f"Invalid format. Use: {', '.join(valid_formats)}"}

    if direction not in ("TB", "LR", "RL", "BT"):
        direction = "TB"

    try:
        # Import the KG module to query it
        from stdlib.tools.kg import _KG

        # Get nodes and edges from the KG
        if entity_id:
            # Query centered on an entity
            result = _KG.query(
                namespace=namespace,
                entity_id=str(entity_id).strip(),
                depth=depth,
                limit=limit,
            )
        elif query:
            # Query by text
            result = _KG.query(
                namespace=namespace,
                query=str(query).strip(),
                limit=limit,
            )
        else:
            # Get current state (goals, projects, tasks + edges)
            current = _KG.current(namespace=namespace, limit=limit)
            # Combine into hits format
            nodes_list = current.get("goals", []) + current.get("projects", []) + current.get("tasks", [])
            edges_list = current.get("edges", [])
            result = {"hits": []}
            for n in nodes_list:
                result["hits"].append({"kind": "node", **n})
            for e in edges_list:
                result["hits"].append({"kind": "edge", **e})

        # Separate nodes and edges from hits
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        for hit in result.get("hits", []):
            if hit.get("kind") == "node":
                nodes.append(hit)
            elif hit.get("kind") == "edge":
                edges.append(hit)

        if not nodes and not edges:
            return {
                "success": True,
                "diagram": "(empty knowledge graph)",
                "format": fmt,
                "node_count": 0,
                "edge_count": 0,
                "hint": "Use kg.upsert to add nodes and edges first",
            }

        # Generate diagram based on format
        if fmt == "mermaid":
            diagram = kg_to_mermaid(
                nodes, edges,
                direction=direction,
                show_types=show_types,
                title=str(title) if title else None,
            )
        elif fmt == "dot":
            diagram = kg_to_dot(
                nodes, edges,
                show_types=show_types,
                rankdir=direction,
                title=str(title) if title else None,
            )
        else:  # ascii
            diagram = kg_to_ascii(
                nodes, edges,
                show_types=show_types,
                title=str(title) if title else None,
            )

        return {
            "success": True,
            "diagram": diagram,
            "format": fmt,
            "namespace": namespace,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    except Exception as e:
        logger.error("Failed to visualize knowledge graph: %s", e)
        return {"success": False, "error": str(e)}


__all__ = [
    # Conversion functions
    "pathway_to_mermaid",
    "pathway_to_ascii",
    "pathway_to_dot",
    "pathway_to_d3_json",
    "visualize",
    # KG visualization functions
    "kg_to_mermaid",
    "kg_to_dot",
    "kg_to_ascii",
    # Stdlib tools
    "visualize_pathway_tool",
    "list_visualizable_pathways",
    "visualize_kg_tool",
]
