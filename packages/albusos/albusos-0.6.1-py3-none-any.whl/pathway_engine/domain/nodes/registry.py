"""Node Type Registry - Metadata and JSON Schema for all node types.

This registry enables:
- Studio UI to know what nodes are available
- JSON Schema validation for node configurations
- Auto-generated documentation
- Type-safe node creation via API

Usage:
    from pathway_engine.domain.nodes.registry import NodeTypeRegistry, register_builtin_node_types
    
    register_builtin_node_types()
    
    # Get all node types
    for spec in NodeTypeRegistry.list_all():
        print(f"{spec.type}: {spec.name}")
    
    # Get JSON Schema for a node type
    spec = NodeTypeRegistry.get("llm")
    schema = spec.to_config_schema()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


@dataclass
class PortSpec:
    """Specification for a node input or output port."""

    name: str
    type: str  # "any", "string", "number", "boolean", "array", "object"
    required: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class NodeExample:
    """Example configuration for a node type."""

    name: str
    description: str
    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
        }


@dataclass
class NodeTypeSpec:
    """Complete specification for a node type."""

    type: str
    name: str
    description: str
    category: str  # "compute", "control", "memory", "composition", "streaming", "agent"
    node_class: Type["BaseModel"]

    # Port specifications
    inputs: list[PortSpec] = field(default_factory=list)
    outputs: list[PortSpec] = field(default_factory=list)

    # Examples for documentation/templates
    examples: list[NodeExample] = field(default_factory=list)

    # Fields to exclude from config schema (identity fields)
    _identity_fields: tuple[str, ...] = ("id", "type", "name", "description")

    def to_config_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for this node type's configuration.

        Extracts config-relevant fields from the Pydantic model schema,
        excluding identity fields (id, type, name, description).
        """
        full_schema = self.node_class.model_json_schema()

        properties = {}
        required = []

        for field_name, field_info in full_schema.get("properties", {}).items():
            if field_name in self._identity_fields:
                continue  # Skip identity fields

            # Copy field schema
            properties[field_name] = field_info

            # Check if required
            if field_name in full_schema.get("required", []):
                required.append(field_name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        # Include definitions if present (for nested types)
        if "$defs" in full_schema:
            schema["$defs"] = full_schema["$defs"]

        return schema

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response format."""
        return {
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "config_schema": self.to_config_schema(),
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "examples": [e.to_dict() for e in self.examples],
        }


class NodeTypeRegistry:
    """Registry of all available node types.

    This is the single source of truth for what nodes exist and how
    to configure them. Studio uses this to populate the node catalog.
    """

    _types: dict[str, NodeTypeSpec] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, spec: NodeTypeSpec) -> None:
        """Register a node type specification."""
        cls._types[spec.type] = spec

    @classmethod
    def get(cls, node_type: str) -> NodeTypeSpec | None:
        """Get specification for a node type."""
        cls._ensure_initialized()
        return cls._types.get(node_type)

    @classmethod
    def list_all(cls) -> list[NodeTypeSpec]:
        """List all registered node types."""
        cls._ensure_initialized()
        return list(cls._types.values())

    @classmethod
    def by_category(cls, category: str) -> list[NodeTypeSpec]:
        """List node types in a specific category."""
        cls._ensure_initialized()
        return [s for s in cls._types.values() if s.category == category]

    @classmethod
    def categories(cls) -> list[str]:
        """List all categories."""
        cls._ensure_initialized()
        return sorted(set(s.category for s in cls._types.values()))

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure built-in types are registered."""
        if not cls._initialized:
            register_builtin_node_types()
            cls._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset registry (for testing)."""
        cls._types = {}
        cls._initialized = False


def register_builtin_node_types() -> None:
    """Register all built-in node types with their specifications."""
    from pathway_engine.domain.nodes import (
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
        AgentLoopNode,
        MapNode,
        RetryNode,
        TimeoutNode,
        FallbackNode,
        EventSourceNode,
        IntrospectionNode,
        ToolCallingLLMNode,
        ToolExecutorNode,
        SubPathwayNode,
        ConditionalNode,
        RouteNode,
    )

    # =========================================================================
    # COMPUTE NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="llm",
            name="LLM Node",
            description="Call a language model to generate text. Supports templating with {{variable}} syntax in prompts.",
            category="compute",
            node_class=LLMNode,
            inputs=[
                PortSpec("input", "any", False, "Input data for prompt templating"),
            ],
            outputs=[
                PortSpec("response", "string", True, "Generated text response"),
                PortSpec("model", "string", True, "Model that was used"),
                PortSpec("usage", "object", False, "Token usage statistics"),
                PortSpec(
                    "metadata",
                    "object",
                    False,
                    "Additional metadata including parsed JSON",
                ),
            ],
            examples=[
                NodeExample(
                    name="Summarize",
                    description="Summarize input text",
                    config={
                        "prompt": "Summarize the following:\n\n{{input}}",
                        "model": "gpt-4o",
                    },
                ),
                NodeExample(
                    name="JSON Output",
                    description="Generate structured JSON output",
                    config={
                        "prompt": "Extract entities from: {{input}}",
                        "model": "gpt-4o",
                        "response_format": "json",
                        "json_schema": {
                            "type": "object",
                            "properties": {
                                "entities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                }
                            },
                        },
                    },
                ),
                NodeExample(
                    name="Vision OCR",
                    description="Extract text from images using vision models",
                    config={
                        "prompt": "Extract all text from these images. Return the text exactly as written.",
                        "model": "gpt-4o",
                        "images": "{{uploaded_images}}",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="tool",
            name="Tool Node",
            description="Call a registered tool by name. Arguments can use {{variable}} templates.",
            category="compute",
            node_class=ToolNode,
            inputs=[
                PortSpec(
                    "input",
                    "any",
                    False,
                    "Input data passed to tool and available for templating",
                ),
            ],
            outputs=[
                PortSpec("output", "any", True, "Tool execution result"),
            ],
            examples=[
                NodeExample(
                    name="Web Search",
                    description="Search the web",
                    config={"tool": "search.web", "args": {"query": "{{query}}"}},
                ),
                NodeExample(
                    name="Read File",
                    description="Read a file from workspace",
                    config={
                        "tool": "workspace.read_file",
                        "args": {"path": "{{path}}"},
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="code",
            name="Code Node",
            description=(
                "Execute Python code in a Docker sandbox. Code receives inputs dict "
                "and should return a result via main(input) or global 'result' variable. "
                "Use 'profile' to select pre-configured environments (datascience, viz, web)."
            ),
            category="compute",
            node_class=CodeNode,
            inputs=[
                PortSpec("input", "any", False, "Inputs available in code execution"),
            ],
            outputs=[
                PortSpec("output", "any", True, "Code execution result"),
                PortSpec("stdout", "string", False, "Captured stdout from execution"),
                PortSpec("stderr", "string", False, "Captured stderr from execution"),
                PortSpec("error", "string", False, "Error message if execution failed"),
                PortSpec("ok", "boolean", True, "Whether execution succeeded"),
                PortSpec("duration_ms", "number", False, "Execution time in milliseconds"),
            ],
            examples=[
                NodeExample(
                    name="Transform Data",
                    description="Transform input data with Python",
                    config={
                        "code": "result = input['value'] * 2",
                        "language": "python",
                    },
                ),
                NodeExample(
                    name="Data Analysis",
                    description="Analyze data with pandas (requires datascience profile)",
                    config={
                        "code": """import pandas as pd

def main(input):
    df = pd.DataFrame(input["data"])
    return {"mean": df["value"].mean(), "count": len(df)}
""",
                        "profile": "datascience",
                        "allow_site_packages": True,
                        "timeout_ms": 30000,
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="code_generator",
            name="Code Generator Node",
            description="Use an LLM to generate code from a natural language description.",
            category="compute",
            node_class=CodeGeneratorNode,
            inputs=[
                PortSpec("input", "any", False, "Context for code generation"),
            ],
            outputs=[
                PortSpec("code", "string", True, "Generated code"),
                PortSpec("language", "string", True, "Programming language"),
                PortSpec("description", "string", False, "What the code does"),
            ],
            examples=[
                NodeExample(
                    name="Generate Function",
                    description="Generate a Python function",
                    config={
                        "description": "A function that {{task}}",
                        "language": "python",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="debug",
            name="Debug Node",
            description="LLM-powered code debugging. Analyzes errors and suggests fixes.",
            category="compute",
            node_class=DebugNode,
            inputs=[
                PortSpec("code", "string", True, "Code to debug"),
                PortSpec("error", "string", True, "Error message"),
                PortSpec("traceback", "string", False, "Full traceback"),
            ],
            outputs=[
                PortSpec("fixed_code", "string", True, "Corrected code"),
                PortSpec("analysis", "string", True, "Explanation of the bug"),
            ],
            examples=[
                NodeExample(
                    name="Debug Python",
                    description="Debug a Python error",
                    config={"model": "gpt-4o", "temperature": 0.3},
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="transform",
            name="Transform Node",
            description="Transform data using a safe expression. Supports arithmetic, comparisons, and dict access.",
            category="compute",
            node_class=TransformNode,
            inputs=[
                PortSpec("input", "any", False, "Data available in expression"),
            ],
            outputs=[
                PortSpec("output", "any", True, "Expression result"),
            ],
            examples=[
                NodeExample(
                    name="Add Numbers",
                    description="Add two numbers",
                    config={"expr": "a + b"},
                ),
                NodeExample(
                    name="Extract Field",
                    description="Extract a field from input",
                    config={"expr": "data.get('name', 'unknown')"},
                ),
            ],
        )
    )

    # =========================================================================
    # CONTROL FLOW NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="router",
            name="Router Node",
            description="Multi-way routing based on a condition value. Routes to different nodes based on the result.",
            category="control",
            node_class=RouterNode,
            inputs=[
                PortSpec("input", "any", False, "Data for condition evaluation"),
            ],
            outputs=[
                PortSpec("selected_route", "string", True, "Which route was selected"),
                PortSpec(
                    "condition_value", "any", True, "The evaluated condition value"
                ),
                PortSpec("routes_available", "array", True, "List of available routes"),
            ],
            examples=[
                NodeExample(
                    name="Intent Router",
                    description="Route based on detected intent",
                    config={
                        "condition": "{{intent}}",
                        "routes": {"search": "search_node", "create": "create_node"},
                        "default": "fallback_node",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="gate",
            name="Gate Node",
            description="Binary conditional (if/else). Routes to true_path or false_path based on condition.",
            category="control",
            node_class=GateNode,
            inputs=[
                PortSpec("input", "any", False, "Data for condition evaluation"),
            ],
            outputs=[
                PortSpec("selected_route", "string", True, "Which path was selected"),
                PortSpec("condition_value", "boolean", True, "The evaluated condition"),
            ],
            examples=[
                NodeExample(
                    name="Confidence Gate",
                    description="Route based on confidence threshold",
                    config={
                        "condition": "score > 0.8",
                        "true_path": "high_confidence",
                        "false_path": "low_confidence",
                    },
                ),
            ],
        )
    )

    # =========================================================================
    # MEMORY NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="memory_read",
            name="Memory Read Node",
            description="Read from memory store by key or semantic search.",
            category="memory",
            node_class=MemoryReadNode,
            inputs=[
                PortSpec("input", "any", False, "Context for templating key/query"),
            ],
            outputs=[
                PortSpec("value", "any", False, "Value at key (for key lookup)"),
                PortSpec(
                    "results", "array", False, "Search results (for semantic search)"
                ),
            ],
            examples=[
                NodeExample(
                    name="Get by Key",
                    description="Get a specific value",
                    config={"key": "user_preferences", "namespace": "default"},
                ),
                NodeExample(
                    name="Semantic Search",
                    description="Search memory semantically",
                    config={"query": "{{question}}", "limit": 5},
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="memory_write",
            name="Memory Write Node",
            description="Write to memory store.",
            category="memory",
            node_class=MemoryWriteNode,
            inputs=[
                PortSpec("input", "any", True, "Value to write"),
            ],
            outputs=[
                PortSpec("key", "string", True, "Key that was written"),
                PortSpec("written", "boolean", True, "Whether write succeeded"),
            ],
            examples=[
                NodeExample(
                    name="Store Result",
                    description="Store a computation result",
                    config={
                        "key": "last_result",
                        "value_expr": "{{output}}",
                        "namespace": "default",
                    },
                ),
            ],
        )
    )

    # =========================================================================
    # COMPOSITION NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="subpathway",
            name="Sub-Pathway Node",
            description="Execute an embedded pathway as a single node. Enables hierarchical composition.",
            category="composition",
            node_class=SubPathwayNode,
            inputs=[
                PortSpec("input", "any", False, "Inputs passed to sub-pathway"),
            ],
            outputs=[
                PortSpec("success", "boolean", True, "Whether sub-pathway succeeded"),
                PortSpec("outputs", "object", True, "Sub-pathway outputs"),
            ],
            examples=[
                NodeExample(
                    name="Nested Analysis",
                    description="Run an analysis sub-pathway",
                    config={
                        "pathway_data": {},  # Pathway JSON here
                        "input_mapping": {"text": "input"},
                        "output_mapping": {"result": "output"},
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="map",
            name="Map Node",
            description="Apply a node to each item in a collection, running in parallel.",
            category="composition",
            node_class=MapNode,
            inputs=[
                PortSpec("input", "array", True, "Collection to iterate over"),
            ],
            outputs=[
                PortSpec("results", "array", True, "Results from each iteration"),
                PortSpec("count", "number", True, "Number of items processed"),
                PortSpec("errors", "array", False, "Any errors that occurred"),
            ],
            examples=[
                NodeExample(
                    name="Analyze Each",
                    description="Analyze each item in a list",
                    config={
                        "over": "{{items}}",
                        "node_data": {"type": "llm", "prompt": "Analyze: {{item}}"},
                        "max_concurrent": 5,
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="conditional",
            name="Conditional Node",
            description="Conditionally execute a node based on runtime condition.",
            category="composition",
            node_class=ConditionalNode,
            inputs=[
                PortSpec("input", "any", False, "Input for condition and execution"),
            ],
            outputs=[
                PortSpec(
                    "executed", "string", False, "'then', 'else', or null if skipped"
                ),
                PortSpec("condition", "boolean", True, "Condition result"),
            ],
            examples=[
                NodeExample(
                    name="Conditional LLM",
                    description="Only call LLM if needed",
                    config={
                        "condition": "needs_analysis",
                        "then_node_data": {
                            "type": "llm",
                            "prompt": "Analyze: {{input}}",
                        },
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="route",
            name="Route Node",
            description="Route execution to one of several embedded nodes based on condition.",
            category="composition",
            node_class=RouteNode,
            inputs=[
                PortSpec("input", "any", False, "Input for condition and execution"),
            ],
            outputs=[
                PortSpec("selected_route", "string", True, "Which route was taken"),
                PortSpec("route_value", "any", True, "Condition value"),
            ],
            examples=[
                NodeExample(
                    name="Mode Switch",
                    description="Different behavior per mode",
                    config={
                        "condition": "{{mode}}",
                        "routes_data": {
                            "fast": {
                                "type": "llm",
                                "prompt": "Quick answer: {{input}}",
                                "model": "gpt-3.5-turbo",
                            },
                            "thorough": {
                                "type": "llm",
                                "prompt": "Detailed analysis: {{input}}",
                                "model": "gpt-4o",
                            },
                        },
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="retry",
            name="Retry Node",
            description="Retry a node on failure with configurable backoff.",
            category="composition",
            node_class=RetryNode,
            inputs=[
                PortSpec("input", "any", False, "Input to wrapped node"),
            ],
            outputs=[
                PortSpec("attempts", "number", True, "Number of attempts made"),
            ],
            examples=[
                NodeExample(
                    name="Retry API Call",
                    description="Retry a flaky API call",
                    config={
                        "node_data": {"type": "tool", "tool": "api.call"},
                        "max_attempts": 3,
                        "backoff_seconds": 1.0,
                        "backoff_multiplier": 2.0,
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="timeout",
            name="Timeout Node",
            description="Execute a node with a timeout. Returns error or default value on timeout.",
            category="composition",
            node_class=TimeoutNode,
            inputs=[
                PortSpec("input", "any", False, "Input to wrapped node"),
            ],
            outputs=[
                PortSpec("timed_out", "boolean", True, "Whether timeout occurred"),
            ],
            examples=[
                NodeExample(
                    name="Bounded LLM",
                    description="LLM call with timeout",
                    config={
                        "node_data": {"type": "llm", "prompt": "{{input}}"},
                        "timeout_seconds": 30.0,
                        "on_timeout": "error",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="fallback",
            name="Fallback Node",
            description="Try nodes in sequence until one succeeds.",
            category="composition",
            node_class=FallbackNode,
            inputs=[
                PortSpec("input", "any", False, "Input to all fallback nodes"),
            ],
            outputs=[
                PortSpec(
                    "fallback_index",
                    "number",
                    True,
                    "Which fallback succeeded (0-indexed)",
                ),
                PortSpec(
                    "fallback_attempts", "number", True, "Number of attempts made"
                ),
            ],
            examples=[
                NodeExample(
                    name="Model Fallback",
                    description="Try GPT-4, fall back to GPT-3.5",
                    config={
                        "nodes_data": [
                            {"type": "llm", "prompt": "{{input}}", "model": "gpt-4o"},
                            {
                                "type": "llm",
                                "prompt": "{{input}}",
                                "model": "gpt-3.5-turbo",
                            },
                        ],
                    },
                ),
            ],
        )
    )

    # =========================================================================
    # AGENT NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="agent_loop",
            name="Agent Loop Node",
            description="Agentic execution loop where the model decides which tools to use. Claude-like behavior.",
            category="agent",
            node_class=AgentLoopNode,
            inputs=[
                PortSpec("input", "any", False, "Initial context/goal"),
            ],
            outputs=[
                PortSpec("response", "string", True, "Final agent response"),
                PortSpec("steps", "array", True, "Steps taken by agent"),
                PortSpec("tool_calls", "array", True, "All tool calls made"),
            ],
            examples=[
                NodeExample(
                    name="Research Agent",
                    description="Agent that researches a topic",
                    config={
                        "goal": "Research {{topic}} and summarize findings",
                        "tools": ["search.*", "memory.*"],
                        "max_steps": 10,
                        "model": "gpt-4o",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="tool_calling_llm",
            name="Tool Calling LLM Node",
            description="LLM with tool calling capability. Model decides which tools to call.",
            category="agent",
            node_class=ToolCallingLLMNode,
            inputs=[
                PortSpec("input", "any", False, "User message/context"),
            ],
            outputs=[
                PortSpec(
                    "response", "string", False, "Model response (if no tools called)"
                ),
                PortSpec("tool_calls", "array", False, "Tool calls to execute"),
                PortSpec("finish_reason", "string", True, "Why model stopped"),
            ],
            examples=[
                NodeExample(
                    name="Assistant with Tools",
                    description="Assistant that can use tools",
                    config={
                        "prompt": "Help the user: {{input}}",
                        "tools": ["search.*", "workspace.*"],
                        "model": "gpt-4o",
                    },
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="tool_executor",
            name="Tool Executor Node",
            description="Execute tool calls from a ToolCallingLLMNode.",
            category="agent",
            node_class=ToolExecutorNode,
            inputs=[
                PortSpec("tool_calls", "array", True, "Tool calls to execute"),
            ],
            outputs=[
                PortSpec("results", "array", True, "Results from tool executions"),
            ],
            examples=[
                NodeExample(
                    name="Execute Tools",
                    description="Execute pending tool calls",
                    config={"parallel": True, "max_concurrent": 5},
                ),
            ],
        )
    )

    # =========================================================================
    # STREAMING NODES
    # =========================================================================

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="event_source",
            name="Event Source Node",
            description="Streaming event source. Emits events that trigger downstream execution.",
            category="streaming",
            node_class=EventSourceNode,
            inputs=[],
            outputs=[
                PortSpec("event", "any", True, "Emitted event"),
                PortSpec("source_node_id", "string", True, "Source node identifier"),
            ],
            examples=[
                NodeExample(
                    name="Timer",
                    description="Emit events on interval",
                    config={
                        "source": "timer.interval",
                        "config": {"interval_seconds": 60},
                    },
                ),
                NodeExample(
                    name="Webhook",
                    description="Listen for webhook events",
                    config={"source": "webhook.listen", "config": {"topic": "updates"}},
                ),
            ],
        )
    )

    NodeTypeRegistry.register(
        NodeTypeSpec(
            type="introspection",
            name="Introspection Node",
            description="Stream internal pathway events for observation/debugging.",
            category="streaming",
            node_class=IntrospectionNode,
            inputs=[],
            outputs=[
                PortSpec("event", "object", True, "Internal pathway event"),
            ],
            examples=[
                NodeExample(
                    name="Observe All",
                    description="Observe all pathway events",
                    config={
                        "event_types": ["node_started", "node_completed", "tool_called"]
                    },
                ),
            ],
        )
    )


__all__ = [
    "NodeTypeRegistry",
    "NodeTypeSpec",
    "PortSpec",
    "NodeExample",
    "register_builtin_node_types",
]
