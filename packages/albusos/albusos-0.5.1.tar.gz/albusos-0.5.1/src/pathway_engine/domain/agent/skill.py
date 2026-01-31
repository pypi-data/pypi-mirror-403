"""Skill - A pathway exposed as a tool.

A Skill wraps a Pathway so agents can invoke it as a tool.
That's it. No bundles, no triggers, no registries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pathway_engine.domain.pathway import Pathway
    from pathway_engine.domain.context import Context


@dataclass
class Skill:
    """A pathway exposed as an agent tool.

    Example:
        triage_skill = Skill(
            id="triage",
            name="Triage Request",
            description="Classify urgency and route appropriately",
            pathway_builder=build_triage_pathway,
        )
    """

    id: str
    name: str
    description: str = ""
    pathway_builder: Callable[[], "Pathway"] | None = None

    # Optional: document inputs/outputs for LLM
    inputs_schema: dict[str, str] = field(default_factory=dict)
    outputs_schema: dict[str, str] = field(default_factory=dict)

    async def invoke(self, inputs: dict[str, Any], ctx: "Context") -> dict[str, Any]:
        """Execute this skill."""
        from pathway_engine.application.kernel.vm import PathwayVM

        if not self.pathway_builder:
            return {"error": f"Skill {self.id} has no pathway"}

        pathway = self.pathway_builder()
        vm = PathwayVM(ctx)
        result = await vm.execute(pathway, inputs)

        if result:
            return {"success": True, "outputs": result.outputs}
        return {"success": False, "error": "Pathway execution failed"}

    def to_tool_schema(self) -> dict[str, Any]:
        """Generate tool schema for LLM function calling."""
        properties = {}
        required = []

        for key, desc in self.inputs_schema.items():
            if " - " in desc:
                type_hint, description = desc.split(" - ", 1)
            else:
                type_hint, description = "string", desc

            properties[key] = {
                "type": type_hint if type_hint in ["string", "number", "boolean", "object", "array"] else "string",
                "description": description,
            }
            required.append(key)

        return {
            "name": f"skill.{self.id}",
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "inputs_schema": self.inputs_schema,
            "outputs_schema": self.outputs_schema,
        }


def skill(
    id: str,
    name: str,
    description: str = "",
    pathway_builder: Callable[[], "Pathway"] | None = None,
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
) -> Skill:
    """Create a skill (factory function)."""
    return Skill(
        id=id,
        name=name,
        description=description,
        pathway_builder=pathway_builder,
        inputs_schema=inputs or {},
        outputs_schema=outputs or {},
    )


__all__ = ["Skill", "skill"]
