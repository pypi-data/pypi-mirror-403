"""
Voice manipulation functionality for fmus-vox.

This module provides functionality for voice cloning, transformation, and
enhancement.
"""

from typing import Optional, Union, Dict, Any

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import VoiceError

# Import voice implementation
from fmus_vox.voice.cloner import VoiceCloner
from fmus_vox.voice.enhance import AudioEnhancer, enhance_audio, denoise_audio
from fmus_vox.voice.transform import (
    VoiceTransformer,
    transform_voice,
    shift_pitch,
    stretch_time
)
from fmus_vox.voice.clone import VoiceClone, clone, create_voice_model

def clone_voice(
    reference_audio: Union[str, Audio],
    text: str,
    output: Optional[str] = None,
    model: str = "yourtts",
    **kwargs
) -> Optional[Audio]:
    """
    Clone a voice from reference audio and synthesize text with it.

    This is a simple functional API for quick voice cloning.
    For more control, use the VoiceCloner class directly.

    Args:
        reference_audio: Reference audio to clone voice from (file path or Audio object)
        text: Text to synthesize with the cloned voice
        output: Path to save audio file (if None, returns Audio object)
        model: Model to use for voice cloning (yourtts, etc.)
        **kwargs: Additional model-specific parameters

    Returns:
        Audio object if output is None, otherwise None

    Raises:
        VoiceError: If voice cloning fails

    Examples:
        >>> # Clone voice and play it
        >>> audio = clone_voice("my_voice.wav", "Hello, this is my cloned voice")
        >>> audio.play()

        >>> # Clone voice and save to file
        >>> clone_voice("my_voice.wav", "Hello, this is my cloned voice", output="cloned.wav")
    """
    try:
        # Create voice cloner with specified model
        cloner = VoiceCloner(model=model, **kwargs)

        # Load reference audio if path is provided
        if isinstance(reference_audio, str):
            reference_audio = Audio.load(reference_audio)

        # Process reference audio and synthesize text
        voice_id = cloner.add_reference(reference_audio)
        audio = cloner.synthesize(text, voice_id)

        # Save to file if output path is provided
        if output:
            audio.save(output)
            return None

        return audio

    except Exception as e:
        raise VoiceError(f"Failed to clone voice: {str(e)}")
