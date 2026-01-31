"""pathway_engine - Pathway runtime kernel (IR + executor).

This package is the **runtime**, not the authoring language.

- Authoring: Direct Pathway construction via Pathway, Node, and Connection classes
- Standard library tools: `stdlib`

`pathway_engine` provides:
- `Pathway` IR (nodes + edges + gates + loops)
- typed node classes (LLM/tool/router/memory/streaming/etc.)
- `PathwayVM` executor (`execute` + `stream_execute`)
"""

from __future__ import annotations

# =============================================================================
# NODES - Classes with embedded compute
# =============================================================================
from pathway_engine.domain.nodes import (
    NodeBase,
    LLMNode,
    ToolNode,
    CodeNode,
    TransformNode,
    RouterNode,
    GateNode,
    MemoryReadNode,
    MemoryWriteNode,
    # Tool calling
    ToolCallingLLMNode,
    ToolExecutorNode,
    ToolCall,
    ToolResult,
    ToolCallPlan,
    ToolExecutionResult,
    # Execution records
    PathwayRecord,
    PathwayStatus,
    PathwayEvent,
    PathwayMetrics,
)

# =============================================================================
# PATHWAY - Graph structure
# =============================================================================
from pathway_engine.domain.pathway import (
    Pathway,
    Connection,
    Gate,
    Loop,
    Signal,
    NodeStatus,
)

# =============================================================================
# CONTEXT - Execution context
# =============================================================================
from pathway_engine.domain.context import Context, ToolHandler

# =============================================================================
# STREAMING NODES - For observe verbs
# =============================================================================
from pathway_engine.domain.nodes.streaming import (
    EventSourceNode,
    IntrospectionNode,
)

# =============================================================================
# STREAMING PRIMITIVES - VM-internal event sources
# =============================================================================
from pathway_engine.domain.streaming import (
    WEBHOOK_BUS,
    WebhookBus,
    STREAMING_HANDLERS,
    get_streaming_handler,
    register_streaming_handler,
)

# =============================================================================
# ACTION NODE - Pack-centric action dispatch
# =============================================================================

# =============================================================================
# TRIGGERS - Event-driven pathway triggers
# =============================================================================
from pathway_engine.domain.trigger import Trigger, TriggerSource
from pathway_engine.domain.trigger_context import (
    TriggerContext,
    ReplyChannel,
)

# =============================================================================
# AGENT - Persistent AI entity with identity, memory, and capabilities
# =============================================================================
from pathway_engine.domain.agent import (
    Agent,
    AgentBuilder,
    agent_builder,
    Skill,
    skill,
    ReasoningMode,
    OrationMode,
    SupervisionMode,
    CognitiveStyle,
    CognitivePresets,
    MemoryScope,
    AgentMemoryConfig,
    AgentCapabilities,
    ProactiveTrigger,
    AgentState,
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

# =============================================================================
# VM - Execution engine
# =============================================================================
from pathway_engine.application.kernel import PathwayVM

# =============================================================================
# TRIGGERS - Event-driven pathway triggers
# =============================================================================
from pathway_engine.application.triggers import (
    TriggerManager,
    TriggerSubscription,
    TriggerError,
)

__all__ = [
    # Compute nodes
    "NodeBase",
    "LLMNode",
    "ToolNode",
    "CodeNode",
    "TransformNode",
    # Control flow nodes
    "RouterNode",
    "GateNode",
    # Memory nodes
    "MemoryReadNode",
    "MemoryWriteNode",
    # Tool calling nodes
    "ToolCallingLLMNode",
    "ToolExecutorNode",
    "ToolCall",
    "ToolResult",
    "ToolCallPlan",
    "ToolExecutionResult",
    # Streaming / observation nodes
    "EventSourceNode",
    "IntrospectionNode",
    # Action node (pack-centric)
    # Pack / Triggers
    "Pack",
    "PackBuilder",
    "Trigger",
    "TriggerSource",
    "TriggerContext",
    "ReplyChannel",
    # Agent
    "Agent",
    "AgentBuilder",
    "agent_builder",
    "Skill",
    "skill",
    "ReasoningMode",
    "OrationMode",
    "SupervisionMode",
    "CognitiveStyle",
    "CognitivePresets",
    "AgentCapabilities",
    "AgentMemoryConfig",
    "AgentState",
    "MemoryScope",
    "ProactiveTrigger",
    # Pathway structure
    "Pathway",
    "Connection",
    "Gate",
    "Loop",
    "Signal",
    "NodeStatus",
    # Context
    "Context",
    "ToolHandler",
    # Execution records
    "PathwayRecord",
    "PathwayStatus",
    "PathwayEvent",
    "PathwayMetrics",
    # Expressions
    "ExpressionV1",
    "ExpressionValidationResult",
    "SafeExpressionError",
    "safe_eval",
    "safe_eval_bool",
    "safe_expr_parse",
    "validate_expression_v1",
    "eval_expression_v1",
    # VM
    "PathwayVM",
    # Dispatchers / Triggers
    "TriggerManager",
    "TriggerSubscription",
    "TriggerError",
    # Streaming primitives
    "WEBHOOK_BUS",
    "WebhookBus",
    "STREAMING_HANDLERS",
    "get_streaming_handler",
    "register_streaming_handler",
]
