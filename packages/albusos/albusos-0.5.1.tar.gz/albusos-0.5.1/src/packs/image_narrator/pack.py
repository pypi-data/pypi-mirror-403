"""Image Narrator Pack - Describe images aloud.

Agents consume this pack:
    agent_builder().use_pack("image_narrator")

Skills (pathways):
    - describe.v1   Analyze image and speak description (Vision + TTS)
"""

from packs.registry import deployable
from pathway_engine.domain.pack import pack_builder
from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes import (
    VisionNode,
    TTSNode,
)


def build_describe_pathway():
    """Full image description with spoken narration.
    
    Pipeline:
        image → VisionNode (detailed analysis) → TTSNode (speak)
    
    Inputs:
        - image_url: URL to the image
        - image_base64: OR base64-encoded image
    
    Outputs:
        - response: Text description from vision
        - audio_base64: Spoken description as MP3
    """
    analyze_node = VisionNode(
        id="analyze",
        prompt="""Describe this image in vivid detail for someone who cannot see it.

Include:
- Main subject and what they're doing
- Setting and environment  
- Colors, lighting, mood
- Any text visible in the image

Keep it under 3 paragraphs, natural and engaging.""",
        model="gpt-4o",
        max_output_tokens=500,
    )
    speak_node = TTSNode(
        id="speak",
        voice="nova",
        model="tts-1",
        format="mp3",
    )
    
    return Pathway(
        id="image_narrator.describe.v1",
        name="Describe Image Aloud",
        description="Analyze an image and speak the description",
        nodes={
            "analyze": analyze_node,
            "speak": speak_node,
        },
        connections=[
            # Input image flows to vision node
            Connection(from_node="input", to_node="analyze"),
            # Vision response flows to TTS
            Connection(
                from_node="analyze",
                to_node="speak",
                from_output="response",
                to_input="text",
            ),
            # Outputs flow to final output
            Connection(from_node="analyze", to_node="output"),
            Connection(from_node="speak", to_node="output"),
        ],
    )


@deployable
def IMAGE_NARRATOR_PACK():
    """Build the Image Narrator pack."""
    return (
        pack_builder()
        .id("image_narrator")
        .name("Image Narrator")
        .description("Describe images aloud using Vision + TTS")
        .pathway("image_narrator.describe.v1", build_describe_pathway)
        .build()
    )
