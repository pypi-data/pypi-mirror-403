"""Speech tools - TTS and ASR.

These tools provide audio I/O capabilities in a way that is usable from pathways:
- speech.tts: text -> audio (base64)
- speech.asr: audio (base64) -> text
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.llm import LLMProviderError, get_provider
from stdlib.llm.capability_routing import get_model_for_capability
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


def _mime_for_audio_format(fmt: str) -> str:
    f = (fmt or "").strip().lower()
    if f == "wav":
        return "audio/wav"
    if f == "ogg":
        return "audio/ogg"
    return "audio/mpeg"  # mp3 default


@register_tool(
    "speech.tts",
    description="Text-to-speech. Returns audio bytes as base64 plus a ready-to-render <audio> HTML snippet.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to speak"},
            "voice": {
                "type": "string",
                "description": "Voice name (provider-specific). For OpenAI: alloy, verse, etc.",
                "default": "alloy",
            },
            "format": {
                "type": "string",
                "description": "Audio format: mp3|wav|ogg",
                "default": "mp3",
            },
            "model": {
                "type": "string",
                "description": "TTS model to use. If omitted, auto-select via capability routing.",
            },
        },
        "required": ["text"],
    },
)
async def speech_tts(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    text = str(inputs.get("text", "")).strip()
    if not text:
        return {"success": False, "error": "text is required"}

    voice = str(inputs.get("voice") or "alloy").strip() or "alloy"
    fmt = str(inputs.get("format") or "mp3").strip().lower() or "mp3"

    model = str(inputs.get("model") or "").strip()
    if not model:
        model = get_model_for_capability("speech.tts") or "tts-1"

    try:
        provider = get_provider(model)
        if not hasattr(provider, "tts"):
            return {
                "success": False,
                "error": f"provider_missing_tts:{type(provider).__name__}",
                "model": model,
            }

        audio_bytes: bytes = await provider.tts(text=text, model=model, voice=voice, format=fmt)  # type: ignore[attr-defined]
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        mime = _mime_for_audio_format(fmt)

        player_html = f"""<!doctype html>
<html>
  <head><meta charset="utf-8" /></head>
  <body>
    <audio controls src="data:{mime};base64,{audio_b64}"></audio>
  </body>
</html>
"""

        return {
            "success": True,
            "text": text,
            "model": model,
            "provider": "openai" if model.lower().startswith(("tts-",)) else "unknown",
            "voice": voice,
            "format": fmt,
            "mime_type": mime,
            "bytes": len(audio_bytes),
            "audio_base64": audio_b64,
            "player_html": player_html,
        }
    except LLMProviderError as e:
        return {
            "success": False,
            "error": str(e.message),
            "provider": e.provider,
            "model": e.model,
            "is_transient": e.is_transient,
        }
    except Exception as e:
        logger.warning("speech.tts failed: %s", e)
        return {"success": False, "error": str(e), "model": model}


@register_tool(
    "speech.asr",
    description="Speech-to-text (ASR). Provide audio bytes as base64 and get transcript text.",
    parameters={
        "type": "object",
        "properties": {
            "audio_base64": {
                "type": "string",
                "description": "Base64-encoded audio bytes",
            },
            "model": {
                "type": "string",
                "description": "ASR model (default: auto-select via capability routing)",
            },
            "language": {
                "type": "string",
                "description": "Optional language hint (e.g. 'en')",
            },
            "prompt": {
                "type": "string",
                "description": "Optional transcription prompt",
            },
        },
        "required": ["audio_base64"],
    },
)
async def speech_asr(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    audio_b64 = str(inputs.get("audio_base64", "")).strip()
    if not audio_b64:
        return {"success": False, "error": "audio_base64 is required"}

    model = str(inputs.get("model") or "").strip()
    if not model:
        model = get_model_for_capability("speech.asr") or "whisper-1"

    language = inputs.get("language")
    prompt = inputs.get("prompt")

    try:
        provider = get_provider(model)
        if not hasattr(provider, "asr"):
            return {
                "success": False,
                "error": f"provider_missing_asr:{type(provider).__name__}",
                "model": model,
            }

        text: str = await provider.asr(  # type: ignore[attr-defined]
            audio_base64=audio_b64,
            model=model,
            language=str(language).strip() if language else None,
            prompt=str(prompt) if prompt else None,
        )
        return {
            "success": True,
            "model": model,
            "provider": (
                "openai" if model.lower().startswith(("whisper",)) else "unknown"
            ),
            "text": text,
        }
    except LLMProviderError as e:
        return {
            "success": False,
            "error": str(e.message),
            "provider": e.provider,
            "model": e.model,
            "is_transient": e.is_transient,
        }
    except Exception as e:
        logger.warning("speech.asr failed: %s", e)
        return {"success": False, "error": str(e), "model": model}


__all__ = ["speech_tts", "speech_asr"]
