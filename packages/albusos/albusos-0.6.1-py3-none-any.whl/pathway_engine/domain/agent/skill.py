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
    tags: set[str] = field(default_factory=set)

    async def invoke(self, inputs: dict[str, Any], ctx: "Context") -> dict[str, Any]:
        """Execute this skill.

        Handles both Context (from agent loops) and ToolContext (from HTTP tools).
        """
        import logging
        from pathway_engine.application.kernel.vm import PathwayVM
        from pathway_engine.domain.context import Context

        logger = logging.getLogger(__name__)

        if not self.pathway_builder:
            return {"error": f"Skill {self.id} has no pathway"}

        # Debug: log context type and tools
        logger.info(
            "Skill.invoke(%s): ctx type=%s, has tools attr=%s, tools count=%s",
            self.id,
            type(ctx).__name__,
            hasattr(ctx, "tools"),
            len(getattr(ctx, "tools", {})) if hasattr(ctx, "tools") else "N/A",
        )

        # Build proper Context if we received ToolContext or need to bridge
        if not isinstance(ctx, Context):
            # Got ToolContext from HTTP tools endpoint - build a proper Context
            logger.info("Skill.invoke: Converting ToolContext to Context")
            extras = getattr(ctx, "extras", {}) or {}
            tools_dict = extras.get("tools", {})

            ctx = Context(
                tools=tools_dict,
                extras=extras,
                workspace_id=getattr(ctx, "workspace_id", None),
                thread_id=getattr(ctx, "thread_id", None),
            )
        elif not ctx.tools:
            # Context but tools not populated - try to get from extras
            logger.info("Skill.invoke: Context has no tools, checking extras")
            tools_from_extras = ctx.extras.get("tools", {})
            if tools_from_extras:
                ctx = Context(
                    tools=tools_from_extras,
                    extras=ctx.extras,
                    memory=ctx.memory,
                    workspace_id=ctx.workspace_id,
                    thread_id=ctx.thread_id,
                    pathway_id=ctx.pathway_id,
                    execution_id=ctx.execution_id,
                )
        
        logger.info(
            "Skill.invoke: Final ctx tools count=%s, sample tools=%s",
            len(ctx.tools),
            list(ctx.tools.keys())[:5] if ctx.tools else "NONE",
        )

        pathway = self.pathway_builder()
        vm = PathwayVM(ctx)
        logger.info("Skill.invoke: Created PathwayVM, executing pathway %s", pathway.id)
        result = await vm.execute(pathway, inputs)
        logger.info("Skill.invoke: Pathway result=%s", result)

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
            "tags": sorted(self.tags),
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

@dataclass
class SkillBuilder:
    """Fluent builder for Skill objects (used in tests/docs)."""

    _id: str | None = None
    _name: str | None = None
    _description: str = ""
    _pathway_builder: Callable[[], "Pathway"] | None = None
    _inputs: dict[str, str] = field(default_factory=dict)
    _outputs: dict[str, str] = field(default_factory=dict)
    _tags: set[str] = field(default_factory=set)

    def id(self, value: str) -> "SkillBuilder":
        self._id = value
        return self

    def name(self, value: str) -> "SkillBuilder":
        self._name = value
        return self

    def description(self, value: str) -> "SkillBuilder":
        self._description = value
        return self

    def pathway(self, builder: Callable[[], "Pathway"]) -> "SkillBuilder":
        self._pathway_builder = builder
        return self

    def input(self, key: str, schema: str) -> "SkillBuilder":
        self._inputs[key] = schema
        return self

    def output(self, key: str, schema: str) -> "SkillBuilder":
        self._outputs[key] = schema
        return self

    def tag(self, *tags: str) -> "SkillBuilder":
        for t in tags:
            if t:
                self._tags.add(t)
        return self

    def build(self) -> Skill:
        if not self._id:
            raise ValueError("SkillBuilder.id(...) is required")
        if not self._name:
            raise ValueError("SkillBuilder.name(...) is required")
        return Skill(
            id=self._id,
            name=self._name,
            description=self._description,
            pathway_builder=self._pathway_builder,
            inputs_schema=self._inputs,
            outputs_schema=self._outputs,
            tags=self._tags,
        )


def skill_builder() -> SkillBuilder:
    return SkillBuilder()


@dataclass
class SkillBundle:
    """A simple grouping of related skills."""

    id: str
    name: str
    description: str = ""
    skills: list[Skill] = field(default_factory=list)
    version: str | None = None
    author: str | None = None
    tags: set[str] = field(default_factory=set)

    def get_skill(self, skill_id: str) -> Skill | None:
        for s in self.skills:
            if s.id == skill_id:
                return s
        return None

    def list_skills(self) -> list[str]:
        return [s.id for s in self.skills]


@dataclass
class BundleBuilder:
    """Fluent builder for SkillBundle objects (used in tests/docs)."""

    _id: str | None = None
    _name: str | None = None
    _description: str = ""
    _skills: list[Skill] = field(default_factory=list)
    _version: str | None = None
    _author: str | None = None
    _tags: set[str] = field(default_factory=set)

    def id(self, value: str) -> "BundleBuilder":
        self._id = value
        return self

    def name(self, value: str) -> "BundleBuilder":
        self._name = value
        return self

    def description(self, value: str) -> "BundleBuilder":
        self._description = value
        return self

    def skill(self, value: Skill) -> "BundleBuilder":
        self._skills.append(value)
        return self

    def version(self, value: str) -> "BundleBuilder":
        self._version = value
        return self

    def author(self, value: str) -> "BundleBuilder":
        self._author = value
        return self

    def tag(self, *tags: str) -> "BundleBuilder":
        for t in tags:
            if t:
                self._tags.add(t)
        return self

    def build(self) -> SkillBundle:
        if not self._id:
            raise ValueError("BundleBuilder.id(...) is required")
        if not self._name:
            raise ValueError("BundleBuilder.name(...) is required")
        return SkillBundle(
            id=self._id,
            name=self._name,
            description=self._description,
            skills=self._skills,
            version=self._version,
            author=self._author,
            tags=self._tags,
        )


def bundle_builder() -> BundleBuilder:
    return BundleBuilder()


__all__ = [
    "Skill",
    "SkillBuilder",
    "SkillBundle",
    "BundleBuilder",
    "skill",
    "skill_builder",
    "bundle_builder",
]
