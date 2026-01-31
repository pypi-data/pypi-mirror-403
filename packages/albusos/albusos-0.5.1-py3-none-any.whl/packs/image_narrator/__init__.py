"""Image Narrator Pack - Describe images aloud.

This pack demonstrates VisionNode + TTSNode integration:
1. Analyzes an image using vision-capable LLM
2. Speaks the description using text-to-speech

Usage:
    from packs.image_narrator import IMAGE_NARRATOR_PACK
    
    # Run the pathway
    result = await runtime.run_pathway(
        "image_narrator.describe.v1",
        inputs={"image_url": "https://example.com/photo.jpg"}
    )
    # Returns: audio_base64, description text, etc.
"""

from packs.image_narrator.pack import IMAGE_NARRATOR_PACK

__all__ = ["IMAGE_NARRATOR_PACK"]
