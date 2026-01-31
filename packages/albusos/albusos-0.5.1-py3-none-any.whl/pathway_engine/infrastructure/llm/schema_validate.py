"""Schema validation utilities for tool inputs/outputs.

This logic was previously in `pathway_engine.capabilities.tools.schema_validate`.
It provides "subset validation" - ensuring a payload satisfies a schema,
but allowing extra fields if the schema doesn't forbid them.
"""

from __future__ import annotations

from typing import Any

from pathway_engine.infrastructure.llm.tools import SchemaValidationError


def validate_schema_subset(schema: dict[str, Any], data: Any, path: str = "") -> None:
    """Validate that `data` satisfies `schema`.

    This is a lightweight, recursive validator that checks types and required fields.
    It is NOT a full JSON Schema validator (use `jsonschema` library for that if needed).

    Features:
    - Checks `type` (string, number, boolean, array, object)
    - Checks `required` fields in objects
    - Recurses into `properties` for objects
    - Recurses into `items` for arrays
    """
    if not isinstance(schema, dict):
        return  # No schema constraints

    # Type check
    schema_type = schema.get("type")
    if schema_type:
        if schema_type == "string" and not isinstance(data, str):
            raise SchemaValidationError(
                f"{path}: expected string, got {type(data).__name__}"
            )
        elif schema_type == "number" and not isinstance(data, (int, float)):
            raise SchemaValidationError(
                f"{path}: expected number, got {type(data).__name__}"
            )
        elif schema_type == "integer" and not isinstance(data, int):
            raise SchemaValidationError(
                f"{path}: expected integer, got {type(data).__name__}"
            )
        elif schema_type == "boolean" and not isinstance(data, bool):
            raise SchemaValidationError(
                f"{path}: expected boolean, got {type(data).__name__}"
            )
        elif schema_type == "array" and not isinstance(data, list):
            raise SchemaValidationError(
                f"{path}: expected array, got {type(data).__name__}"
            )
        elif schema_type == "object" and not isinstance(data, dict):
            raise SchemaValidationError(
                f"{path}: expected object, got {type(data).__name__}"
            )

    # Object validation
    if schema_type == "object" and isinstance(data, dict):
        # Check required fields
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if field not in data:
                    raise SchemaValidationError(
                        f"{path}: missing required field '{field}'"
                    )

        # Check properties
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, prop_schema in properties.items():
                if key in data:
                    validate_schema_subset(
                        prop_schema, data[key], path=f"{path}.{key}" if path else key
                    )

    # Array validation
    if schema_type == "array" and isinstance(data, list):
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for i, item in enumerate(data):
                validate_schema_subset(items_schema, item, path=f"{path}[{i}]")


__all__ = ["validate_schema_subset"]
