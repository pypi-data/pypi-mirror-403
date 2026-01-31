"""PathwayDoc - Validation and operations for pathway documents.

Pathway documents are JSON representations of graphs:
{
    "nodes": [{"id": "...", "type": "...", ...}, ...],
    "connections": [{"from": "...", "to": "..."}, ...]
}

This module handles validation and patching of these documents.
"""

from __future__ import annotations

from typing import Any

from shared_types.schemas.expression import ExpressionV1, validate_expression_v1
from persistence.domain.errors import StudioValidationError


def validate_pathway_semantics(content: dict[str, Any]) -> None:
    """Minimal, high-value semantic invariants for Pathway documents.

    We enforce:
    - node ids are strings + unique
    - connection endpoints reference existing node ids
    - expression fields are valid
    """
    if not isinstance(content, dict):
        raise StudioValidationError("pathwaydoc_not_an_object")

    # Empty document is allowed
    if not content:
        return

    nodes_raw = content.get("nodes", [])
    connections_raw = content.get("connections", [])

    if not isinstance(nodes_raw, list):
        raise StudioValidationError("nodes_not_a_list")

    # Validate nodes and collect IDs
    node_ids: set[str] = set()
    for i, node in enumerate(nodes_raw):
        if not isinstance(node, dict):
            raise StudioValidationError(f"nodes[{i}]_not_an_object")

        node_id = str(node.get("id", "")).strip()
        if not node_id:
            raise StudioValidationError(f"nodes[{i}]_missing_id")

        if node_id in node_ids:
            raise StudioValidationError(f"duplicate_node_id:{node_id}")
        node_ids.add(node_id)

        node_type = str(node.get("type", "")).strip().lower()
        if not node_type:
            raise StudioValidationError(f"nodes[{i}]_missing_type")

        # Validate expressions in specific node types
        if node_type == "router":
            condition = node.get("condition")
            if condition and isinstance(condition, dict):
                try:
                    expr = ExpressionV1.model_validate(condition)
                    v = validate_expression_v1(
                        ExpressionV1(
                            **{
                                **expr.model_dump(),
                                "context_id": "router_v1",
                                "expected_type": "string",
                            }
                        )
                    )
                    if not v.ok:
                        raise StudioValidationError(
                            f"nodes[{i}]_router_condition_invalid:{v.error}"
                        )
                except StudioValidationError:
                    raise
                except Exception:
                    pass  # Allow string conditions

    # Validate connections
    if not isinstance(connections_raw, list):
        if connections_raw is not None:
            raise StudioValidationError("connections_not_a_list")
        return

    seen_connections: set[tuple[str, str]] = set()
    for i, conn in enumerate(connections_raw):
        if not isinstance(conn, dict):
            raise StudioValidationError(f"connections[{i}]_not_an_object")

        from_node = str(conn.get("from", conn.get("from_node", ""))).strip()
        to_node = str(conn.get("to", conn.get("to_node", ""))).strip()

        if not from_node or not to_node:
            raise StudioValidationError(f"connections[{i}]_missing_from_or_to")

        if from_node not in node_ids:
            raise StudioValidationError(f"connections[{i}]_unknown_from:{from_node}")
        if to_node not in node_ids:
            raise StudioValidationError(f"connections[{i}]_unknown_to:{to_node}")

        conn_key = (from_node, to_node)
        if conn_key in seen_connections:
            raise StudioValidationError(
                f"connections[{i}]_duplicate:{from_node}→{to_node}"
            )
        seen_connections.add(conn_key)


def normalize_pathway_doc_content(content: dict[str, Any]) -> dict[str, Any]:
    """Normalize PathwayDoc content.

    Preserves content as-is; validation happens separately.
    """
    return dict(content or {})


def apply_ops(base: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply a minimal (validated) op stream to a JSON-like dict.

    Supported ops:
    - set: path (list[str|int]), value
    - delete: path (list[str|int])
    """

    def _clone(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: _clone(v) for k, v in x.items()}
        if isinstance(x, list):
            return [_clone(v) for v in x]
        return x

    def _ensure_container(parent: Any, key: str | int) -> Any:
        if isinstance(key, int):
            if not isinstance(parent, list):
                raise StudioValidationError("patch path expects list container")
            while len(parent) <= key:
                parent.append({})
            return parent
        if not isinstance(parent, dict):
            raise StudioValidationError("patch path expects dict container")
        if key not in parent or parent[key] is None:
            parent[key] = {}
        return parent

    out: Any = _clone(base)
    if not isinstance(out, dict):
        raise StudioValidationError("base content must be an object")

    for raw in ops:
        op = str(raw.get("op") or "")
        path = raw.get("path")
        if not isinstance(path, list) or not path:
            raise StudioValidationError("patch op path must be a non-empty list")
        parts: list[str | int] = []
        for p in path:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, int):
                parts.append(int(p))
            else:
                raise StudioValidationError(
                    "patch path parts must be string or integer"
                )

        parent: Any = out
        for part in parts[:-1]:
            parent = _ensure_container(parent, part)
            if isinstance(part, int):
                parent = parent[part]
            else:
                parent = parent[part]

        last = parts[-1]
        if op == "set":
            value = raw.get("value")
            if isinstance(last, int):
                if not isinstance(parent, list):
                    raise StudioValidationError("patch path expects list container")
                while len(parent) <= last:
                    parent.append(None)
                parent[last] = _clone(value)
            else:
                if not isinstance(parent, dict):
                    raise StudioValidationError("patch path expects dict container")
                parent[last] = _clone(value)
        elif op == "delete":
            if isinstance(last, int):
                if not isinstance(parent, list):
                    raise StudioValidationError("patch path expects list container")
                if 0 <= last < len(parent):
                    parent.pop(last)
            else:
                if not isinstance(parent, dict):
                    raise StudioValidationError("patch path expects dict container")
                parent.pop(last, None)
        else:
            raise StudioValidationError("unsupported patch op (expected set|delete)")

    if not isinstance(out, dict):
        raise StudioValidationError("patched content must be an object")
    return out
