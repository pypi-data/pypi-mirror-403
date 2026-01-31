"""Pathway - The execution graph structure.

This module defines:
- Pathway: A graph of nodes and connections (serializable!)
- Connection: Links between nodes
- Signal: Result of node execution
- Gate, Loop: Control flow primitives

Nodes are defined in nodes/core.py (LLMNode, ToolNode, etc.)

Serialization:
    # Pathway to JSON
    pathway = Pathway(id="example", name="Example")
    json_data = pathway.model_dump_json()
    
    # JSON to Pathway
    pathway2 = Pathway.model_validate_json(json_data)
    
    # Execute
    await vm.execute(pathway2, inputs)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, TYPE_CHECKING, Annotated, Union
from uuid import uuid4

from pydantic import BaseModel, Field

# Import node types for discriminated union serialization
# This must be a runtime import (not TYPE_CHECKING) for Pydantic to work
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
from pathway_engine.domain.nodes.composition import (
    SubPathwayNode,
    MapNode,
    ConditionalNode,
    RouteNode,
    RetryNode,
    TimeoutNode,
    FallbackNode,
)
from pathway_engine.domain.nodes.tool_calling import (
    ToolCallingLLMNode,
    ToolExecutorNode,
)
from pathway_engine.domain.nodes.streaming import (
    EventSourceNode,
    IntrospectionNode,
)
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode
from pathway_engine.domain.nodes.vision import VisionNode, ImageGenNode
from pathway_engine.domain.nodes.speech import TTSNode, ASRNode

if TYPE_CHECKING:
    from pathway_engine.domain.nodes.base import NodeBase
    from pathway_engine.domain.schemas.signature import PathwaySignature


# Pseudo-nodes used in connections but not in pathway.nodes
# These represent data flow entry/exit points, not executable nodes.
# All graph algorithms (cycle detection, topological sort) must skip these.
PSEUDO_NODES: frozenset[str] = frozenset({"input", "output"})


def is_real_node(node_id: str, pathway_nodes: dict | None = None) -> bool:
    """Check if a node ID refers to a real executable node.
    
    Args:
        node_id: The node ID to check
        pathway_nodes: Optional dict of pathway nodes for additional validation
        
    Returns:
        True if node_id is a real node (not a pseudo-node)
    """
    if node_id in PSEUDO_NODES:
        return False
    if pathway_nodes is not None:
        return node_id in pathway_nodes
    return True


# Discriminated union of all node types - enables JSON serialization/deserialization
Node = Annotated[
    Union[
        # Compute nodes
        LLMNode,
        ToolNode,
        CodeNode,
        CodeGeneratorNode,
        DebugNode,
        TransformNode,
        # Control flow
        RouterNode,
        GateNode,
        # Memory
        MemoryReadNode,
        MemoryWriteNode,
        # Composition
        SubPathwayNode,
        MapNode,
        ConditionalNode,
        RouteNode,
        RetryNode,
        TimeoutNode,
        FallbackNode,
        # Tool calling
        ToolCallingLLMNode,
        ToolExecutorNode,
        # Agent loop (Claude-like agentic execution)
        AgentLoopNode,
        # Streaming / Observation
        EventSourceNode,
        IntrospectionNode,
        # Pack-centric action dispatch
        # Vision nodes
        VisionNode,
        ImageGenNode,
        # Speech nodes
        TTSNode,
        ASRNode,
    ],
    Field(discriminator="type"),
]


class NodeStatus(Enum):
    """Status of a node execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Signal(BaseModel):
    """Result of a node execution."""

    model_config = {"extra": "allow"}

    value: Any = None
    error: str | None = None
    status: NodeStatus = NodeStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == NodeStatus.COMPLETED and self.error is None


class Connection(BaseModel):
    """Connection between nodes."""

    model_config = {"extra": "allow"}

    from_node: str
    to_node: str
    from_output: str = "output"
    to_input: str = "input"

    def transfer(self, data: Any) -> Any:
        """Transfer data through this connection."""
        return data


class Gate(BaseModel):
    """Conditional flow control - if/else branching.

    Used by GateNode in nodes.py. The VM checks gate conditions
    to determine which nodes to skip.
    """

    model_config = {"extra": "allow"}

    condition: str  # Expression to evaluate
    true_path: str  # Node ID if true
    false_path: str | None = None  # Node ID if false

    def evaluate(self, data: dict[str, Any]) -> str | None:
        """Evaluate condition and return next node ID."""
        from pathway_engine.domain.expressions import safe_eval

        result = safe_eval(self.condition, data)
        if result:
            return self.true_path
        return self.false_path


class Loop(BaseModel):
    """Loop control - iteration."""

    model_config = {"extra": "allow"}

    max_iterations: int = 10
    condition: str  # Expression: (data, iteration) -> continue?
    body_nodes: list[str] = Field(default_factory=list)

    def should_continue(self, data: dict[str, Any], iteration: int) -> bool:
        """Check if loop should continue."""
        if iteration >= self.max_iterations:
            return False
        from pathway_engine.domain.expressions import safe_eval

        return bool(safe_eval(self.condition, {**data, "_iteration": iteration}))


class Pathway(BaseModel):
    """A computation graph - fully serializable.

    A Pathway is:
    - nodes: Dict of node_id -> Node (discriminated union, serializable)
    - connections: List of Connection (data flow between nodes)
    - gates: Conditional flow control
    - loops: Iteration control

    Composition (DSL):
    - pathway >> node: append node to end
    - pathway >> other: chain pathways
    - pathway | other: parallel composition

    Serialization:
    - pathway.model_dump_json() → JSON string
    - Pathway.model_validate_json(json) → Pathway object

    Execution happens in PathwayVM.
    """

    model_config = {"extra": "allow"}

    id: str = Field(default_factory=lambda: f"pathway_{uuid4().hex[:8]}")
    name: str | None = None
    description: str | None = None

    # Discriminated union enables proper JSON serialization/deserialization
    nodes: dict[str, Node] = Field(default_factory=dict)

    connections: list[Connection] = Field(default_factory=list)
    gates: list[Gate] = Field(default_factory=list)
    loops: list[Loop] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Typed I/O contract (optional)
    signature: Any = None  # PathwaySignature

    # Learning configuration (optional)
    learning: Any = None

    # Trigger configuration (optional) - when to auto-run this pathway
    # Examples:
    #   {"type": "timer", "schedule": "0 9 * * *"}  # Daily at 9am
    #   {"type": "webhook", "topic": "github-events"}  # On webhook
    #   {"type": "event", "channel": "user-signup"}  # On internal event
    trigger: dict[str, Any] | None = None

    # =========================================================================
    # ENTRY/EXIT for composition
    # =========================================================================

    @property
    def entry_id(self) -> str:
        """ID of the entry node (first node with no incoming connections)."""
        if not self.nodes:
            raise ValueError("Pathway has no nodes")

        has_incoming = {conn.to_node for conn in self.connections}
        entry_candidates = [nid for nid in self.nodes if nid not in has_incoming]

        if entry_candidates:
            return entry_candidates[0]
        return next(iter(self.nodes.keys()))

    @property
    def exit_id(self) -> str:
        """ID of the exit node (last node with no outgoing connections)."""
        if not self.nodes:
            raise ValueError("Pathway has no nodes")

        has_outgoing = {conn.from_node for conn in self.connections}
        exit_candidates = [nid for nid in self.nodes if nid not in has_outgoing]

        if exit_candidates:
            return exit_candidates[-1]
        return list(self.nodes.keys())[-1]

    # =========================================================================
    # COMPOSITION OPERATORS
    # =========================================================================

    def __rshift__(self, other: "NodeBase | Pathway") -> "Pathway":
        """Chain: self >> other"""
        if isinstance(other, Pathway):
            return Pathway(
                id=f"chain_{uuid4().hex[:6]}",
                nodes={**self.nodes, **other.nodes},
                connections=[
                    *self.connections,
                    Connection(from_node=self.exit_id, to_node=other.entry_id),
                    *other.connections,
                ],
                gates=[*self.gates, *other.gates],
                loops=[*self.loops, *other.loops],
                metadata={**self.metadata, **other.metadata},
            )

        # It's a node
        return Pathway(
            id=f"chain_{uuid4().hex[:6]}",
            nodes={**self.nodes, other.id: other},
            connections=[
                *self.connections,
                Connection(from_node=self.exit_id, to_node=other.id),
            ],
            gates=list(self.gates),
            loops=list(self.loops),
            metadata=dict(self.metadata),
        )

    def __or__(self, other: "Pathway") -> "Pathway":
        """Parallel: self | other"""
        if not isinstance(other, Pathway):
            raise TypeError(f"Cannot parallel compose with {type(other)}")

        parallel_group = self.metadata.get("parallel_group", list(self.nodes.keys()))
        other_group = other.metadata.get("parallel_group", list(other.nodes.keys()))

        return Pathway(
            id=f"parallel_{uuid4().hex[:6]}",
            nodes={**self.nodes, **other.nodes},
            connections=[*self.connections, *other.connections],
            gates=[*self.gates, *other.gates],
            loops=[*self.loops, *other.loops],
            metadata={
                **self.metadata,
                **other.metadata,
                "parallel_group": [*parallel_group, *other_group],
            },
        )

    # =========================================================================
    # BUILDER METHODS
    # =========================================================================

    def add_node(self, node: "NodeBase") -> "Pathway":
        """Add a node to this pathway."""
        self.nodes[node.id] = node  # type: ignore
        return self

    def connect(self, from_node: str, to_node: str) -> "Pathway":
        """Connect two nodes."""
        self.connections.append(Connection(from_node=from_node, to_node=to_node))
        return self

    def add_gate(self, gate: Gate) -> "Pathway":
        """Add conditional flow control."""
        self.gates.append(gate)
        return self


__all__ = [
    "Connection",
    "Gate",
    "Loop",
    "Node",
    "NodeStatus",
    "Pathway",
    "PSEUDO_NODES",
    "Signal",
    "is_real_node",
]
