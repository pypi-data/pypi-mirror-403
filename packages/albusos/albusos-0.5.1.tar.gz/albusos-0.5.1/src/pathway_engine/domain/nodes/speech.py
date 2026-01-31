"""Speech nodes - Text-to-speech and speech recognition.

First-class pathway nodes for speech capabilities.
Uses tools via context to maintain layering (pathway_engine cannot import stdlib).
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from pathway_engine.domain.context import Context
from pathway_engine.domain.models.speech import (
    TTSOutput,
    ASROutput,
)
from pathway_engine.domain.nodes.base import NodeBase

logger = logging.getLogger(__name__)


class TTSNode(NodeBase):
    """Convert text to speech audio.

    Uses speech.tts tool via context.

    Usage:
        node = TTSNode(
            id="speak",
            voice="alloy",
            model="tts-1",
        )

    Inputs:
        text: The text to convert to speech

    Outputs:
        audio_base64: Base64-encoded audio
        html_audio_tag: Ready-to-render HTML audio element
    """

    type: Literal["tts"] = "tts"
    voice: str = "alloy"
    model: str = "tts-1"
    format: str = "mp3"
    speed: float = 1.0

    async def compute(
        self, inputs: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Convert text to speech."""
        text = inputs.get("text", "")
        if not text:
            return TTSOutput(
                audio_base64="",
                format=self.format,
                model=self.model,
                voice=self.voice,
                provider="openai",
            ).model_dump()

        voice = inputs.get("voice", self.voice)
        model = inputs.get("model", self.model)
        audio_format = inputs.get("format", self.format)
        speed = inputs.get("speed", self.speed)

        # Use speech.tts tool
        speech_tts = ctx.tools.get("speech.tts")
        if speech_tts:
            result = await speech_tts(
                {
                    "text": text,
                    "voice": voice,
                    "model": model,
                    "format": audio_format,
                    "speed": speed,
                },
                ctx,
            )
            return result

        # Fallback: return error if tool not available
        return TTSOutput(
            format=audio_format,
            model=model,
            voice=voice,
            provider="openai",
            metadata={"error": "speech.tts tool not available"},
        ).model_dump()


class ASRNode(NodeBase):
    """Convert speech audio to text (transcription).

    Uses speech.asr tool via context.

    Usage:
        node = ASRNode(
            id="transcribe",
            model="whisper-1",
        )

    Inputs:
        audio_base64: Base64-encoded audio
        audio_data: Raw audio bytes
        audio_url: URL to audio file

    Outputs:
        text: Transcribed text
        language: Detected language
    """

    type: Literal["asr"] = "asr"
    model: str = "whisper-1"
    language: str | None = None
    temperature: float = 0.0
    response_format: str = "json"

    async def compute(
        self, inputs: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Transcribe audio to text."""
        audio_base64 = inputs.get("audio_base64") or inputs.get("audio")
        audio_url = inputs.get("audio_url")

        if not audio_base64 and not audio_url:
            return ASROutput(
                text="",
                model=self.model,
                provider="openai",
                metadata={"error": "No audio provided"},
            ).model_dump()

        model = inputs.get("model", self.model)
        language = inputs.get("language", self.language)

        # Use speech.asr tool
        speech_asr = ctx.tools.get("speech.asr")
        if speech_asr:
            result = await speech_asr(
                {
                    "audio_base64": audio_base64,
                    "model": model,
                    "language": language,
                },
                ctx,
            )
            return result

        # Fallback: return error if tool not available
        return ASROutput(
            text="",
            model=model,
            provider="openai",
            metadata={"error": "speech.asr tool not available"},
        ).model_dump()


__all__ = [
    "TTSNode",
    "ASRNode",
]
