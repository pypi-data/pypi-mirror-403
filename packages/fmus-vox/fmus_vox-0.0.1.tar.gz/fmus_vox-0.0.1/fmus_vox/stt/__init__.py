"""
Speech-to-Text (STT) functionality for fmus-vox.

This module provides functionality for transcribing speech to text
using various models and techniques.
"""

from typing import Optional, Union, Dict, Any

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import TranscriptionError

# Import model implementations
from fmus_vox.stt.transcriber import Transcriber

def transcribe(
    audio: Union[str, Audio],
    model: str = "whisper",
    language: Optional[str] = None,
    **kwargs
) -> str:
    """
    Transcribe audio to text using a specified model.

    This is a simple functional API for quick transcriptions.
    For more control, use the Transcriber class directly.

    Args:
        audio: Audio to transcribe (file path or Audio object)
        model: Model to use for transcription (whisper, wav2vec, etc.)
        language: Language code (if None, auto-detect)
        **kwargs: Additional model-specific parameters

    Returns:
        Transcribed text

    Raises:
        TranscriptionError: If transcription fails

    Examples:
        >>> # Transcribe an audio file
        >>> text = transcribe("recording.wav")
        >>> print(text)

        >>> # Transcribe with a specific model and language
        >>> text = transcribe("recording.wav", model="whisper-large", language="en")
    """
    try:
        # Create transcriber with specified model
        transcriber = Transcriber(model=model, **kwargs)

        # Load audio if path is provided
        if isinstance(audio, str):
            audio = Audio.load(audio)

        # Transcribe audio
        return transcriber.transcribe(audio, language=language)

    except Exception as e:
        raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")
