"""
Text-to-Speech (TTS) functionality for fmus-vox.

This module provides functionality for synthesizing text into speech
using various models and techniques.
"""

from typing import Optional, Union, Dict, Any

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import SynthesisError

# Import speaker implementation
from fmus_vox.tts.speaker import Speaker

def speak(
    text: str,
    voice: str = "default",
    output: Optional[str] = None,
    model: str = "vits",
    **kwargs
) -> Optional[Audio]:
    """
    Synthesize speech from text using a specified model and voice.

    This is a simple functional API for quick speech synthesis.
    For more control, use the Speaker class directly.

    Args:
        text: Text to synthesize
        voice: Voice to use (name or ID)
        output: Path to save audio file (if None, returns Audio object)
        model: Model to use for synthesis (vits, coqui, etc.)
        **kwargs: Additional model-specific parameters

    Returns:
        Audio object if output is None, otherwise None

    Raises:
        SynthesisError: If synthesis fails

    Examples:
        >>> # Synthesize speech and play it
        >>> audio = speak("Hello, world!")
        >>> audio.play()

        >>> # Synthesize speech and save to file
        >>> speak("Hello, world!", output="hello.wav")
    """
    try:
        # Create speaker with specified model and voice
        speaker = Speaker(model=model, voice=voice, **kwargs)

        # Synthesize speech
        audio = speaker.speak(text)

        # Save to file if output path is provided
        if output:
            audio.save(output)
            return None

        return audio

    except Exception as e:
        raise SynthesisError(f"Failed to synthesize speech: {str(e)}")
