"""
Voice cloning interface module.

This module provides simple functions for voice cloning that wrap
the VoiceCloner class for easier usage.
"""

from typing import Optional, Union, Dict, Any
from pathlib import Path

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import VoiceError
from fmus_vox.voice.cloner import VoiceCloner


class VoiceClone:
    """
    Simplified voice cloning interface.

    This class provides a simpler interface to the VoiceCloner class
    for common voice cloning tasks.

    Args:
        model: Voice cloning model to use
        **kwargs: Additional model parameters
    """

    def __init__(self, model: str = "yourtts", **kwargs):
        """
        Initialize the voice cloner.

        Args:
            model: Voice cloning model to use
            **kwargs: Additional model parameters
        """
        self._cloner = VoiceCloner(model=model, **kwargs)
        self._voice_ids: Dict[str, str] = {}

    def add_reference(self, audio: Union[str, Audio], name: Optional[str] = None) -> str:
        """
        Add a reference audio for voice cloning.

        Args:
            audio: Reference audio (file path or Audio object)
            name: Optional name for this voice

        Returns:
            Voice ID
        """
        if isinstance(audio, str):
            audio = Audio.load(audio)

        voice_id = self._cloner.add_reference(audio)

        # Store name if provided
        if name:
            self._voice_ids[name] = voice_id

        return voice_id

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        output: Optional[str] = None
    ) -> Audio:
        """
        Synthesize speech with cloned voice.

        Args:
            text: Text to synthesize
            voice: Voice name or ID (uses first if None)
            output: Optional output file path

        Returns:
            Synthesized audio
        """
        # Resolve voice ID
        voice_id = voice
        if voice and voice in self._voice_ids:
            voice_id = self._voice_ids[voice]
        elif not voice_id and self._cloner._voices:
            voice_id = list(self._cloner._voices.keys())[0]
        elif not voice_id:
            raise VoiceError("No voice available. Add a reference audio first.")

        audio = self._cloner.synthesize(text, voice_id)

        if output:
            audio.save(output)

        return audio

    def list_voices(self) -> list:
        """List available voices."""
        return list(self._cloner._voices.keys())


def clone(
    reference: Union[str, Audio],
    text: str,
    output: Optional[str] = None,
    model: str = "yourtts"
) -> Audio:
    """
    Quick voice cloning function.

    Args:
        reference: Reference audio (file path or Audio object)
        text: Text to synthesize
        output: Optional output file path
        model: Voice cloning model to use

    Returns:
        Synthesized audio

    Examples:
        >>> audio = clone("my_voice.wav", "Hello, this is my cloned voice")
        >>> audio.play()

        >>> clone("my_voice.wav", "Save this", output="cloned.wav")
    """
    cloner = VoiceClone(model=model)
    cloner.add_reference(reference)
    return cloner.synthesize(text, output=output)


def create_voice_model(model: str = "yourtts", **kwargs) -> VoiceClone:
    """
    Create a voice model for cloning.

    Args:
        model: Voice cloning model to use
        **kwargs: Additional model parameters

    Returns:
        VoiceClone instance

    Examples:
        >>> voice_model = create_voice_model()
        >>> voice_model.add_reference("voice1.wav", name="john")
        >>> voice_model.add_reference("voice2.wav", name="jane")
        >>> audio = voice_model.synthesize("Hello", voice="john")
    """
    return VoiceClone(model=model, **kwargs)
