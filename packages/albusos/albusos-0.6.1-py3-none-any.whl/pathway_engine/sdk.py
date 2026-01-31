"""pathway_engine.sdk - Small, stable runtime kernel surface.

`pathway_engine` top-level already re-exports a curated public API. This module
exists as an explicit SDK import path, and to make it easy to keep a short,
intentional surface for downstream callers.
"""

from __future__ import annotations

# =============================================================================
# VM - Execution engine
# =============================================================================
from pathway_engine.application.kernel import PathwayVM

# =============================================================================
# CONTEXT - Execution context
# =============================================================================
from pathway_engine.domain.context import Context, ToolHandler

# =============================================================================
# NODES - Classes with embedded compute
# =============================================================================
from pathway_engine.domain.nodes import (
    CodeNode,
    GateNode,
    LLMNode,
    MemoryReadNode,
    MemoryWriteNode,
    NodeBase,
    PathwayEvent,
    PathwayMetrics,
    PathwayRecord,
    PathwayStatus,
    RouterNode,
    ToolCall,
    ToolCallingLLMNode,
    ToolCallPlan,
    ToolExecutionResult,
    ToolExecutorNode,
    ToolNode,
    ToolResult,
    TransformNode,
)

# =============================================================================
# STREAMING NODES - For observe verbs
# =============================================================================
from pathway_engine.domain.nodes.streaming import EventSourceNode, IntrospectionNode

# =============================================================================
# PATHWAY - Graph structure
# =============================================================================
from pathway_engine.domain.pathway import (
    Connection,
    Gate,
    Loop,
    NodeStatus,
    Pathway,
    Signal,
)

# =============================================================================
# EXPRESSIONS - Safe evaluation (shared)
# =============================================================================
from shared_types import (
    ExpressionV1,
    ExpressionValidationResult,
    SafeExpressionError,
    eval_expression_v1,
    safe_eval,
    safe_eval_bool,
    safe_expr_parse,
    validate_expression_v1,
)

__all__ = [
    "CodeNode",
    "Connection",
    # Context
    "Context",
    # Streaming / observation nodes
    "EventSourceNode",
    # Expressions
    "ExpressionV1",
    "ExpressionValidationResult",
    "Gate",
    "GateNode",
    "IntrospectionNode",
    "LLMNode",
    "Loop",
    # Memory nodes
    "MemoryReadNode",
    "MemoryWriteNode",
    # Compute nodes
    "NodeBase",
    "NodeStatus",
    # Pathway structure
    "Pathway",
    "PathwayEvent",
    "PathwayMetrics",
    # Execution records
    "PathwayRecord",
    "PathwayStatus",
    # VM
    "PathwayVM",
    # Control flow nodes
    "RouterNode",
    "SafeExpressionError",
    "Signal",
    "ToolCall",
    "ToolCallPlan",
    # Tool calling nodes
    "ToolCallingLLMNode",
    "ToolExecutionResult",
    "ToolExecutorNode",
    "ToolHandler",
    "ToolNode",
    "ToolResult",
    "TransformNode",
    "eval_expression_v1",
    "safe_eval",
    "safe_eval_bool",
    "safe_expr_parse",
    "validate_expression_v1",
]
