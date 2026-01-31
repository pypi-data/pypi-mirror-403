"""Composition Nodes - Advanced composability primitives.

These nodes enable:
- Hierarchical composition (pathway-as-node)
- Fan-out/fan-in (map over collections)
- Conditional inclusion
- Dynamic pathway execution

Together with the DSL operators (>>, |, &), these provide
complete composability for building complex cognitive architectures.
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal, TYPE_CHECKING

from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.context import Context

if TYPE_CHECKING:
    from pathway_engine.domain.pathway import Pathway


# =============================================================================
# SUBPATHWAY NODE - Hierarchical Composition
# =============================================================================


class SubPathwayNode(NodeBase):
    """Execute an embedded pathway as a single node.

    Enables hierarchical composition - pathways can contain other pathways.
    The sub-pathway receives this node's inputs and its outputs become
    this node's outputs.

    Attributes:
        pathway_data: Serialized pathway (for Pydantic serialization)
        input_mapping: Map parent inputs to child inputs
        output_mapping: Map child outputs to parent outputs
    """

    type: Literal["subpathway"] = "subpathway"
    pathway_data: dict[str, Any] = Field(default_factory=dict)
    input_mapping: dict[str, str] = Field(
        default_factory=dict
    )  # parent_key -> child_key
    output_mapping: dict[str, str] = Field(
        default_factory=dict
    )  # child_key -> parent_key

    # Runtime-only (not serialized)
    _pathway: "Pathway | None" = None

    def set_pathway(self, pathway: "Pathway") -> "SubPathwayNode":
        """Set the pathway at runtime (before serialization, use pathway_data)."""
        self._pathway = pathway
        self.pathway_data = pathway.model_dump()
        return self

    def get_pathway(self) -> "Pathway":
        """Get the pathway (deserializes from pathway_data if needed)."""
        if self._pathway is not None:
            return self._pathway

        from pathway_engine.domain.pathway import Pathway

        self._pathway = Pathway.model_validate(self.pathway_data)
        return self._pathway

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute the sub-pathway."""
        # Get VM from context
        vm = ctx.services.pathway_executor
        if not vm:
            raise RuntimeError(
                "pathway_executor not available in context for SubPathwayNode"
            )

        # Map inputs
        child_inputs = dict(inputs)
        for parent_key, child_key in self.input_mapping.items():
            if parent_key in inputs:
                child_inputs[child_key] = inputs[parent_key]

        # Execute sub-pathway
        pathway = self.get_pathway()
        record = await vm.execute(pathway, child_inputs)

        if not record.success:
            return {
                "success": False,
                "error": record.error,
                "outputs": {},
            }

        # Map outputs
        result = dict(record.outputs)
        for child_key, parent_key in self.output_mapping.items():
            if child_key in record.outputs:
                result[parent_key] = record.outputs[child_key]

        return {
            "success": True,
            "outputs": result,
            **result,  # Flatten for easy access
        }


# =============================================================================
# MAP NODE - Fan-out / Fan-in
# =============================================================================


class MapNode(NodeBase):
    """Map a node/pathway over a collection, running in parallel.

    Fan-out pattern: takes a list, applies operation to each item,
    collects results back into a list.

    Attributes:
        over: Input key containing the collection to iterate
        node_data: Serialized node to apply to each item
        max_concurrent: Max parallel executions (0 = unlimited)
        item_key: Key name for current item in node inputs
        index_key: Key name for current index in node inputs
    """

    type: Literal["map"] = "map"
    over: str  # e.g., "{{items}}" or just "items"
    node_data: dict[str, Any] = Field(default_factory=dict)
    max_concurrent: int = 10
    item_key: str = "item"
    index_key: str = "index"
    collect_key: str = "results"

    # Runtime-only
    _node: "NodeBase | None" = None

    def set_node(self, node: "NodeBase") -> "MapNode":
        """Set the node to map."""
        self._node = node
        self.node_data = node.model_dump()
        return self

    def get_node(self) -> "NodeBase":
        """Get the node (deserializes if needed)."""
        if self._node is not None:
            return self._node

        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Node)
        self._node = adapter.validate_python(self.node_data)
        return self._node

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute node over each item in the collection."""
        # Resolve the collection
        over_key = self.over.strip("{}")
        collection = self._resolve_path(inputs, over_key)

        if not isinstance(collection, (list, tuple)):
            return {
                "error": f"Expected list for '{over_key}', got {type(collection).__name__}",
                self.collect_key: [],
            }

        if not collection:
            return {self.collect_key: []}

        node = self.get_node()

        # Execute with concurrency control
        semaphore = (
            asyncio.Semaphore(self.max_concurrent) if self.max_concurrent > 0 else None
        )

        async def run_one(idx: int, item: Any) -> dict[str, Any]:
            if semaphore:
                async with semaphore:
                    return await self._run_item(node, inputs, idx, item, ctx)
            return await self._run_item(node, inputs, idx, item, ctx)

        tasks = [run_one(i, item) for i, item in enumerate(collection)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        outputs = []
        errors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({"index": i, "error": str(result)})
                outputs.append(None)
            else:
                outputs.append(result)

        return {
            self.collect_key: outputs,
            "count": len(collection),
            "errors": errors if errors else None,
        }

    async def _run_item(
        self,
        node: "NodeBase",
        base_inputs: dict[str, Any],
        index: int,
        item: Any,
        ctx: Context,
    ) -> dict[str, Any]:
        """Run node for a single item."""
        item_inputs = {
            **base_inputs,
            self.item_key: item,
            self.index_key: index,
        }
        return await node.compute(item_inputs, ctx)


# =============================================================================
# CONDITIONAL NODE - Build-time conditional inclusion
# =============================================================================


class ConditionalNode(NodeBase):
    """Conditionally execute a node based on runtime condition.

    Unlike routing (RouterNode/GateNode) which routes between nodes, this conditionally
    executes or skips a single node entirely.

    Attributes:
        condition: Expression to evaluate
        then_node_data: Node to execute if condition is true
        else_node_data: Optional node to execute if condition is false
    """

    type: Literal["conditional"] = "conditional"
    condition: str
    then_node_data: dict[str, Any] = Field(default_factory=dict)
    else_node_data: dict[str, Any] | None = None

    _then_node: "NodeBase | None" = None
    _else_node: "NodeBase | None" = None

    def set_then(self, node: "NodeBase") -> "ConditionalNode":
        self._then_node = node
        self.then_node_data = node.model_dump()
        return self

    def set_else(self, node: "NodeBase") -> "ConditionalNode":
        self._else_node = node
        self.else_node_data = node.model_dump()
        return self

    def get_then_node(self) -> "NodeBase":
        if self._then_node:
            return self._then_node
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        self._then_node = TypeAdapter(Node).validate_python(self.then_node_data)
        return self._then_node

    def get_else_node(self) -> "NodeBase | None":
        if self._else_node:
            return self._else_node
        if not self.else_node_data:
            return None
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        self._else_node = TypeAdapter(Node).validate_python(self.else_node_data)
        return self._else_node

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute conditionally."""
        from pathway_engine.domain.expressions import safe_eval

        # Evaluate condition
        formatted_condition = self._format_template(self.condition, inputs)
        try:
            result = safe_eval(formatted_condition, inputs)
        except Exception:
            result = bool(formatted_condition)  # Fallback to truthiness

        if result:
            node = self.get_then_node()
            output = await node.compute(inputs, ctx)
            return {"executed": "then", "condition": True, **output}
        else:
            else_node = self.get_else_node()
            if else_node:
                output = await else_node.compute(inputs, ctx)
                return {"executed": "else", "condition": False, **output}
            return {"executed": None, "condition": False, "skipped": True}


# =============================================================================
# ROUTE NODE - Multi-way routing (switch)
# =============================================================================


class RouteNode(NodeBase):
    """Route execution to exactly one embedded node based on a runtime condition.

    This is a multi-way version of ConditionalNode that preserves a clean single-node
    surface for pathway composition.

    Attributes:
        condition: Expression to evaluate (supports {{var}} templates or dict syntax)
        routes_data: Mapping of route values -> serialized Node data
        default_node_data: Optional serialized Node to execute if no route matches
    """

    type: Literal["route"] = "route"
    condition: str
    routes_data: dict[str, dict[str, Any]] = Field(default_factory=dict)
    default_node_data: dict[str, Any] | None = None

    _routes: dict[str, "NodeBase"] | None = None
    _default_node: "NodeBase | None" = None

    def set_routes(self, routes: dict[str, "NodeBase"]) -> "RouteNode":
        self._routes = routes
        self.routes_data = {k: v.model_dump() for k, v in routes.items()}
        return self

    def set_default(self, node: "NodeBase | None") -> "RouteNode":
        self._default_node = node
        self.default_node_data = node.model_dump() if node is not None else None
        return self

    def get_routes(self) -> dict[str, "NodeBase"]:
        if self._routes is not None:
            return self._routes
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Node)
        self._routes = {
            k: adapter.validate_python(d) for k, d in self.routes_data.items()
        }
        return self._routes

    def get_default(self) -> "NodeBase | None":
        if self._default_node is not None:
            return self._default_node
        if not self.default_node_data:
            return None
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        self._default_node = TypeAdapter(Node).validate_python(self.default_node_data)
        return self._default_node

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        from pathway_engine.domain.expressions import safe_eval

        routes = self.get_routes()

        # Evaluate condition (match RouterNode semantics)
        condition = self.condition
        if "{{" in condition:
            interpolated = self._format_template(condition, inputs)
            try:
                value = safe_eval(interpolated, {})
            except Exception:
                value = interpolated
        else:
            value = safe_eval(condition, inputs)

        str_value = str(value).lower() if isinstance(value, bool) else str(value)

        node = routes.get(str_value)
        selected_key: str | None = str_value if node is not None else None

        if node is None:
            node = self.get_default()
            if node is None:
                return {
                    "error": f"No route matched value={str_value!r}",
                    "route_value": value,
                    "selected_route": None,
                    "routes_available": sorted(list(routes.keys())),
                }
            selected_key = "default"

        out = await node.compute(inputs, ctx)
        return {
            "selected_route": selected_key,
            "route_value": value,
            "routes_available": sorted(list(routes.keys())),
            **out,
        }


# =============================================================================
# RETRY NODE - Automatic retry with backoff
# =============================================================================


class RetryNode(NodeBase):
    """Retry a node on failure with configurable backoff.

    Attributes:
        node_data: Node to retry
        max_attempts: Maximum retry attempts
        backoff_seconds: Initial backoff delay
        backoff_multiplier: Multiply backoff each retry
        retry_on: List of error substrings that trigger retry (empty = all errors)
    """

    type: Literal["retry"] = "retry"
    node_data: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    retry_on: list[str] = Field(default_factory=list)

    _node: "NodeBase | None" = None

    def set_node(self, node: "NodeBase") -> "RetryNode":
        self._node = node
        self.node_data = node.model_dump()
        return self

    def get_node(self) -> "NodeBase":
        if self._node:
            return self._node
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        self._node = TypeAdapter(Node).validate_python(self.node_data)
        return self._node

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute with retry."""
        node = self.get_node()
        last_error = None
        backoff = self.backoff_seconds

        for attempt in range(self.max_attempts):
            try:
                result = await node.compute(inputs, ctx)

                # Check if result indicates failure
                if result.get("error") or result.get("success") is False:
                    error_msg = str(result.get("error", ""))
                    if self._should_retry(error_msg):
                        last_error = error_msg
                        if attempt < self.max_attempts - 1:
                            await asyncio.sleep(backoff)
                            backoff *= self.backoff_multiplier
                            continue

                return {
                    **result,
                    "attempts": attempt + 1,
                }

            except Exception as e:
                last_error = str(e)
                if self._should_retry(last_error) and attempt < self.max_attempts - 1:
                    await asyncio.sleep(backoff)
                    backoff *= self.backoff_multiplier
                    continue
                raise

        return {
            "error": f"Max retries ({self.max_attempts}) exceeded. Last error: {last_error}",
            "attempts": self.max_attempts,
        }

    def _should_retry(self, error: str) -> bool:
        if not self.retry_on:
            return True  # Retry all errors
        return any(pattern in error for pattern in self.retry_on)


# =============================================================================
# TIMEOUT NODE - Execution timeout
# =============================================================================


class TimeoutNode(NodeBase):
    """Execute a node with a timeout.

    Attributes:
        node_data: Node to execute
        timeout_seconds: Maximum execution time
        on_timeout: What to return on timeout ("error" or "default")
        default_value: Default value to return on timeout
    """

    type: Literal["timeout"] = "timeout"
    node_data: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    on_timeout: Literal["error", "default"] = "error"
    default_value: dict[str, Any] = Field(default_factory=dict)

    _node: "NodeBase | None" = None

    def set_node(self, node: "NodeBase") -> "TimeoutNode":
        self._node = node
        self.node_data = node.model_dump()
        return self

    def get_node(self) -> "NodeBase":
        if self._node:
            return self._node
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        self._node = TypeAdapter(Node).validate_python(self.node_data)
        return self._node

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute with timeout."""
        node = self.get_node()

        try:
            result = await asyncio.wait_for(
                node.compute(inputs, ctx),
                timeout=self.timeout_seconds,
            )
            return {**result, "timed_out": False}

        except asyncio.TimeoutError:
            if self.on_timeout == "default":
                return {
                    **self.default_value,
                    "timed_out": True,
                    "timeout_seconds": self.timeout_seconds,
                }
            return {
                "error": f"Execution timed out after {self.timeout_seconds}s",
                "timed_out": True,
            }


# =============================================================================
# FALLBACK NODE - Try alternatives on failure
# =============================================================================


class FallbackNode(NodeBase):
    """Try nodes in sequence until one succeeds.

    Attributes:
        nodes_data: List of serialized nodes to try in order
    """

    type: Literal["fallback"] = "fallback"
    nodes_data: list[dict[str, Any]] = Field(default_factory=list)

    _nodes: list["NodeBase"] | None = None

    def set_nodes(self, nodes: list["NodeBase"]) -> "FallbackNode":
        self._nodes = nodes
        self.nodes_data = [n.model_dump() for n in nodes]
        return self

    def get_nodes(self) -> list["NodeBase"]:
        if self._nodes:
            return self._nodes
        from pathway_engine.domain.nodes import Node
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Node)
        self._nodes = [adapter.validate_python(d) for d in self.nodes_data]
        return self._nodes

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Try each node until one succeeds."""
        nodes = self.get_nodes()
        errors = []

        for i, node in enumerate(nodes):
            try:
                result = await node.compute(inputs, ctx)

                # Check for success
                if not result.get("error") and result.get("success") is not False:
                    return {
                        **result,
                        "fallback_index": i,
                        "fallback_attempts": i + 1,
                    }

                errors.append(
                    {"index": i, "error": result.get("error", "Unknown error")}
                )

            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return {
            "error": "All fallback options failed",
            "fallback_errors": errors,
            "fallback_attempts": len(nodes),
        }


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    "SubPathwayNode",
    "MapNode",
    "ConditionalNode",
    "RouteNode",
    "RetryNode",
    "TimeoutNode",
    "FallbackNode",
]
