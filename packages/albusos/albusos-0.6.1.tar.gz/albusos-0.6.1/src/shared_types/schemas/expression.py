"""Typed Expression Wrapper (shared schema).

This is the schema/grammar layer - it defines how expressions look on disk/wire.
The evaluation primitives live alongside the schema here (safe_expr) for parity across
runtime and Studio validation.
"""

from __future__ import annotations

import ast
from typing import Any, Literal

from pydantic import BaseModel, Field

from shared_types.expressions.safe_expr import (
    SafeExpressionError,
    safe_eval,
    safe_eval_bool,
    safe_expr_parse,
)

ExpressionLanguage = Literal["safe_expr_v1"]
ExpressionExpectedType = Literal["any", "bool", "string", "number", "json"]
ExpressionFailurePolicy = Literal["fail_open", "fail_closed"]

# Named contexts give expressions a stable "shape" (allowed variables + default failure semantics).
ExpressionContextId = Literal[
    "generic_v1", "router_v1", "loop_v1", "verifier_v1", "agent_guard_v1"
]


_CTX_ALLOWED_NAMES: dict[str, set[str]] = {
    "generic_v1": set(),
    # Router condition: safe_expr evaluated with env {"data": ...}
    "router_v1": {"data"},
    # Loop condition: safe_expr evaluated with env {"value": ..., "iteration": ...}
    "loop_v1": {"value", "iteration"},
    # Verifier expression: default to {"data": ...} for convenience
    "verifier_v1": {"data"},
    # Agent guard: make data sources explicit and stable
    "agent_guard_v1": {"context", "payload"},
}

_CTX_DEFAULT_FAILURE: dict[str, ExpressionFailurePolicy] = {
    "generic_v1": "fail_closed",
    "router_v1": "fail_open",
    "loop_v1": "fail_open",
    "verifier_v1": "fail_closed",
    "agent_guard_v1": "fail_closed",
}


class ExpressionV1(BaseModel):
    """A typed, versioned expression wrapper."""

    model_config = {"extra": "forbid"}

    language: ExpressionLanguage = "safe_expr_v1"
    context_id: ExpressionContextId = "generic_v1"
    source: str
    expected_type: ExpressionExpectedType = "any"
    # If None, use context default (router/loop fail-open; verifier fail-closed).
    failure_policy: ExpressionFailurePolicy | None = None
    # Optional tags for internal analytics / learning features.
    tags: dict[str, Any] = Field(default_factory=dict)

    def effective_failure_policy(self) -> ExpressionFailurePolicy:
        return self.failure_policy or _CTX_DEFAULT_FAILURE.get(
            str(self.context_id), "fail_closed"
        )


class ExpressionValidationResult(BaseModel):
    model_config = {"extra": "forbid"}

    ok: bool
    error: str | None = None
    detail: str | None = None
    referenced_names: list[str] = Field(default_factory=list)
    normalized_source: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)


def _extract_names(tree: ast.AST) -> list[str]:
    names: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.id, str):
            names.add(n.id)
    return sorted(names)


def _extract_features(tree: ast.AST) -> dict[str, Any]:
    """Deterministic feature extraction for learning/telemetry (no side effects)."""
    nodes = list(ast.walk(tree))
    node_count = len(nodes)
    # Operator counts
    ops: dict[str, int] = {}
    for n in nodes:
        if isinstance(n, ast.BinOp):
            k = f"binop:{n.op.__class__.__name__}"
            ops[k] = ops.get(k, 0) + 1
        elif isinstance(n, ast.UnaryOp):
            k = f"unaryop:{n.op.__class__.__name__}"
            ops[k] = ops.get(k, 0) + 1
        elif isinstance(n, ast.BoolOp):
            k = f"boolop:{n.op.__class__.__name__}"
            ops[k] = ops.get(k, 0) + 1
        elif isinstance(n, ast.Compare):
            for op in n.ops:
                k = f"cmpop:{op.__class__.__name__}"
                ops[k] = ops.get(k, 0) + 1
        elif isinstance(n, ast.Subscript):
            ops["subscript"] = ops.get("subscript", 0) + 1
        elif isinstance(n, ast.IfExp):
            ops["ifexp"] = ops.get("ifexp", 0) + 1
    return {"node_count": node_count, "ops": dict(sorted(ops.items()))}


def validate_expression_v1(expr: ExpressionV1) -> ExpressionValidationResult:
    """Validate safety + allowed variable names, and return a canonicalized form."""

    if expr.language != "safe_expr_v1":
        return ExpressionValidationResult(
            ok=False, error="unsupported_language", detail=str(expr.language)
        )

    try:
        tree = safe_expr_parse(expr.source)
    except SafeExpressionError as e:
        return ExpressionValidationResult(
            ok=False, error="invalid_expression", detail=str(e)
        )

    referenced = _extract_names(tree)
    features = _extract_features(tree)
    allowed = _CTX_ALLOWED_NAMES.get(str(expr.context_id), set())
    if allowed:
        unknown = sorted([n for n in referenced if n not in allowed])
        if unknown:
            return ExpressionValidationResult(
                ok=False,
                error="unknown_names",
                detail=f"unknown={unknown}, allowed={sorted(allowed)}",
                referenced_names=referenced,
                features=features,
            )

    normalized = None
    try:
        normalized = (
            ast.unparse(tree.body)
            if hasattr(ast, "unparse") and isinstance(tree, ast.Expression)
            else None
        )
    except Exception:
        normalized = None

    return ExpressionValidationResult(
        ok=True,
        referenced_names=referenced,
        normalized_source=normalized,
        features=features,
    )


def eval_expression_v1(expr: ExpressionV1, *, env: dict[str, Any]) -> Any:
    """Evaluate the expression, enforcing failure policy and expected type best-effort."""

    # Validate once per call (deterministic + allows Studio/runtime parity).
    v = validate_expression_v1(expr)
    if not v.ok:
        if expr.effective_failure_policy() == "fail_open":
            return None
        raise SafeExpressionError(f"{v.error}:{v.detail}")

    if expr.expected_type == "bool":
        out = safe_eval_bool(expr.source, env=env)
        return bool(out)

    out = safe_eval(expr.source, env=env)

    # Optional: coerce to declared type (best-effort; fail according to policy).
    try:
        if expr.expected_type == "string":
            return str(out)
        if expr.expected_type == "number":
            return float(out)
        return out
    except Exception as e:
        if expr.effective_failure_policy() == "fail_open":
            return None
        raise SafeExpressionError(f"type_coercion_failed:{e}") from e


__all__ = [
    "ExpressionContextId",
    "ExpressionExpectedType",
    "ExpressionFailurePolicy",
    "ExpressionLanguage",
    "ExpressionV1",
    "ExpressionValidationResult",
    "eval_expression_v1",
    "validate_expression_v1",
]
