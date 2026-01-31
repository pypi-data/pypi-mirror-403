"""NodeBase - Base class for all node types with composition operators.

Nodes are composable values. They:
1. Are Pydantic models (serializable to JSON)
2. Have a compute() method (executable)
3. Support operators for composition (>>, |, &)

Example:
    understand = LLMNode(prompt="Analyze: {{input}}")
    search = ToolNode(tool="web.search")
    
    # Chain with >>
    graph = understand >> search
    
    # Parallel with |
    multi = search_a | search_b | search_c
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context
    from pathway_engine.domain.pathway import Pathway, Connection


class NodeBase(BaseModel):
    """Base class for all node types.

    Subclasses must:
    1. Define a `type` literal field (for serialization)
    2. Implement `compute(inputs, ctx)` method

    Example:
        class LLMNode(NodeBase):
            type: Literal["llm"] = "llm"
            prompt: str
            model: str = "auto"  # Uses capability routing

            async def compute(self, inputs: dict, ctx: Context) -> dict:
                ...
    """

    model_config = {"extra": "forbid"}

    # Identity
    id: str = Field(default_factory=lambda: f"n_{uuid4().hex[:6]}")
    name: str | None = None
    description: str | None = None

    # Subclasses must override
    async def compute(self, inputs: dict[str, Any], ctx: "Context") -> dict[str, Any]:
        """Execute this node. Subclasses must implement.

        Args:
            inputs: Data from upstream nodes (gathered by VM from connections)
            ctx: Execution context with tools, memory, extras

        Returns:
            Output dict. Convention: {"output": value} or {"response": value}
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement compute()")

    # =========================================================================
    # COMPOSITION OPERATORS
    # =========================================================================

    def __rshift__(self, other: "NodeBase | Pathway") -> "Pathway":
        """Chain: self >> other

        Creates a Pathway where self connects to other.
        """
        from pathway_engine.domain.pathway import Pathway, Connection

        if isinstance(other, Pathway):
            # self >> existing_pathway: prepend self
            return Pathway(
                id=f"chain_{uuid4().hex[:6]}",
                nodes={self.id: self, **other.nodes},
                connections=[
                    Connection(from_node=self.id, to_node=other.entry_id),
                    *other.connections,
                ],
            )
        else:
            # self >> other_node: create two-node pathway
            return Pathway(
                id=f"chain_{uuid4().hex[:6]}",
                nodes={self.id: self, other.id: other},
                connections=[Connection(from_node=self.id, to_node=other.id)],
            )

    def __or__(self, other: "NodeBase") -> "Pathway":
        """Parallel: self | other

        Creates a Pathway where both nodes run in parallel (no connection between them).
        They will receive the same input and their outputs can be joined downstream.
        """
        from pathway_engine.domain.pathway import Pathway

        return Pathway(
            id=f"parallel_{uuid4().hex[:6]}",
            nodes={self.id: self, other.id: other},
            connections=[],  # No connection = parallel
            metadata={"parallel_group": [self.id, other.id]},
        )

    def __and__(self, other: "NodeBase") -> "Pathway":
        """Join: self & other

        Creates a Pathway indicating both must complete before continuing.
        Similar to parallel but semantic difference for scheduling.
        """
        from pathway_engine.domain.pathway import Pathway

        return Pathway(
            id=f"join_{uuid4().hex[:6]}",
            nodes={self.id: self, other.id: other},
            connections=[],
            metadata={"join_group": [self.id, other.id]},
        )

    # =========================================================================
    # TEMPLATE HELPERS
    # =========================================================================

    def _format_template(self, template: str, data: dict[str, Any]) -> str:
        """Replace {{key}} and {{key.path}} with values from data.

        Supports:
            {{message}} - simple key
            {{node.output}} - nested path
            {{node.response.text}} - deep path
        """

        def replacer(match: re.Match) -> str:
            path = match.group(1).strip()
            value = self._resolve_path(data, path)
            if isinstance(value, (dict, list)):
                import json

                return json.dumps(value)
            return str(value) if value is not None else ""

        return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", replacer, template)

    def _resolve_path(self, data: dict[str, Any], path: str) -> Any:
        """Resolve a.b.c path in nested dict.

        Args:
            data: Dict to traverse
            path: Dot-separated path like "node.output.text"

        Returns:
            Value at path, or empty string if not found
        """
        obj: Any = data
        for part in path.split("."):
            if isinstance(obj, dict):
                obj = obj.get(part, "")
            elif isinstance(obj, (list, tuple)) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(obj):
                    obj = obj[idx]
                else:
                    return ""
            elif hasattr(obj, part):
                obj = getattr(obj, part, "")
            else:
                return ""
        return obj


__all__ = [
    "NodeBase",
]
