from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .attachments import LLMAttachment
from .config import LLMConfig
from .tools import LLMTool, ToolChoice


class LLMRequest(BaseModel):
    """Provider-agnostic LLM request DTO for the runtime port boundary.

    This is a strict, serialized-friendly contract:
    - No provider SDK types
    - No call-site **kwargs leakage
    - Explicit support for chat-style messages (incl. multimodal content arrays)
    """

    model_config = ConfigDict(extra="allow")

    task: str = Field(
        default="chat",
        description="Logical task for model selection (chat/vision/code/...).",
    )

    # Inputs: callers may supply either prompt (+ optional system) OR explicit messages.
    prompt: Optional[str] = Field(
        default=None, description="User prompt text (ignored if messages provided)."
    )
    system: Optional[str] = Field(
        default=None, description="Optional system instruction."
    )

    # OpenAI-style messages. Content may be a string or a structured array (e.g. vision content parts).
    # We keep this as plain JSON-friendly dicts to avoid SDK coupling.
    messages: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Chat messages. If provided, takes precedence over prompt/system.",
    )

    attachments: list[LLMAttachment] | None = Field(
        default=None,
        description="Optional attachments (e.g. images). Only used when messages is not provided.",
    )

    response_format: Literal["text", "json"] = Field(
        default="text",
        description="Desired response format (best-effort across providers).",
    )

    output_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional JSON schema for structured outputs (runtime-enforced).",
    )

    tools: list[LLMTool] | None = Field(
        default=None,
        description="Optional tool/function definitions for tool calling.",
    )
    tool_choice: ToolChoice = Field(
        default=None,
        description="Tool choice policy: 'auto'|'none'|tool_name|provider-specific object.",
    )

    llm: LLMConfig = Field(
        ...,
        description="Provider-agnostic LLM configuration (model/temperature/token budget/etc).",
    )

    @model_validator(mode="after")
    def _validate_inputs(self) -> "LLMRequest":
        if self.messages is not None:
            if not isinstance(self.messages, list) or not self.messages:
                raise ValueError("messages must be a non-empty list when provided")
            if self.attachments:
                raise ValueError("attachments_not_allowed_when_messages_provided")
            return self

        p = (self.prompt or "").strip()
        if not p and not self.attachments:
            raise ValueError("Either messages or a non-empty prompt must be provided")
        return self


__all__ = ["LLMRequest"]
