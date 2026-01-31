"""pathway_engine.nodes - Node classes with embedded compute.

Each node knows how to execute itself. No resolvers needed.
Nodes return TYPED outputs from pathway_engine.domain.models.
"""

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.nodes.core import (
    LLMNode,
    ToolNode,
    CodeNode,
    CodeGeneratorNode,
    DebugNode,
    TransformNode,
    RouterNode,
    GateNode,
    MemoryReadNode,
    MemoryWriteNode,
)

# Composition nodes
from pathway_engine.domain.nodes.composition import (
    SubPathwayNode,
    MapNode,
    ConditionalNode,
    RouteNode,
    RetryNode,
    TimeoutNode,
    FallbackNode,
)

# Tool calling nodes
from pathway_engine.domain.nodes.tool_calling import (
    ToolCallingLLMNode,
    ToolExecutorNode,
)

# Agent loop node
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode, AgentState

# Streaming / observation nodes
from pathway_engine.domain.nodes.streaming import (
    EventSourceNode,
    IntrospectionNode,
)


# Vision nodes
from pathway_engine.domain.nodes.vision import (
    VisionNode,
    ImageGenNode,
)

# Speech nodes
from pathway_engine.domain.nodes.speech import (
    TTSNode,
    ASRNode,
)

# DTOs from models/ (re-export for convenience)
from pathway_engine.domain.models.tool import (
    ToolCall,
    ToolResult,
    ToolCallPlan,
    ToolExecutionResult,
)
from pathway_engine.domain.models.tool_calling_llm import (
    ToolCallingLLMOutput,
)
from pathway_engine.domain.nodes.execution import (
    PathwayRecord,
    PathwayStatus,
    PathwayEvent,
    PathwayMetrics,
)

__all__ = [
    # Base
    "NodeBase",
    # Compute nodes
    "LLMNode",
    "ToolNode",
    "CodeNode",
    "CodeGeneratorNode",
    "DebugNode",
    "TransformNode",
    # Control flow nodes
    "RouterNode",
    "GateNode",
    # Memory nodes
    "MemoryReadNode",
    "MemoryWriteNode",
    # Composition nodes
    "SubPathwayNode",
    "MapNode",
    "ConditionalNode",
    "RouteNode",
    "RetryNode",
    "TimeoutNode",
    "FallbackNode",
    # Tool calling nodes
    "ToolCallingLLMNode",
    "ToolExecutorNode",
    # Agent loop
    "AgentLoopNode",
    "AgentState",
    # Streaming / observation nodes
    "EventSourceNode",
    "IntrospectionNode",
    # Vision nodes
    "VisionNode",
    "ImageGenNode",
    # Speech nodes
    "TTSNode",
    "ASRNode",
    # Tool DTOs (from models/)
    "ToolCall",
    "ToolResult",
    "ToolCallPlan",
    "ToolExecutionResult",
    "ToolCallingLLMOutput",
    # Execution records
    "PathwayRecord",
    "PathwayStatus",
    "PathwayEvent",
    "PathwayMetrics",
]
