"""pathway_engine.expressions - Expression schema and evaluation.

The versioned schema types (ExpressionV1, etc.) are defined here.
These import the shared evaluation primitives from `shared_types`.
"""

# Re-export the shared expression schema + eval functions
from shared_types import (
    ExpressionContextId,
    ExpressionExpectedType,
    ExpressionFailurePolicy,
    ExpressionLanguage,
    ExpressionV1,
    ExpressionValidationResult,
    eval_expression_v1,
    validate_expression_v1,
)
from shared_types import (
    CompiledLambda,
    SafeExpressionError,
    compile_safe_lambda,
    safe_eval,
    safe_eval_bool,
    safe_expr_parse,
)

__all__ = [
    # Schema types (defined in pathway_engine)
    "ExpressionContextId",
    "ExpressionExpectedType",
    "ExpressionFailurePolicy",
    "ExpressionLanguage",
    "ExpressionV1",
    "ExpressionValidationResult",
    "eval_expression_v1",
    "validate_expression_v1",
    # Pure eval from pathway_engine (re-exported)
    "CompiledLambda",
    "SafeExpressionError",
    "compile_safe_lambda",
    "safe_eval",
    "safe_eval_bool",
    "safe_expr_parse",
]
