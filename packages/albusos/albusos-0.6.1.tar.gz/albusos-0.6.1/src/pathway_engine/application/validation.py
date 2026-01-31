"""Pathway Validation - Pre-run validation for pathways.

This module provides comprehensive validation of pathways before execution:
- Check for empty pathways
- Validate node configurations (tools exist, expressions parse)
- Check connection validity (nodes exist)
- Detect cycles
- Check gate/router targets
- Identify orphan nodes

Usage:
    from pathway_engine.application.validation import validate_pathway
    
    result = validate_pathway(pathway, ctx)
    if not result.valid:
        for error in result.errors:
            print(f"Error: {error.message}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from pathway_engine.domain.pathway import PSEUDO_NODES

if TYPE_CHECKING:
    from pathway_engine.domain.pathway import Pathway
    from pathway_engine.domain.context import Context


@dataclass
class ValidationIssue:
    """A single validation error or warning."""

    code: str
    message: str
    severity: str  # "error" | "warning"
    node_id: str | None = None
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "node_id": self.node_id,
            "field": self.field,
        }


@dataclass
class ValidationResult:
    """Result of pathway validation."""

    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


def validate_pathway(pathway: "Pathway", ctx: "Context") -> ValidationResult:
    """Validate a pathway before execution.

    Args:
        pathway: The pathway to validate
        ctx: Execution context (for checking tool availability)

    Returns:
        ValidationResult with errors and warnings
    """
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    # 1. Check for empty pathway
    if not pathway.nodes:
        errors.append(
            ValidationIssue(
                code="EMPTY_PATHWAY",
                message="Pathway has no nodes",
                severity="error",
            )
        )
        # Return early - other checks don't make sense
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # 2. Validate each node
    for node_id, node in pathway.nodes.items():
        node_errors, node_warnings = _validate_node(node, ctx)
        errors.extend(node_errors)
        warnings.extend(node_warnings)

    # 3. Check connections reference valid nodes
    for conn in pathway.connections:
        if conn.from_node not in pathway.nodes:
            errors.append(
                ValidationIssue(
                    code="INVALID_CONNECTION_SOURCE",
                    message=f"Connection references unknown source node: {conn.from_node}",
                    severity="error",
                    field="from_node",
                )
            )
        if conn.to_node not in pathway.nodes:
            errors.append(
                ValidationIssue(
                    code="INVALID_CONNECTION_TARGET",
                    message=f"Connection references unknown target node: {conn.to_node}",
                    severity="error",
                    field="to_node",
                )
            )
        # Check for self-loops
        if conn.from_node == conn.to_node:
            errors.append(
                ValidationIssue(
                    code="SELF_LOOP",
                    message=f"Node '{conn.from_node}' has a connection to itself",
                    severity="error",
                    node_id=conn.from_node,
                )
            )

    # 4. Check for cycles
    cycle = find_cycle(pathway)
    if cycle:
        errors.append(
            ValidationIssue(
                code="CYCLE_DETECTED",
                message=(
                    "Pathway contains cycles - execution order cannot be determined. "
                    f"Cycle: {' -> '.join(cycle)}"
                ),
                severity="error",
                node_id=cycle[0] if cycle else None,
            )
        )

    # 5. Check for orphan nodes (no connections in or out)
    if len(pathway.nodes) > 1:
        connected_nodes = set()
        for conn in pathway.connections:
            connected_nodes.add(conn.from_node)
            connected_nodes.add(conn.to_node)

        for node_id in pathway.nodes:
            if node_id not in connected_nodes:
                warnings.append(
                    ValidationIssue(
                        code="ORPHAN_NODE",
                        message=f"Node '{node_id}' has no connections (will receive only initial inputs)",
                        severity="warning",
                        node_id=node_id,
                    )
                )

    # 6. Check gate/router targets exist
    for node_id, node in pathway.nodes.items():
        node_type = getattr(node, "type", None)

        if node_type == "gate":
            true_path = getattr(node, "true_path", None)
            false_path = getattr(node, "false_path", None)

            if true_path and true_path not in pathway.nodes:
                errors.append(
                    ValidationIssue(
                        code="INVALID_GATE_TARGET",
                        message=f"Gate true_path references unknown node: {true_path}",
                        severity="error",
                        node_id=node_id,
                        field="true_path",
                    )
                )
            if false_path and false_path not in pathway.nodes:
                errors.append(
                    ValidationIssue(
                        code="INVALID_GATE_TARGET",
                        message=f"Gate false_path references unknown node: {false_path}",
                        severity="error",
                        node_id=node_id,
                        field="false_path",
                    )
                )

        if node_type == "router":
            routes = getattr(node, "routes", {})
            default_route = getattr(node, "default", None)

            for route_value, target_id in routes.items():
                if target_id not in pathway.nodes:
                    errors.append(
                        ValidationIssue(
                            code="INVALID_ROUTE_TARGET",
                            message=f"Route '{route_value}' targets unknown node: {target_id}",
                            severity="error",
                            node_id=node_id,
                            field=f"routes.{route_value}",
                        )
                    )

            if default_route and default_route not in pathway.nodes:
                errors.append(
                    ValidationIssue(
                        code="INVALID_ROUTE_TARGET",
                        message=f"Default route targets unknown node: {default_route}",
                        severity="error",
                        node_id=node_id,
                        field="default",
                    )
                )

    # 7. Check for duplicate node IDs (shouldn't happen with dict, but validate anyway)
    # This is implicitly handled by dict keys, but we check for consistency

    # 8. Check loops reference valid body nodes
    for i, loop in enumerate(pathway.loops):
        for body_node in loop.body_nodes:
            if body_node not in pathway.nodes:
                errors.append(
                    ValidationIssue(
                        code="INVALID_LOOP_BODY",
                        message=f"Loop {i} references unknown body node: {body_node}",
                        severity="error",
                        field=f"loops[{i}].body_nodes",
                    )
                )

    # 9. Check gates reference valid nodes
    for i, gate in enumerate(pathway.gates):
        if gate.true_path not in pathway.nodes:
            errors.append(
                ValidationIssue(
                    code="INVALID_GATE_PATH",
                    message=f"Gate {i} true_path references unknown node: {gate.true_path}",
                    severity="error",
                    field=f"gates[{i}].true_path",
                )
            )
        if gate.false_path and gate.false_path not in pathway.nodes:
            errors.append(
                ValidationIssue(
                    code="INVALID_GATE_PATH",
                    message=f"Gate {i} false_path references unknown node: {gate.false_path}",
                    severity="error",
                    field=f"gates[{i}].false_path",
                )
            )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _validate_node(
    node: Any, ctx: "Context"
) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    """Validate a single node's configuration.

    Returns:
        Tuple of (errors, warnings)
    """
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    node_id = getattr(node, "id", "unknown")
    node_type = getattr(node, "type", None)

    # Type-specific validation
    if node_type == "tool":
        tool_name = getattr(node, "tool", "")
        if not tool_name:
            errors.append(
                ValidationIssue(
                    code="MISSING_TOOL_NAME",
                    message="Tool node has no tool specified",
                    severity="error",
                    node_id=node_id,
                    field="tool",
                )
            )
        elif tool_name not in (ctx.tools or {}):
            errors.append(
                ValidationIssue(
                    code="TOOL_NOT_FOUND",
                    message=f"Tool not found: {tool_name}",
                    severity="error",
                    node_id=node_id,
                    field="tool",
                )
            )

    elif node_type == "transform":
        expr = getattr(node, "expr", "")
        if not expr:
            errors.append(
                ValidationIssue(
                    code="EMPTY_EXPRESSION",
                    message="Transform node has no expression",
                    severity="error",
                    node_id=node_id,
                    field="expr",
                )
            )
        else:
            # Try to parse the expression
            from shared_types.expressions.safe_expr import (
                safe_expr_parse,
                SafeExpressionError,
            )

            try:
                safe_expr_parse(expr)
            except SafeExpressionError as e:
                errors.append(
                    ValidationIssue(
                        code="INVALID_EXPRESSION",
                        message=f"Invalid expression: {e}",
                        severity="error",
                        node_id=node_id,
                        field="expr",
                    )
                )

    elif node_type in ("gate", "router"):
        condition = getattr(node, "condition", "")
        if not condition:
            errors.append(
                ValidationIssue(
                    code="EMPTY_CONDITION",
                    message=f"{node_type.title()} node has no condition",
                    severity="error",
                    node_id=node_id,
                    field="condition",
                )
            )
        elif "{{" not in condition:
            # Only validate if not a template (templates are resolved at runtime)
            from shared_types.expressions.safe_expr import (
                safe_expr_parse,
                SafeExpressionError,
            )

            try:
                safe_expr_parse(condition)
            except SafeExpressionError as e:
                errors.append(
                    ValidationIssue(
                        code="INVALID_CONDITION",
                        message=f"Invalid condition expression: {e}",
                        severity="error",
                        node_id=node_id,
                        field="condition",
                    )
                )

    elif node_type == "llm":
        prompt = getattr(node, "prompt", "")
        if not prompt or not prompt.strip():
            errors.append(
                ValidationIssue(
                    code="EMPTY_PROMPT",
                    message="LLM node has empty prompt",
                    severity="error",
                    node_id=node_id,
                    field="prompt",
                )
            )

        # Check for valid model (warning only - model availability is runtime)
        model = getattr(node, "model", "")
        if not model:
            warnings.append(
                ValidationIssue(
                    code="NO_MODEL_SPECIFIED",
                    message="LLM node has no model specified (will use default)",
                    severity="warning",
                    node_id=node_id,
                    field="model",
                )
            )

        # Check JSON schema if response_format is json
        response_format = getattr(node, "response_format", "text")
        json_schema = getattr(node, "json_schema", None)
        if response_format == "json" and not json_schema:
            warnings.append(
                ValidationIssue(
                    code="JSON_WITHOUT_SCHEMA",
                    message="LLM node requests JSON but has no schema (output may be unpredictable)",
                    severity="warning",
                    node_id=node_id,
                    field="json_schema",
                )
            )

    elif node_type == "code":
        code = getattr(node, "code", "")
        if not code or not code.strip():
            errors.append(
                ValidationIssue(
                    code="EMPTY_CODE",
                    message="Code node has no code",
                    severity="error",
                    node_id=node_id,
                    field="code",
                )
            )
        else:
            # Try to compile the code (syntax check only)
            try:
                compile(code, "<pathway_code>", "exec")
            except SyntaxError as e:
                errors.append(
                    ValidationIssue(
                        code="INVALID_CODE_SYNTAX",
                        message=f"Code syntax error: {e.msg} at line {e.lineno}",
                        severity="error",
                        node_id=node_id,
                        field="code",
                    )
                )

    elif node_type == "agent_loop":
        tools = getattr(node, "tools", [])
        if not tools:
            warnings.append(
                ValidationIssue(
                    code="AGENT_NO_TOOLS",
                    message="AgentLoop has no tools pattern - agent will have no available tools",
                    severity="warning",
                    node_id=node_id,
                    field="tools",
                )
            )

        goal = getattr(node, "goal", "")
        if not goal:
            warnings.append(
                ValidationIssue(
                    code="AGENT_NO_GOAL",
                    message="AgentLoop has no goal specified",
                    severity="warning",
                    node_id=node_id,
                    field="goal",
                )
            )

    elif node_type == "map":
        over = getattr(node, "over", "")
        if not over:
            errors.append(
                ValidationIssue(
                    code="MAP_NO_COLLECTION",
                    message="Map node has no 'over' collection specified",
                    severity="error",
                    node_id=node_id,
                    field="over",
                )
            )

        node_data = getattr(node, "node_data", {})
        if not node_data:
            errors.append(
                ValidationIssue(
                    code="MAP_NO_NODE",
                    message="Map node has no node_data to apply",
                    severity="error",
                    node_id=node_id,
                    field="node_data",
                )
            )

    elif node_type in ("retry", "timeout", "fallback"):
        # Composition nodes should have inner node data
        if node_type == "fallback":
            nodes_data = getattr(node, "nodes_data", [])
            if not nodes_data:
                errors.append(
                    ValidationIssue(
                        code="FALLBACK_NO_NODES",
                        message="Fallback node has no fallback options",
                        severity="error",
                        node_id=node_id,
                        field="nodes_data",
                    )
                )
        else:
            node_data = getattr(node, "node_data", {})
            if not node_data:
                errors.append(
                    ValidationIssue(
                        code=f"{node_type.upper()}_NO_NODE",
                        message=f"{node_type.title()} node has no inner node",
                        severity="error",
                        node_id=node_id,
                        field="node_data",
                    )
                )

    return errors, warnings


def find_cycle(pathway: "Pathway") -> list[str] | None:
    """Find a cycle in the pathway graph using DFS.

    Returns:
        A list of node_ids representing the cycle, including the repeated
        start/end node to "close the loop" (e.g. ["a", "b", "c", "a"]),
        or None if no cycle exists.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {nid: WHITE for nid in pathway.nodes}
    parent: dict[str, str] = {}

    # Build adjacency list from connections (skip pseudo-nodes like input/output)
    adj: dict[str, list[str]] = {nid: [] for nid in pathway.nodes}
    for conn in pathway.connections:
        # Skip pseudo-nodes (input/output)
        if conn.from_node in PSEUDO_NODES or conn.to_node in PSEUDO_NODES:
            continue
        if conn.from_node in adj and conn.to_node in adj:
            adj[conn.from_node].append(conn.to_node)

    def _reconstruct_cycle(u: str, v: str) -> list[str] | None:
        # Found back-edge u -> v where v is GRAY in current recursion stack.
        # Reconstruct path v -> ... -> u -> v via parent pointers.
        path: list[str] = [v]
        cur = u
        while cur != v:
            path.append(cur)
            if cur not in parent:
                return None
            cur = parent[cur]
        path.append(v)
        path.reverse()
        return path

    def dfs(node: str) -> list[str] | None:
        color[node] = GRAY
        for neighbor in adj.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                return _reconstruct_cycle(node, neighbor)
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
        color[node] = BLACK
        return None

    for node in pathway.nodes:
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def _has_cycle(pathway: "Pathway") -> bool:
    """Detect cycles in the pathway graph."""
    return find_cycle(pathway) is not None


def validate_node_config(
    node_type: str, config: dict[str, Any], ctx: "Context"
) -> ValidationResult:
    """Validate a node configuration without a full pathway.

    Useful for validating node config in Studio UI before adding to pathway.

    Args:
        node_type: Node type string (e.g., "llm", "tool")
        config: Node configuration dict
        ctx: Execution context

    Returns:
        ValidationResult
    """
    from pathway_engine.domain.nodes.registry import NodeTypeRegistry

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    # Get node type spec
    spec = NodeTypeRegistry.get(node_type)
    if spec is None:
        errors.append(
            ValidationIssue(
                code="UNKNOWN_NODE_TYPE",
                message=f"Unknown node type: {node_type}",
                severity="error",
            )
        )
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Try to instantiate the node to validate config
    try:
        node = spec.node_class(
            id="validation_check",
            **config,
        )

        # Run node-specific validation
        node_errors, node_warnings = _validate_node(node, ctx)
        errors.extend(node_errors)
        warnings.extend(node_warnings)

    except Exception as e:
        errors.append(
            ValidationIssue(
                code="INVALID_CONFIG",
                message=f"Invalid configuration: {e}",
                severity="error",
            )
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "validate_pathway",
    "validate_node_config",
]
