"""Common types and utilities for pathway_engine."""

from __future__ import annotations

from typing import Any, Self, TypeAlias

from pydantic import BaseModel, Field, TypeAdapter, model_validator
from pydantic import JsonValue as _PydanticJSONValue

from pathway_engine.domain.common.versioning import ALLOWED_VERSIONS, SCHEMA_VERSION

# ---------------------------------------------------------------------------
# Canonical JSON aliases for public contracts
# ---------------------------------------------------------------------------
#
# These types are the **only** approved way to represent JSON-shaped payloads
# in core DTOs and ports:
# - JSONValue: recursive JSON value (scalar, list, dict).
# - JsonObject: "bag of JSON" used at true JSON boundaries.
#
# Public contracts must **not** use untyped Any/object payload maps (e.g. "dict-of-any" /
# "mapping-of-any") for payloads; they must use these aliases or concrete
# DTOs under `pathway_engine.common.*`.

# Strict JSON value typing for public IO models (no Any).
# This is the canonical JSON-like type used across pathway_engine for public DTOs.
JSONScalar: TypeAlias = str | int | float | bool | None
# Delegate recursive JSON-compatibility to Pydantic's built-in JsonValue type to
# avoid self-recursive typing issues during schema generation.
JSONValue: TypeAlias = _PydanticJSONValue
JSONDict: TypeAlias = dict[str, JSONValue]
JSONList: TypeAlias = list[JSONValue]

# Generic JSON object bucket used at boundaries (HTTP, storage, metadata).
JsonObject: TypeAlias = dict[str, JSONValue]

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def ensure_json_value(value: Any) -> JSONValue:
    """Ensure a value is JSON-serializable."""
    ta: TypeAdapter[JSONValue] = TypeAdapter(JSONValue)
    return ta.validate_python(value)


def ensure_json_object(value: Any) -> JsonObject:
    """Ensure a value is a JSON object."""
    if not isinstance(value, dict):
        raise ValueError(f"Expected dict, got {type(value).__name__}")
    return {k: ensure_json_value(v) for k, v in value.items()}


def json_schema_from_model_type(model_type: type[BaseModel]) -> dict[str, Any]:
    """Extract JSON schema from a Pydantic model type."""
    return model_type.model_json_schema()


# ---------------------------------------------------------------------------
# Base models
# ---------------------------------------------------------------------------


class BaseVersionedModel(BaseModel):
    """Base model with schema versioning support."""

    schema_version: str = Field(default=SCHEMA_VERSION)

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        if self.schema_version not in ALLOWED_VERSIONS:
            raise ValueError(
                f"Unsupported schema version: {self.schema_version}. "
                f"Allowed versions: {ALLOWED_VERSIONS}"
            )
        return self


__all__ = [
    # JSON types
    "JSONScalar",
    "JSONValue",
    "JSONDict",
    "JSONList",
    "JsonObject",
    # Validation
    "ensure_json_value",
    "ensure_json_object",
    "json_schema_from_model_type",
    # Base models
    "BaseVersionedModel",
]
