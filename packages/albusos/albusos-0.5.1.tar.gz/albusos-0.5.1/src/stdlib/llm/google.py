"""Google/Gemini Adapter - Private implementation for llm tools.

Thin adapter that translates tool inputs → Google SDK calls → normalized outputs.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from stdlib.llm import (
    LLMGenerateResult,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore


class GoogleAdapter:
    """Google Gemini provider adapter."""

    DEFAULT_MODEL = "gemini-1.5-pro"

    # Model pricing (per 1M tokens)
    PRICING = {
        "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
        "gemini-1.0-pro": {"input": 0.5, "output": 1.5},
    }

    def __init__(self, api_key: str):
        if genai is None:
            raise ImportError(
                "google-generativeai package not installed. Run: pip install google-generativeai"
            )

        self.api_key = api_key
        genai.configure(api_key=api_key)
        self._clients: dict[str, Any] = {}

    def _get_client(self, model: str) -> Any:
        """Get or create client for model."""
        if model not in self._clients:
            self._clients[model] = genai.GenerativeModel(model)
        return self._clients[model]

    async def aclose(self) -> None:
        """Close connections (no-op for Google)."""
        self._clients.clear()

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
        """Generate text using Google Gemini.

        Args:
            prompt: User prompt
            model: Model to use (default: gemini-1.5-pro)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            response_format: "text" or "json"
            tools: Not supported yet
            tool_choice: Not supported yet
            messages: Full message array (converted to prompt)
            images: List of base64-encoded images for vision

        Returns:
            LLMGenerateResult with content and metadata
        """
        if tools or tool_choice:
            raise LLMProviderError(
                message="Tools not supported by Google adapter",
                provider="google",
                model=model,
                is_transient=False,
            )

        model = (model or "").strip() or self.DEFAULT_MODEL
        client = self._get_client(model)

        # Build prompt
        if messages is not None:
            # Convert messages to single prompt
            parts = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "system":
                    parts.insert(0, f"System: {content}")
                else:
                    parts.append(f"{role.capitalize()}: {content}")
            full_prompt = "\n\n".join(parts)
        else:
            full_prompt = prompt

        if system:
            full_prompt = f"{system}\n\n{full_prompt}"

        # JSON mode via prompting
        if response_format == "json":
            full_prompt += "\n\nRespond with valid JSON only."

        # Build content parts for vision
        import base64
        content_parts: list[Any] = []
        if images:
            for img in images:
                # Gemini uses inline_data with base64
                if img.startswith("/9j/"):
                    mime_type = "image/jpeg"
                elif img.startswith("iVBORw"):
                    mime_type = "image/png"
                else:
                    mime_type = "image/jpeg"
                content_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img,
                    }
                })
        content_parts.append(full_prompt)

        # Generation config
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            candidate_count=1,
        )

        try:
            response = await client.generate_content_async(
                content_parts if images else full_prompt,
                generation_config=generation_config,
            )

            content = response.text

            # Estimate tokens (Google doesn't always provide exact counts)
            input_tokens = int(len(full_prompt.split()) * 1.3)
            output_tokens = int(len(content.split()) * 1.3)
            total_tokens = input_tokens + output_tokens

            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return LLMGenerateResult(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost_usd=cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider="google",
                finish_reason=None,
                tool_calls=None,
                metadata={
                    "provider": "google",
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
                provider="google",
                model=model,
                is_transient=is_transient,
            ) from e

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost in USD."""
        pricing = self.PRICING.get(model, self.PRICING["gemini-1.5-pro"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


__all__ = ["GoogleAdapter"]
