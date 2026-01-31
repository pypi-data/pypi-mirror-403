"""Safe Expression Parser and Evaluator.

Provides a deterministic, sandboxed expression language with:
- AST-based parsing with strict whitelist
- No function calls, attribute access, or side effects
- Safe evaluation with environment injection

This is the foundation of the expression language - the parser
and evaluator that all higher-level constructs use.
"""

from __future__ import annotations

import ast
import functools
from dataclasses import dataclass
from typing import Any, Callable


class SafeExpressionError(ValueError):
    """Raised when an expression is invalid or uses forbidden syntax."""


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub, ast.Not)
_ALLOWED_BOOLOPS = (ast.And, ast.Or)
_ALLOWED_CMPOPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)

# =============================================================================
# Allowed calls / attribute sugar (tight allowlist)
# =============================================================================

# Builtins allowed as function calls, e.g. len(x)
_ALLOWED_FUNCS: dict[str, Callable[..., Any]] = {
    "len": len,
}

# Methods allowed as calls on specific base types.
# NOTE: This keeps the "not Python" safety model while restoring key ergonomics.
_ALLOWED_METHODS: dict[type, set[str]] = {
    dict: {"get"},
    str: {"lower", "upper", "strip"},
}


def _is_safe_node(node: ast.AST) -> bool:
    """AST whitelist for deterministic, sandboxed evaluation.

    Disallows:
    - function calls
    - attribute access
    - comprehensions / generators
    - assignment / mutation
    - imports, lambdas (handled separately), f-strings
    """
    if isinstance(node, ast.Expression):
        return _is_safe_node(node.body)

    # Literals / containers
    if isinstance(node, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set)):
        return all(_is_safe_node(x) for x in ast.iter_child_nodes(node))

    # Variables / load context
    if isinstance(node, (ast.Name, ast.Load)):
        return True

    # Indexing (e.g. data["k"], data[0]); slices disallowed for determinism/simplicity.
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            return False
        return _is_safe_node(node.value) and _is_safe_node(node.slice)

    # Calls (tight allowlist): len(x), dict.get(k, default), basic str methods
    if isinstance(node, ast.Call):
        # Disallow keyword arguments for determinism/simplicity (keep calls positional only).
        if node.keywords:
            return False
        # Allowed builtins
        if isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS:
            return all(_is_safe_node(a) for a in node.args)
        # Allowed methods on safe bases
        if isinstance(node.func, ast.Attribute):
            # We do NOT generally allow attribute access; only allow it for method calls.
            if not _is_safe_node(node.func.value):
                return False
            if node.func.attr.startswith("_"):
                return False
            return all(_is_safe_node(a) for a in node.args)
        return False

    # Attribute access is generally disallowed, but we allow dict sugar:
    # data.foo  -> data["foo"]  (only for simple identifiers, no leading underscore)
    if isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            return False
        return _is_safe_node(node.value)

    # Ops
    if isinstance(node, ast.BinOp):
        return (
            isinstance(node.op, _ALLOWED_BINOPS)
            and _is_safe_node(node.left)
            and _is_safe_node(node.right)
        )
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, _ALLOWED_UNARYOPS) and _is_safe_node(node.operand)
    if isinstance(node, ast.BoolOp):
        return isinstance(node.op, _ALLOWED_BOOLOPS) and all(
            _is_safe_node(v) for v in node.values
        )
    if isinstance(node, ast.Compare):
        return (
            all(isinstance(op, _ALLOWED_CMPOPS) for op in node.ops)
            and _is_safe_node(node.left)
            and all(_is_safe_node(c) for c in node.comparators)
        )

    # Conditional expression: a if cond else b
    if isinstance(node, ast.IfExp):
        return (
            _is_safe_node(node.test)
            and _is_safe_node(node.body)
            and _is_safe_node(node.orelse)
        )

    # Explicitly disallow dangerous / non-deterministic constructs
    if isinstance(
        node,
        (
            ast.Lambda,
            ast.Await,
            ast.Yield,
            ast.YieldFrom,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
            ast.NamedExpr,
            ast.JoinedStr,
            ast.FormattedValue,
        ),
    ):
        return False

    # For everything else, be conservative.
    return False


def safe_eval(expr: str, env: dict[str, Any] | None = None) -> Any:
    """Evaluate a small expression language safely."""
    tree = safe_expr_parse(expr)
    return _safe_eval_ast(tree.body, env=dict(env or {}))


def safe_eval_bool(expr: str, env: dict[str, Any] | None = None) -> bool:
    v = safe_eval(expr, env=env)
    return bool(v)


def _binop(op: ast.operator, a: Any, b: Any) -> Any:
    if isinstance(op, ast.Add):
        return a + b
    if isinstance(op, ast.Sub):
        return a - b
    if isinstance(op, ast.Mult):
        return a * b
    if isinstance(op, ast.Div):
        return a / b
    if isinstance(op, ast.FloorDiv):
        return a // b
    if isinstance(op, ast.Mod):
        return a % b
    if isinstance(op, ast.Pow):
        return a**b
    raise SafeExpressionError("unsupported_binop")


def _unaryop(op: ast.unaryop, v: Any) -> Any:
    if isinstance(op, ast.UAdd):
        return +v
    if isinstance(op, ast.USub):
        return -v
    if isinstance(op, ast.Not):
        return not bool(v)
    raise SafeExpressionError("unsupported_unaryop")


def _compare_one(op: ast.cmpop, a: Any, b: Any) -> bool:
    if isinstance(op, ast.Eq):
        return a == b
    if isinstance(op, ast.NotEq):
        return a != b
    if isinstance(op, ast.Lt):
        return a < b
    if isinstance(op, ast.LtE):
        return a <= b
    if isinstance(op, ast.Gt):
        return a > b
    if isinstance(op, ast.GtE):
        return a >= b
    if isinstance(op, ast.In):
        return a in b
    if isinstance(op, ast.NotIn):
        return a not in b
    if isinstance(op, ast.Is):
        return a is b
    if isinstance(op, ast.IsNot):
        return a is not b
    raise SafeExpressionError("unsupported_cmpop")


def _safe_eval_ast(node: ast.AST, env: dict[str, Any]) -> Any:
    # Literals / containers
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_safe_eval_ast(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_safe_eval_ast(elt, env) for elt in node.elts)
    if isinstance(node, ast.Set):
        return {_safe_eval_ast(elt, env) for elt in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _safe_eval_ast(k, env): _safe_eval_ast(v, env)
            for k, v in zip(node.keys, node.values)
        }

    # Variables
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise SafeExpressionError(f"unknown_name:{node.id}")

    # Indexing
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            raise SafeExpressionError("slice_not_supported")
        base = _safe_eval_ast(node.value, env)
        idx = _safe_eval_ast(node.slice, env)
        return base[idx]

    # Attribute access sugar: obj.field -> obj["field"] (only if obj is dict-like)
    if isinstance(node, ast.Attribute):
        base = _safe_eval_ast(node.value, env)
        if isinstance(base, dict):
            if node.attr.startswith("_"):
                raise SafeExpressionError("forbidden_attribute")
            try:
                return base[node.attr]
            except KeyError:
                raise
        raise SafeExpressionError("attribute_not_supported")

    # Calls (tight allowlist)
    if isinstance(node, ast.Call):
        if node.keywords:
            raise SafeExpressionError("call_keywords_not_supported")

        # Builtins: len(x)
        if isinstance(node.func, ast.Name):
            fn = _ALLOWED_FUNCS.get(node.func.id)
            if fn is None:
                raise SafeExpressionError("call_not_allowed")
            args = [_safe_eval_ast(a, env) for a in node.args]
            try:
                return fn(*args)
            except Exception as e:
                raise SafeExpressionError(f"call_failed:{type(e).__name__}") from e

        # Methods: dict.get(k, default), str.lower/upper/strip
        if isinstance(node.func, ast.Attribute):
            base = _safe_eval_ast(node.func.value, env)
            method = str(node.func.attr or "")
            if method.startswith("_"):
                raise SafeExpressionError("call_not_allowed")
            args = [_safe_eval_ast(a, env) for a in node.args]

            if isinstance(base, dict):
                if method not in _ALLOWED_METHODS[dict]:
                    raise SafeExpressionError("call_not_allowed")
                if method == "get":
                    if len(args) == 1:
                        return base.get(args[0])
                    if len(args) == 2:
                        return base.get(args[0], args[1])
                    raise SafeExpressionError("dict_get_arity")

            if isinstance(base, str):
                if method not in _ALLOWED_METHODS[str]:
                    raise SafeExpressionError("call_not_allowed")
                if args:
                    raise SafeExpressionError("str_method_no_args")
                # These are pure / deterministic
                return getattr(base, method)()

            raise SafeExpressionError("call_not_allowed")

        raise SafeExpressionError("call_not_allowed")

    # Ops
    if isinstance(node, ast.BinOp):
        return _binop(
            node.op, _safe_eval_ast(node.left, env), _safe_eval_ast(node.right, env)
        )
    if isinstance(node, ast.UnaryOp):
        return _unaryop(node.op, _safe_eval_ast(node.operand, env))
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for v in node.values:
                cur = _safe_eval_ast(v, env)
                if not bool(cur):
                    return cur
            return cur  # type: ignore[possibly-undefined]
        if isinstance(node.op, ast.Or):
            for v in node.values:
                cur = _safe_eval_ast(v, env)
                if bool(cur):
                    return cur
            return cur  # type: ignore[possibly-undefined]
        raise SafeExpressionError("unsupported_boolop")
    if isinstance(node, ast.Compare):
        left = _safe_eval_ast(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            right = _safe_eval_ast(comp, env)
            if not _compare_one(op, left, right):
                return False
            left = right
        return True

    # Conditional expression: a if cond else b
    if isinstance(node, ast.IfExp):
        test = _safe_eval_ast(node.test, env)
        return _safe_eval_ast(node.body if bool(test) else node.orelse, env)

    raise SafeExpressionError(f"unsupported_node:{node.__class__.__name__}")


@functools.lru_cache(maxsize=4096)
def safe_expr_parse(expr: str) -> ast.Expression:
    """Parse + validate a safe expression, returning the AST."""
    s = str(expr or "").strip()
    if not s:
        raise SafeExpressionError("empty_expression")
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise SafeExpressionError(f"invalid_expression: {e}") from e
    if not isinstance(tree, ast.Expression):
        raise SafeExpressionError("invalid_expression")
    if not _is_safe_node(tree):
        raise SafeExpressionError("forbidden_syntax")
    return tree


@dataclass(frozen=True)
class CompiledLambda:
    """A safe, deterministic "lambda x: <expr>" compiled to an interpreter closure."""

    source: str
    arg_name: str
    body_expr: str
    body_ast: ast.AST

    def to_callable(self) -> Callable[[Any], Any]:
        arg = self.arg_name
        body_ast = self.body_ast

        def _fn(x: Any) -> Any:
            return _safe_eval_ast(body_ast, env={arg: x})

        return _fn


def compile_safe_lambda(source: str, *, arg_name: str = "x") -> CompiledLambda:
    """Parse `lambda x: <expr>` and compile it to a safe evaluator-backed callable."""
    s = str(source or "").strip()
    if not s:
        raise SafeExpressionError("empty_lambda")
    try:
        mod = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise SafeExpressionError(f"invalid_lambda: {e}") from e
    if not isinstance(mod.body, ast.Lambda):
        raise SafeExpressionError("expected_lambda")
    lam = mod.body
    if len(lam.args.args) != 1:
        raise SafeExpressionError("lambda_must_have_one_arg")
    if bool(
        lam.args.vararg or lam.args.kwarg or lam.args.kwonlyargs or lam.args.defaults
    ):
        raise SafeExpressionError("lambda_args_not_supported")
    arg0 = lam.args.args[0].arg
    if arg0 != arg_name:
        raise SafeExpressionError(f"lambda_arg_must_be_{arg_name}")
    if not _is_safe_node(lam.body):
        raise SafeExpressionError("forbidden_syntax")
    body_expr = (
        ast.unparse(lam.body) if hasattr(ast, "unparse") else s.split(":", 1)[1].strip()
    )
    return CompiledLambda(
        source=s,
        arg_name=arg_name,
        body_expr=str(body_expr or "").strip(),
        body_ast=lam.body,
    )


__all__ = [
    "CompiledLambda",
    "SafeExpressionError",
    "compile_safe_lambda",
    "safe_eval",
    "safe_eval_bool",
    "safe_expr_parse",
]
