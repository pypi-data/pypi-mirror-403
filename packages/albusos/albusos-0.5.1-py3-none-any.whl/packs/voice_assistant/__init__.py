"""Voice Assistant Pack - Conversational speech interface.

This pack demonstrates ASRNode + LLM + TTSNode integration:
1. Transcribes user speech to text
2. Processes with LLM for response
3. Speaks the response back

Usage:
    from packs.voice_assistant import VOICE_ASSISTANT_PACK
    
    # Run the pathway
    result = await runtime.run_pathway(
        "voice_assistant.respond.v1",
        inputs={"audio_base64": "<base64 audio>"}
    )
    # Returns: response text, audio_base64, transcript, etc.
"""

from packs.voice_assistant.pack import VOICE_ASSISTANT_PACK

__all__ = ["VOICE_ASSISTANT_PACK"]
