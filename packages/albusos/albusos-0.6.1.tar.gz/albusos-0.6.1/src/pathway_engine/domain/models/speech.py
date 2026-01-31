"""Speech modality models - TTS and ASR.

These define the contracts for speech nodes.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# =============================================================================
# TEXT-TO-SPEECH (TTS)
# =============================================================================


class TTSInput(BaseModel):
    """Input for text-to-speech nodes."""

    model_config = {"extra": "allow"}

    text: str
    voice: str = "alloy"  # Provider-specific voice name
    model: str = "tts-1"  # tts-1, tts-1-hd, etc.
    provider: Literal["openai"] = "openai"

    # Audio format
    format: Literal["mp3", "wav", "ogg", "flac", "opus", "aac"] = "mp3"
    speed: float = 1.0  # 0.25 to 4.0

    context: dict[str, Any] = Field(default_factory=dict)


class TTSOutput(BaseModel):
    """Output from text-to-speech nodes."""

    model_config = {"extra": "allow"}

    audio_data: bytes | None = None
    audio_base64: str | None = None
    audio_url: str | None = None

    # Convenience HTML snippet for rendering
    html_audio_tag: str | None = None

    format: str = "mp3"
    duration_seconds: float | None = None

    model: str = ""
    voice: str = ""
    provider: str = ""

    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# AUTOMATIC SPEECH RECOGNITION (ASR)
# =============================================================================


class ASRInput(BaseModel):
    """Input for automatic speech recognition (speech-to-text) nodes."""

    model_config = {"extra": "allow"}

    audio_data: bytes | None = None
    audio_base64: str | None = None
    audio_url: str | None = None

    model: str = "whisper-1"
    provider: Literal["openai"] = "openai"

    # Transcription options
    language: str | None = None  # ISO-639-1 code (e.g., "en", "es")
    prompt: str | None = None  # Optional context/vocabulary hint
    temperature: float = 0.0

    # Output format
    response_format: Literal[
        "json", "text", "srt", "verbose_json", "vtt"
    ] = "json"

    # Timestamps
    timestamp_granularities: list[Literal["word", "segment"]] | None = None

    context: dict[str, Any] = Field(default_factory=dict)


class ASROutput(BaseModel):
    """Output from automatic speech recognition nodes."""

    model_config = {"extra": "allow"}

    text: str  # Transcribed text
    language: str | None = None  # Detected language

    # Detailed segments (if verbose_json requested)
    segments: list[dict[str, Any]] = Field(default_factory=list)
    words: list[dict[str, Any]] = Field(default_factory=list)

    duration_seconds: float | None = None

    model: str = ""
    provider: str = ""

    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "TTSInput",
    "TTSOutput",
    "ASRInput",
    "ASROutput",
]
