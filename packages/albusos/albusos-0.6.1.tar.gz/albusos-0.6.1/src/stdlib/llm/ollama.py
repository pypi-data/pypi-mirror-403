"""Ollama Adapter - Local model inference via Ollama.

Ollama provides a simple way to run LLMs locally:
- Install: https://ollama.ai
- Run: ollama serve
- Pull models: ollama pull llama3

Environment:
    OLLAMA_HOST: Base URL (default: http://localhost:11434)

Model naming:
    - "ollama:llama3" → uses ollama provider explicitly
    - "llama3", "mistral", "phi3", "qwen2" → auto-routed to ollama if available
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import aiohttp

from stdlib.llm.providers_init import (
    LLMGenerateResult,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

# Models that should auto-route to Ollama (if Ollama is available)
OLLAMA_MODEL_PREFIXES = (
    "llama",
    "mistral",
    "phi",
    "qwen",
    "gemma",
    "codellama",
    "deepseek",
    "starcoder",
    "wizard",
    "vicuna",
    "orca",
    "neural",
    "dolphin",
    "nous",
    "tinyllama",
    "ollama:",
)


class OllamaAdapter:
    """Adapter for Ollama local inference.

    Ollama exposes an OpenAI-compatible API at /v1/chat/completions,
    plus its native API at /api/generate and /api/chat.

    We use the native API for more control.
    """

    def __init__(
        self,
        host: str | None = None,
        timeout: float = 120.0,
    ):
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip(
            "/"
        )
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        # pytest / embedding runtimes may swap event loops between calls.
        # aiohttp sessions are bound to the loop they were created with.
        # If the loop changed (or is closed), recreate the session.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if self._session is not None:
            try:
                sess_loop = getattr(self._session, "_loop", None)
                if (
                    sess_loop is not None
                    and hasattr(sess_loop, "is_closed")
                    and sess_loop.is_closed()
                ):
                    await self.aclose()
                elif (
                    loop is not None and sess_loop is not None and sess_loop is not loop
                ):
                    await self.aclose()
            except Exception:
                # Best-effort cleanup; we'll recreate below if needed.
                try:
                    await self.aclose()
                except Exception:
                    pass

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def aclose(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _normalize_model(self, model: str) -> str:
        """Strip ollama: prefix if present."""
        if model.startswith("ollama:"):
            return model[7:]
        return model

    async def generate(
        self,
        prompt: str,
        model: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str = "text",
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMGenerateResult:
        """Generate text using Ollama.

        Uses /api/chat for conversational interface.
        """
        model = self._normalize_model(model)
        session = await self._get_session()

        # Build messages
        if messages:
            chat_messages = messages
        else:
            chat_messages = []
            if system:
                chat_messages.append({"role": "system", "content": system})
            chat_messages.append({"role": "user", "content": prompt})

        # Build request
        request_body: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # JSON mode
        if response_format == "json":
            request_body["format"] = "json"

        # Tool calling (if supported by model)
        if tools:
            request_body["tools"] = self._convert_tools(tools)

        try:
            async with session.post(
                f"{self.host}/api/chat",
                json=request_body,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise LLMProviderError(
                        message=f"Ollama error ({resp.status}): {error_text}",
                        provider="ollama",
                        model=model,
                        is_transient=resp.status >= 500,
                    )

                data = await resp.json()

        except aiohttp.ClientError as e:
            raise LLMProviderError(
                message=f"Connection error: {e}. Is Ollama running? (ollama serve)",
                provider="ollama",
                model=model,
                is_transient=True,
            )

        # Parse response
        message = data.get("message", {})
        content = message.get("content", "")

        # Token counts (Ollama provides these)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)
        total_tokens = prompt_eval_count + eval_count

        # Tool calls (if any)
        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": json.dumps(
                            tc.get("function", {}).get("arguments", {})
                        ),
                    },
                }
                for i, tc in enumerate(message["tool_calls"])
            ]

        return LLMGenerateResult(
            content=content,
            model=model,
            tokens_used=total_tokens,
            cost_usd=0.0,  # Local models are free!
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            provider="ollama",
            finish_reason=data.get("done_reason", "stop"),
            tool_calls=tool_calls,
            metadata={
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "eval_duration": data.get("eval_duration"),
            },
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tools to Ollama format."""
        ollama_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                ollama_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": func.get("name", ""),
                            "description": func.get("description", ""),
                            "parameters": func.get("parameters", {}),
                        },
                    }
                )
        return ollama_tools

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models in Ollama."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.host}/api/tags") as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("models", [])
        except Exception:
            return []

    async def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        session = await self._get_session()

        try:
            async with session.get(
                f"{self.host}/api/tags", timeout=aiohttp.ClientTimeout(total=2.0)
            ) as resp:
                return resp.status == 200
        except Exception:
            return False


def is_ollama_model(model: str) -> bool:
    """Check if a model should be routed to Ollama."""
    model_lower = model.lower()
    return any(model_lower.startswith(prefix) for prefix in OLLAMA_MODEL_PREFIXES)


__all__ = [
    "OllamaAdapter",
    "OLLAMA_MODEL_PREFIXES",
    "is_ollama_model",
]
