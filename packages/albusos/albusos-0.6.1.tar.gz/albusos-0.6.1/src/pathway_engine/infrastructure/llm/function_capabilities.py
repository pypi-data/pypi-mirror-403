from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pathway_engine.domain.common import JSONValue, ensure_json_object


class LLMToolFunctionCapabilityModel(BaseModel):
    """Provider-ready function capability spec for an LLM node."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Function name visible to provider")
    description: Optional[str] = Field(default=None)
    parameters_schema: JSONValue = Field(
        default_factory=dict, description="Strict JSON Schema object"
    )

    @field_validator("parameters_schema")
    @classmethod
    def _validate_parameters_schema_is_object(cls, v: object) -> object:
        ensure_json_object(v)
        return v


class LLMFunctionCapabilitiesModel(BaseModel):
    """All callable functions exposed by a specific LLM node.

    Compile-time contract:
    - Instances are constructed by Builder (see ``pathway_engine.emitters.llm_capabilities``)
      from graph/node IO models and `function_routes`.
    - Runtime code must not re-derive or mutate capabilities; it
      only consumes these models as part of compiled plan artifacts.
    """

    model_config = ConfigDict(extra="allow")

    llm_node_id: str = Field(..., description="ID of the LLM node")
    tool_functions: List[LLMToolFunctionCapabilityModel] = Field(default_factory=list)


__all__ = ["LLMToolFunctionCapabilityModel", "LLMFunctionCapabilitiesModel"]
