"""shared_types - tiny, dependency-minimal shared contracts.

Purpose:
- Hold lightweight schema/types that multiple layers share without importing each other.
- Must stay independently usable (no albus/stdlib/pathway_engine imports).

Today:
- Expression schema + safe expression grammar helpers.
"""

from shared_types.expressions.safe_expr import (
    CompiledLambda,
    SafeExpressionError,
    compile_safe_lambda,
    safe_eval,
    safe_eval_bool,
    safe_expr_parse,
)
from shared_types.schemas.expression import (
    ExpressionContextId,
    ExpressionExpectedType,
    ExpressionFailurePolicy,
    ExpressionLanguage,
    ExpressionV1,
    ExpressionValidationResult,
    eval_expression_v1,
    validate_expression_v1,
)

__all__ = [
    # safe_expr
    "SafeExpressionError",
    "safe_expr_parse",
    "safe_eval",
    "safe_eval_bool",
    "CompiledLambda",
    "compile_safe_lambda",
    # expression schema
    "ExpressionLanguage",
    "ExpressionExpectedType",
    "ExpressionFailurePolicy",
    "ExpressionContextId",
    "ExpressionV1",
    "ExpressionValidationResult",
    "validate_expression_v1",
    "eval_expression_v1",
]
