"""
Coqui TTS model implementation for text-to-speech.

This module provides the CoquiSpeaker class which uses Coqui's TTS models
for speech synthesis.
"""

from typing import Any, Dict, List, Optional
from fmus_vox.core.utils import get_logger
from fmus_vox.tts.vits import VitsSpeaker, SpeechResult


class CoquiSpeaker(VitsSpeaker):
    """
    Speaker using Coqui TTS models.

    Coqui TTS is an open-source deep learning text-to-speech framework
    with support for many languages and voices.

    Args:
        model: Coqui model variant
        voice: Voice ID or name to use
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available Coqui voices
    _available_voices = [
        {"id": "default", "name": "Default Voice", "language": "en"},
        {"id": "female", "name": "Female Voice", "language": "en"},
        {"id": "male", "name": "Male Voice", "language": "en"},
    ]

    def __init__(self, model: str = "coqui", voice: str = "default",
                device: Optional[str] = None, **kwargs):
        """
        Initialize the Coqui speaker.

        Args:
            model: Coqui model variant
            voice: Voice ID or name to use
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        # Initialize with VITS base class
        super().__init__(model=model, voice=voice, device=device, **kwargs)

        self.logger.debug(f"Initialized CoquiSpeaker with voice={voice}")

    def _load_model(self) -> Any:
        """
        Load the Coqui TTS model.

        Returns:
            Loaded Coqui model (or None if TTS library not installed)
        """
        # Coqui uses the same TTS library as VITS
        return super()._load_model()

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with id, name, and language
        """
        return self._available_voices.copy()
