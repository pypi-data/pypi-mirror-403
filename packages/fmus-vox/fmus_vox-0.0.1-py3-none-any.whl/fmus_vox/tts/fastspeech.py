"""
FastSpeech model implementation for text-to-speech.

This module provides the FastSpeechSpeaker class which uses FastSpeech models
for fast and efficient speech synthesis.
"""

from typing import Any, Dict, List, Optional
from fmus_vox.core.utils import get_logger
from fmus_vox.tts.vits import VitsSpeaker, SpeechResult


class FastSpeechSpeaker(VitsSpeaker):
    """
    Speaker using FastSpeech models.

    FastSpeech is a fast, robust and controllable text-to-speech model
    that enables fast speech synthesis without autoregressive decoding.

    Args:
        model: FastSpeech model variant
        voice: Voice ID or name to use
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available FastSpeech voices
    _available_voices = [
        {"id": "default", "name": "Default Voice", "language": "en"},
        {"id": "fast", "name": "Fast Voice", "language": "en"},
    ]

    def __init__(self, model: str = "fastspeech", voice: str = "default",
                device: Optional[str] = None, **kwargs):
        """
        Initialize the FastSpeech speaker.

        Args:
            model: FastSpeech model variant
            voice: Voice ID or name to use
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        # Initialize with VITS base class (sharing TTS library)
        super().__init__(model=model, voice=voice, device=device, **kwargs)

        self.logger.debug(f"Initialized FastSpeechSpeaker with voice={voice}")

    def _load_model(self) -> Any:
        """
        Load the FastSpeech model.

        Returns:
            Loaded FastSpeech model (or None if TTS library not installed)
        """
        # FastSpeech uses the same TTS library
        return super()._load_model()

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with id, name, and language
        """
        return self._available_voices.copy()
