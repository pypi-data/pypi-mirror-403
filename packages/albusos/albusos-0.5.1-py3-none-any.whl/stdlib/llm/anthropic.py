"""Anthropic Adapter - Private implementation for llm tools.

Thin adapter that translates tool inputs → Anthropic SDK calls → normalized outputs.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from stdlib.llm import (
    LLMGenerateResult,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None  # type: ignore


class AnthropicAdapter:
    """Anthropic provider adapter."""

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    # Model pricing (per 1M tokens)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: Optional[AsyncAnthropic] = None

    def _ensure_client(self) -> AsyncAnthropic:
        if self._client is None:
            if AsyncAnthropic is None:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )

            timeout_s = float(os.getenv("AGENT_STDLIB_ANTHROPIC_TIMEOUT_S", "60"))
            timeout_s = max(5.0, min(timeout_s, 600.0))

            try:
                self._client = AsyncAnthropic(
                    api_key=self.api_key, timeout=timeout_s, max_retries=0
                )
            except TypeError:
                self._client = AsyncAnthropic(api_key=self.api_key)

        return self._client

    async def aclose(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            try:
                if hasattr(self._client, "close"):
                    await self._client.close()
            except Exception:
                pass
            self._client = None

    async def generate(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str | dict[str, Any]] = None,
        messages: Optional[list[dict[str, Any]]] = None,
        images: Optional[list[str]] = None,
    ) -> LLMGenerateResult:
        """Generate text using Anthropic Claude.

        Args:
            prompt: User prompt
            model: Model to use (default: claude-3-5-sonnet)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            response_format: "text" or "json"
            tools: Tool definitions for function calling
            tool_choice: Tool choice constraint
            messages: Full message array (overrides prompt/system)
            images: List of base64-encoded images for vision (claude-3 models)

        Returns:
            LLMGenerateResult with content and metadata
        """
        client = self._ensure_client()
        model = (model or "").strip() or self.DEFAULT_MODEL

        # Build request
        req: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Messages
        if messages is not None:
            # Convert from OpenAI format to Anthropic format
            anthropic_messages = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "system":
                    # System goes in separate field
                    if not req.get("system"):
                        req["system"] = content
                else:
                    anthropic_messages.append({"role": role, "content": content})
            req["messages"] = (
                anthropic_messages
                if anthropic_messages
                else [{"role": "user", "content": prompt}]
            )
        elif images:
            # Build content array with text + images for vision
            content_parts: list[dict[str, Any]] = []
            for img in images:
                # Detect mime type
                if img.startswith("/9j/"):
                    media_type = "image/jpeg"
                elif img.startswith("iVBORw"):
                    media_type = "image/png"
                else:
                    media_type = "image/jpeg"  # Default
                content_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img,
                    },
                })
            content_parts.append({"type": "text", "text": prompt})
            req["messages"] = [{"role": "user", "content": content_parts}]
        else:
            req["messages"] = [{"role": "user", "content": prompt}]

        # System prompt
        if system:
            existing = req.get("system", "")
            req["system"] = f"{existing}\n{system}".strip() if existing else system

        # JSON mode via prompting
        if response_format == "json":
            if req.get("system"):
                req["system"] += "\nAlways respond with valid JSON."
            else:
                req["system"] = "Always respond with valid JSON."

        # Tools (Anthropic format)
        if tools:
            anthropic_tools = []
            for t in tools:
                anthropic_tools.append(
                    {
                        "name": t.get("function", {}).get("name") or t.get("name"),
                        "description": t.get("function", {}).get("description")
                        or t.get("description"),
                        "input_schema": t.get("function", {}).get("parameters")
                        or t.get("input_schema", {}),
                    }
                )
            req["tools"] = anthropic_tools

        if tool_choice is not None:
            if isinstance(tool_choice, str):
                if tool_choice == "auto":
                    req["tool_choice"] = {"type": "auto"}
                elif tool_choice == "none":
                    req["tool_choice"] = {"type": "none"}
                else:
                    req["tool_choice"] = {"type": "tool", "name": tool_choice}
            else:
                req["tool_choice"] = tool_choice

        try:
            response = await client.messages.create(**req)

            # Extract content
            content = ""
            tool_calls_normalized = None

            for block in response.content:
                if hasattr(block, "text"):
                    content += str(block.text)
                elif getattr(block, "type", None) == "tool_use":
                    if tool_calls_normalized is None:
                        tool_calls_normalized = []
                    tool_calls_normalized.append(
                        {
                            "id": getattr(block, "id", None),
                            "name": getattr(block, "name", None),
                            "arguments": getattr(block, "input", None),
                        }
                    )

            # Usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return LLMGenerateResult(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost_usd=cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider="anthropic",
                finish_reason=response.stop_reason,
                tool_calls=tool_calls_normalized,
                metadata={
                    "provider": "anthropic",
                },
            )

        except Exception as e:
            msg_str = str(e).lower()
            is_transient = any(
                tok in msg_str
                for tok in ("timeout", "rate limit", "429", "500", "502", "503", "504")
            )
            raise LLMProviderError(
                message=str(e),
                provider="anthropic",
                model=model,
                is_transient=is_transient,
            ) from e

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost in USD."""
        # Find pricing by model prefix
        pricing = self.PRICING.get(model)
        if not pricing:
            for key in self.PRICING:
                if model.startswith(key.split("-20")[0]):
                    pricing = self.PRICING[key]
                    break
        if not pricing:
            pricing = self.PRICING["claude-3-5-sonnet-20241022"]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


__all__ = ["AnthropicAdapter"]
