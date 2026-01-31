"""Pathway Signatures - Typed I/O contracts for composition.

A PathwaySignature defines what a pathway expects and produces,
enabling type-safe composition into Networks.

This is a RUNTIME TYPE - it's used during execution for validation
and composition. It's not just a schema for user input.

## Architecture Note

PathwaySignature is part of pathway_engine because:
- It's used at runtime for validation
- It's used for network composition
- It defines how pathways connect

It's NOT just a "validation schema" - it's fundamental to how
pathways work.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PortSpec(BaseModel):
    """Specification for an input or output port."""

    model_config = {"extra": "allow"}

    name: str
    description: str | None = None

    # Type specification (JSON Schema compatible)
    type: str = "any"  # "string", "number", "object", "array", "any"
    json_schema: dict[str, Any] | None = None  # Full JSON Schema if complex

    # Constraints
    required: bool = True
    default: Any = None

    def accepts(self, value: Any) -> bool:
        """Check if a value is acceptable for this port."""
        if value is None:
            return not self.required or self.default is not None

        # Basic type checking
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list,
            "any": object,
        }
        expected = type_map.get(self.type, object)
        return isinstance(value, expected)


class PathwaySignature(BaseModel):
    """Contract for pathway composition - defines inputs and outputs.

    A signature enables:
    - Type-safe pathway composition (Network)
    - Documentation of pathway capabilities
    - Runtime validation of inputs/outputs
    - IDE/tooling support
    """

    model_config = {"extra": "allow"}

    # Input ports - what the pathway expects
    inputs: dict[str, PortSpec] = Field(default_factory=dict)

    # Output ports - what the pathway produces
    outputs: dict[str, PortSpec] = Field(default_factory=dict)

    # Optional metadata
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def any_to_any(cls) -> PathwaySignature:
        """Create a permissive signature (accepts anything, outputs anything)."""
        return cls(
            inputs={"input": PortSpec(name="input", type="any", required=False)},
            outputs={"output": PortSpec(name="output", type="any", required=False)},
        )

    @classmethod
    def from_json_schema(
        cls,
        *,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> PathwaySignature:
        """Create a signature from JSON schemas."""
        inputs: dict[str, PortSpec] = {}
        outputs: dict[str, PortSpec] = {}

        if input_schema and isinstance(input_schema, dict):
            props = input_schema.get("properties", {})
            required = set(input_schema.get("required", []))
            for name, prop in props.items():
                inputs[name] = PortSpec(
                    name=name,
                    type=prop.get("type", "any"),
                    description=prop.get("description"),
                    required=name in required,
                    json_schema=prop if prop.get("type") == "object" else None,
                )

        if output_schema and isinstance(output_schema, dict):
            props = output_schema.get("properties", {})
            for name, prop in props.items():
                outputs[name] = PortSpec(
                    name=name,
                    type=prop.get("type", "any"),
                    description=prop.get("description"),
                    required=False,
                    json_schema=prop if prop.get("type") == "object" else None,
                )

        return cls(inputs=inputs, outputs=outputs)

    def validate_inputs(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate input data against this signature.

        Returns:
            (is_valid, list of error messages)
        """
        errors: list[str] = []

        for name, port in self.inputs.items():
            if name not in data:
                if port.required and port.default is None:
                    errors.append(f"Missing required input: {name}")
            elif not port.accepts(data[name]):
                errors.append(f"Invalid type for input '{name}': expected {port.type}")

        return len(errors) == 0, errors

    def compatible_with(self, other: PathwaySignature) -> bool:
        """Check if this pathway's outputs can feed another's inputs.

        Used for Network composition validation.
        """
        for name, other_port in other.inputs.items():
            if not other_port.required:
                continue

            if name not in self.outputs:
                return False

            my_port = self.outputs[name]

            # Type compatibility (simplified - "any" is compatible with everything)
            if my_port.type != "any" and other_port.type != "any":
                if my_port.type != other_port.type:
                    return False

        return True


__all__ = [
    "PortSpec",
    "PathwaySignature",
]
