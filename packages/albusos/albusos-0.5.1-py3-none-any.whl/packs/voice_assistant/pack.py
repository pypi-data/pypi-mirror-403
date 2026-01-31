"""Voice Assistant Pack - Voice conversation skills.

Agents consume this pack:
    agent_builder().use_pack("voice_assistant")

Skills (pathways):
    - respond.v1   Full voice conversation (ASR → LLM → TTS)
    - speak.v1     Text to speech only
"""

from packs.registry import deployable
from pathway_engine.domain.pack import pack_builder
from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes import (
    ASRNode,
    TTSNode,
    LLMNode,
)


ASSISTANT_SYSTEM_PROMPT = """You are a helpful, friendly voice assistant.

Guidelines:
- Keep responses concise (1-3 sentences) since they'll be spoken aloud
- Be conversational and natural
- Don't use markdown or formatting - just natural speech
- Match the user's energy and tone"""


def build_respond_pathway():
    """Full voice conversation: speech in, speech out.
    
    Pipeline:
        audio → ASRNode (transcribe) → LLMNode (respond) → TTSNode (speak)
    
    Inputs:
        - audio_base64: Base64-encoded audio of user speech
    
    Outputs:
        - transcript: What the user said
        - response: Assistant's text response  
        - audio_base64: Spoken response as MP3
    """
    transcribe_node = ASRNode(
        id="transcribe",
        model="whisper-1",
    )
    think_node = LLMNode(
        id="think",
        prompt="{{prompt}}",
        model="gpt-4o-mini",
        system=ASSISTANT_SYSTEM_PROMPT,
        temperature=0.7,
        max_tokens=200,
    )
    speak_node = TTSNode(
        id="speak",
        voice="nova",
        model="tts-1",
        format="mp3",
    )
    
    return Pathway(
        id="voice_assistant.respond.v1",
        name="Voice Response",
        description="Transcribe speech, generate response, speak it back",
        nodes={
            "transcribe": transcribe_node,
            "think": think_node,
            "speak": speak_node,
        },
        connections=[
            # Input audio flows to transcribe
            Connection(from_node="input", to_node="transcribe"),
            # Transcript flows to LLM (text -> prompt)
            Connection(
                from_node="transcribe",
                to_node="think",
                from_output="text",
                to_input="prompt",
            ),
            # LLM response flows to TTS (response -> text)
            Connection(
                from_node="think",
                to_node="speak",
                from_output="response",
                to_input="text",
            ),
            # All outputs flow to final output
            Connection(from_node="transcribe", to_node="output"),
            Connection(from_node="think", to_node="output"),
            Connection(from_node="speak", to_node="output"),
        ],
    )


def build_speak_pathway():
    """Text-to-speech only.
    
    Inputs:
        - text: Text to speak
        - voice: Voice name (optional, default: nova)
    
    Outputs:
        - audio_base64: MP3 audio
    """
    speak_node = TTSNode(
        id="speak",
        voice="nova",
        model="tts-1",
        format="mp3",
    )
    
    return Pathway(
        id="voice_assistant.speak.v1",
        name="Speak Text",
        description="Convert text to spoken audio",
        nodes={
            "speak": speak_node,
        },
        connections=[
            Connection(from_node="input", to_node="speak"),
            Connection(from_node="speak", to_node="output"),
        ],
    )


@deployable
def VOICE_ASSISTANT_PACK():
    """Build the Voice Assistant pack."""
    return (
        pack_builder()
        .id("voice_assistant")
        .name("Voice Assistant")
        .description("Conversational voice interface using ASR + LLM + TTS")
        .pathway("voice_assistant.respond.v1", build_respond_pathway)
        .pathway("voice_assistant.speak.v1", build_speak_pathway)
        .build()
    )
