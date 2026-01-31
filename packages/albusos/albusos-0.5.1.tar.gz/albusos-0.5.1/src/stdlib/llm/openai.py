"""OpenAI Adapter - Private implementation for llm tools.

Thin adapter that translates tool inputs → OpenAI SDK calls → normalized outputs.
All cross-cutting concerns (retry, audit) are handled by the tools layer.
"""

from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any, Optional

from stdlib.llm import (
    LLMEmbedResult,
    LLMGenerateResult,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None  # type: ignore


class OpenAIAdapter:
    """OpenAI provider adapter."""

    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

    # Model pricing (per 1M tokens)
    PRICING = {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-5": {"input": 2.5, "output": 10.0},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: Optional[AsyncOpenAI] = None

    def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            if AsyncOpenAI is None:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )

            timeout_s = float(os.getenv("AGENT_STDLIB_OPENAI_TIMEOUT_S", "60"))
            timeout_s = max(5.0, min(timeout_s, 600.0))

            try:
                self._client = AsyncOpenAI(
                    api_key=self.api_key, timeout=timeout_s, max_retries=0
                )
            except TypeError:
                self._client = AsyncOpenAI(api_key=self.api_key)

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
        max_tokens: int = 1200,
        response_format: str = "text",
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str | dict[str, Any]] = None,
        messages: Optional[list[dict[str, Any]]] = None,
        images: Optional[list[str]] = None,
    ) -> LLMGenerateResult:
        """Generate text using OpenAI.

        Args:
            prompt: User prompt
            model: Model to use (default: gpt-4o)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            response_format: "text" or "json"
            tools: Tool definitions for function calling
            tool_choice: Tool choice constraint
            messages: Full message array (overrides prompt/system)
            images: List of base64-encoded images for vision (gpt-4o, etc.)

        Returns:
            LLMGenerateResult with content and metadata
        """
        client = self._ensure_client()
        model = (model or "").strip() or self.DEFAULT_MODEL
        model_l = model.lower()

        # Build messages
        if messages is not None:
            msgs = list(messages)
        else:
            msgs = []
            if system:
                msgs.append({"role": "system", "content": system})

            # Handle vision: build content array with text + images
            if images:
                content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
                for img in images:
                    # Handle both raw base64 and data URLs
                    if img.startswith("data:"):
                        image_url = img
                    else:
                        # Detect mime type from base64 prefix
                        if img.startswith("/9j/"):
                            mime = "image/jpeg"
                        elif img.startswith("iVBORw"):
                            mime = "image/png"
                        else:
                            mime = "image/jpeg"  # Default
                        image_url = f"data:{mime};base64,{img}"
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    })
                msgs.append({"role": "user", "content": content})
            else:
                msgs.append({"role": "user", "content": prompt})

        # Build request
        req: dict[str, Any] = {"model": model, "messages": msgs}

        # Temperature (some models don't support it)
        if not model_l.startswith("o1"):
            req["temperature"] = temperature

        # Max tokens
        if model_l.startswith("gpt-5"):
            req["max_completion_tokens"] = max_tokens
        else:
            req["max_tokens"] = max_tokens

        # JSON mode - OpenAI requires "json" to appear in messages when using json_object mode
        if response_format == "json":
            req["response_format"] = {"type": "json_object"}
            # Check if "json" already appears in the messages
            all_content = " ".join(str(m.get("content", "")) for m in msgs).lower()
            if "json" not in all_content:
                # Append instruction to last user message or add system message
                for i in range(len(msgs) - 1, -1, -1):
                    if msgs[i].get("role") == "user":
                        msgs[i]["content"] = (
                            msgs[i]["content"] + "\n\nRespond with JSON."
                        )
                        break
                else:
                    msgs.append({"role": "system", "content": "Respond with JSON."})

        # Tools
        if tools:
            req["tools"] = tools
        if tool_choice is not None:
            if isinstance(tool_choice, str):
                if tool_choice in ("auto", "none"):
                    req["tool_choice"] = tool_choice
                else:
                    req["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
            else:
                req["tool_choice"] = tool_choice

        try:
            response = await client.chat.completions.create(**req)
            msg = response.choices[0].message
            content = msg.content or ""

            # Usage
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = (usage.total_tokens if usage else 0) or (
                input_tokens + output_tokens
            )

            # Tool calls
            tool_calls_normalized = None
            if msg.tool_calls:
                tool_calls_normalized = []
                for tc in msg.tool_calls:
                    tool_calls_normalized.append(
                        {
                            "id": tc.id,
                            "name": tc.function.name if tc.function else None,
                            "arguments": tc.function.arguments if tc.function else None,
                        }
                    )

            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return LLMGenerateResult(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost_usd=cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider="openai",
                finish_reason=response.choices[0].finish_reason,
                tool_calls=tool_calls_normalized,
                metadata={
                    "provider": "openai",
                    "api": "chat.completions",
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
                provider="openai",
                model=model,
                is_transient=is_transient,
            ) from e

    async def embed(
        self,
        texts: list[str],
        *,
        model: Optional[str] = None,
    ) -> LLMEmbedResult:
        """Generate embeddings using OpenAI.

        Args:
            texts: List of texts to embed
            model: Embedding model (default: text-embedding-3-small)

        Returns:
            LLMEmbedResult with vectors
        """
        client = self._ensure_client()
        model = (model or "").strip() or self.DEFAULT_EMBEDDING_MODEL

        try:
            response = await client.embeddings.create(
                model=model,
                input=texts,
            )

            vectors = [item.embedding for item in response.data]
            total_tokens = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(model, total_tokens, 0)

            return LLMEmbedResult(
                vectors=vectors,
                model=model,
                tokens_used=total_tokens,
                cost_usd=cost,
                provider="openai",
            )

        except Exception as e:
            msg_str = str(e).lower()
            is_transient = any(
                tok in msg_str
                for tok in ("timeout", "rate limit", "429", "500", "502", "503", "504")
            )
            raise LLMProviderError(
                message=str(e),
                provider="openai",
                model=model,
                is_transient=is_transient,
            ) from e

    async def tts(
        self,
        *,
        text: str,
        model: str = "tts-1",
        voice: str = "alloy",
        format: str = "mp3",
    ) -> bytes:
        """Generate speech audio from text using OpenAI TTS.

        Returns raw audio bytes in the requested format.
        """
        client = self._ensure_client()

        text = (text or "").strip()
        if not text:
            raise LLMProviderError(
                message="text is required",
                provider="openai",
                model=model,
                is_transient=False,
            )

        fmt = (format or "mp3").strip().lower()
        if fmt not in {"mp3", "wav", "ogg"}:
            raise LLMProviderError(
                message=f"unsupported_format:{fmt}",
                provider="openai",
                model=model,
                is_transient=False,
            )

        try:
            # OpenAI Python SDK (v1.x): client.audio.speech.create(...)
            resp = await client.audio.speech.create(
                model=model,
                voice=voice,  # type: ignore[arg-type]
                input=text,
                response_format=fmt,  # type: ignore[arg-type]
            )
            # Different SDK versions expose bytes differently.
            # HttpxBinaryResponseContent has both read() (sync) and content (sync)
            if hasattr(resp, "content"):
                data = resp.content  # type: ignore[attr-defined]
            elif hasattr(resp, "read"):
                data = resp.read()  # type: ignore[func-returns-value]
            elif hasattr(resp, "data"):
                data = resp.data  # type: ignore[attr-defined]
            else:
                # As a last resort, attempt to coerce to bytes.
                data = bytes(resp)  # type: ignore[arg-type]
            if not isinstance(data, (bytes, bytearray)):
                raise TypeError("TTS response did not contain bytes")
            return bytes(data)
        except LLMProviderError:
            raise
        except Exception as e:
            msg_str = str(e).lower()
            is_transient = any(
                tok in msg_str
                for tok in ("timeout", "rate limit", "429", "500", "502", "503", "504")
            )
            raise LLMProviderError(
                message=str(e),
                provider="openai",
                model=model,
                is_transient=is_transient,
            ) from e

    async def asr(
        self,
        *,
        audio_base64: str,
        model: str = "whisper-1",
        language: str | None = None,
        prompt: str | None = None,
    ) -> str:
        """Transcribe speech audio to text using OpenAI Whisper.

        Inputs are passed as base64-encoded audio bytes.
        """
        client = self._ensure_client()

        b64 = (audio_base64 or "").strip()
        if not b64:
            raise LLMProviderError(
                message="audio_base64 is required",
                provider="openai",
                model=model,
                is_transient=False,
            )

        try:
            audio_bytes = base64.b64decode(b64, validate=False)
        except Exception as e:
            raise LLMProviderError(
                message=f"invalid_base64:{e}",
                provider="openai",
                model=model,
                is_transient=False,
            ) from e

        try:
            buf = io.BytesIO(audio_bytes)
            # The OpenAI SDK expects a "file-like" with a name attribute.
            setattr(buf, "name", "audio.wav")
            req: dict[str, Any] = {"file": buf, "model": model}
            if language:
                req["language"] = language
            if prompt:
                req["prompt"] = prompt
            resp = await client.audio.transcriptions.create(**req)
            text = getattr(resp, "text", None)
            if not isinstance(text, str):
                # Some SDK versions return dict-like payloads
                if isinstance(resp, dict) and isinstance(resp.get("text"), str):
                    return resp["text"]
                raise TypeError("ASR response missing 'text'")
            return text
        except LLMProviderError:
            raise
        except Exception as e:
            msg_str = str(e).lower()
            is_transient = any(
                tok in msg_str
                for tok in ("timeout", "rate limit", "429", "500", "502", "503", "504")
            )
            raise LLMProviderError(
                message=str(e),
                provider="openai",
                model=model,
                is_transient=is_transient,
            ) from e

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost in USD."""
        pricing = self.PRICING.get(model, self.PRICING["gpt-4o"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


__all__ = ["OpenAIAdapter"]
