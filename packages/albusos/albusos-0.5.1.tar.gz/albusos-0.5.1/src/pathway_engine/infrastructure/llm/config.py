from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pathway_engine.domain.common import JSONValue, ensure_json_object
from pathway_engine.domain.common.errors import ValidationError

from .enums import ModelProvider

__all__: list[str] = [
    "LLMConfig",
    "LlmCallConfig",
]


class LLMConfig(BaseModel):
    """Provider-agnostic configuration for LLM calls.

    This is a pure contract/DTO:
    - No registry/model-catalog lookups.
    - No environment-specific details (keys, base URLs, orgs).
    - No provider SDK coupling.
    """

    provider: ModelProvider | None = Field(
        default=None,
        description="Logical LLM provider (optional). Runtime routing is typically model-driven.",
    )

    model: Optional[str] = Field(
        default=None,
        description="Logical model name for the provider (e.g. 'gpt-4o', 'claude-3-5-sonnet').",
    )

    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature; None to use provider default.",
    )

    max_output_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum output tokens to generate; None to use provider default.",
    )

    max_context_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Soft cap on total context window (prompt + completion).",
    )

    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling probability; None to use provider default.",
    )

    frequency_penalty: Optional[float] = Field(
        default=None,
        description="Provider-specific frequency penalty; None to use default.",
    )

    presence_penalty: Optional[float] = Field(
        default=None,
        description="Provider-specific presence penalty; None to use default.",
    )

    seed: Optional[int] = Field(
        default=None,
        description="Optional deterministic sampling seed (provider support varies).",
    )

    stop_sequences: Optional[list[str]] = Field(
        default=None,
        description="Optional list of stop sequences.",
    )

    # Logical, provider-agnostic extension point for compile-time hints.
    # Runtime/environment details (API keys, base URLs, org routing, etc.)
    # are owned by runtime configuration, not plan contracts.
    # Custom parameters are strictly JSONValue-typed so they can safely cross
    # compile/runtime boundaries and be persisted or logged when needed.
    custom_parameters: JSONValue | None = Field(
        default=None,
        description="Additional provider-agnostic parameters for logical configuration.",
    )

    # In core, we want strict schemas: no random extras sneaking in.
    model_config = ConfigDict(extra="allow")

    # --- Validators -----------------------------------------------------

    @field_validator("model")
    @classmethod
    def _validate_model(cls, v: Optional[str]) -> Optional[str]:
        def _model_name_must_be_non_empty() -> ValidationError:
            return ValidationError(
                "Model name, if provided, must be a non-empty string."
            )

        if v is None:
            return v
        v = v.strip()
        if not v:
            raise _model_name_must_be_non_empty()
        # No registry or provider-catalog checks here; that belongs in builder/runtime.
        return v

    @field_validator("stop_sequences")
    @classmethod
    def _validate_stop_sequences(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return None
        cleaned = [s for s in (s.strip() for s in v) if s]
        return cleaned or None

    @field_validator("custom_parameters")
    @classmethod
    def _validate_custom_parameters_is_object_or_none(cls, v: object) -> object:
        if v is None:
            return v
        ensure_json_object(v)
        return v


class LlmCallConfig(BaseModel):
    """Logical LLM call configuration used by LLM- and Agent-style nodes.

    This DTO is intentionally narrow:
    - It composes the shared low-level call parameters for a single LLM call.
    - It is a pure value object (no provider SDKs, no kernel, no ExecutionCtx).
    - It is derived from node configs (`LLMNodeConfig`, `RouterNodeConfig`) and
      is not itself part of the SSOT node_config JSON schema.
    """

    model_config = ConfigDict(extra="allow")

    prompt: str = Field(
        ...,
        description="Prompt template or instruction text for the LLM call.",
    )
    llm_config: LLMConfig = Field(
        ...,
        description="Provider-agnostic LLM configuration for this call.",
    )
