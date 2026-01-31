"""Tool capabilities - Specifications and Runtime Protocol.

This module defines the contract for tools ("The Body's hands").
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pathway_engine.domain.common import JsonObject

# =============================================================================
# LLM TOOL DEFINITIONS (For OpenAI/Anthropic/etc.)
# =============================================================================


class LLMTool(BaseModel):
    """Provider-agnostic tool/function definition for LLM tool calling."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    description: str | None = None
    parameters_schema: JsonObject = Field(
        default_factory=dict, description="JSON Schema object for tool parameters."
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        s = str(v or "").strip()
        if not s:
            raise ValueError("tool_name_empty")
        return s


ToolChoice = Literal["auto", "none"] | str | dict[str, Any] | None


# =============================================================================
# TOOL SPECIFICATION (System Tools)
# =============================================================================


class HttpToolConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    url: str = Field(min_length=1)
    headers: JsonObject = Field(default_factory=dict)
    query: JsonObject = Field(default_factory=dict)
    body: Any | None = None

    # Optional auth binding. v1 supports env-backed secrets only.
    # Example: "STRIPE_API_KEY"
    auth_env: str | None = None


class JsonRpcToolConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str = Field(min_length=1)
    method: str = Field(min_length=1)
    headers: JsonObject = Field(default_factory=dict)
    params: JsonObject = Field(default_factory=dict)
    auth_env: str | None = None


class McpToolConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    server_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)


class CompositeToolConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    pathway_id: str = Field(min_length=1)
    # Optional selector for the returned value, e.g.:
    # - "outputs" (default) -> full outputs dict
    # - "node_id" -> output of a specific step
    # - "node_id.result" -> attribute access on BaseModel outputs
    output_selector: str | None = None


class PythonToolConfig(BaseModel):
    """Local Python execution tool config (sandboxed subprocess).

    Notes:
    - This is intentionally "local-only" for v1: no network installs, no external deps.
    - Determinism default: `allow_site_packages=False` (runs with -I/-S).
    """

    model_config = ConfigDict(extra="allow")

    timeout_ms: int = Field(default=10_000, ge=1, le=600_000)
    memory_mb: int = Field(default=256, ge=16, le=16_384)
    cpu_seconds: int = Field(default=5, ge=1, le=600)
    max_output_kb: int = Field(default=256, ge=1, le=8192)
    allow_site_packages: bool = False
    python_executable: str | None = None


class BuiltinToolConfig(BaseModel):
    """Config for builtin/canonical tools (implemented in Python runtime)."""

    model_config = ConfigDict(extra="allow")

    # Handler name in builtins registry (optional, defaults to tool id)
    handler: str | None = None


ToolKind = Literal["http", "jsonrpc", "mcp", "composite", "python", "builtin"]


class ToolSpec(BaseModel):
    """Canonical persisted tool spec for user-defined tools."""

    model_config = ConfigDict(extra="allow")

    scope: str = Field(default="system", min_length=1)
    id: str = Field(
        min_length=1, description="Tool id, referenced by pathway tool_name."
    )
    name: str | None = None
    description: str | None = None

    # Implementation reference (kind + version).
    # Examples: "http:v1", "jsonrpc:v1", "mcp:v1", "composite:v1"
    impl_ref: str = Field(min_length=1)
    kind: ToolKind

    # JSON-schema-ish contracts (subset enforced by runtime).
    input_schema: JsonObject = Field(default_factory=dict)
    output_schema: JsonObject = Field(default_factory=dict)

    tags: list[str] = Field(default_factory=list)
    version: int = 1

    config: (
        HttpToolConfig
        | JsonRpcToolConfig
        | McpToolConfig
        | CompositeToolConfig
        | PythonToolConfig
        | BuiltinToolConfig
    )

    @field_validator("impl_ref")
    @classmethod
    def _validate_impl_ref(cls, v: str) -> str:
        s = str(v).strip()
        if not s:
            raise ValueError("impl_ref_empty")
        if ":" not in s:
            raise ValueError("impl_ref_must_include_version")
        return s

    def key(self) -> str:
        """Stable key used by APIs (scope-qualified)."""
        return f"{self.scope}:{self.id}"


class SchemaValidationError(Exception):
    """Raised when tool inputs/outputs fail schema validation."""

    pass


__all__ = [
    "CompositeToolConfig",
    "HttpToolConfig",
    "JsonRpcToolConfig",
    "LLMTool",
    "McpToolConfig",
    "PythonToolConfig",
    "SchemaValidationError",
    "ToolChoice",
    "ToolKind",
    "ToolSpec",
]


# Built-in tool schemas (for filtering in modules)
BUILTIN_TOOL_SCHEMAS: set[str] = set()
