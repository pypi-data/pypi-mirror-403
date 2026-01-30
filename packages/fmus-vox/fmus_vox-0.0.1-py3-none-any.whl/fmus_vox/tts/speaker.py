"""
Base Speaker class for text-to-speech functionality.

This module provides the Speaker class which is the common interface for
all text-to-speech models in fmus-vox.
"""

import os
from typing import Any, Dict, List, Optional, Union, Generator
from pathlib import Path
import asyncio

from fmus_vox.core.audio import Audio
from fmus_vox.core.config import get_config
from fmus_vox.core.errors import SynthesisError, ModelError
from fmus_vox.core.utils import get_logger, LazyLoader, timed

class SpeechResult:
    """
    Container for speech synthesis results, including audio and metadata.
    """

    def __init__(self,
                audio: Audio,
                voice_id: str,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a speech result.

        Args:
            audio: Synthesized audio
            voice_id: ID of the voice used
            metadata: Additional synthesis metadata
        """
        self.audio = audio
        self.voice_id = voice_id
        self.metadata = metadata or {}

    def save(self, path: Union[str, Path]) -> str:
        """Save synthesized audio to file."""
        return self.audio.save(path)

    def play(self) -> None:
        """Play synthesized audio."""
        self.audio.play()

class Speaker:
    """
    Base class for text-to-speech synthesis.

    This class provides the common interface for all TTS models
    and handles model loading, voice selection, and synthesis.

    Args:
        model: Name of the model to use (vits, coqui, etc.)
        voice: Voice ID or name to use
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Registry of available model implementations
    _model_registry = {}

    @classmethod
    def register_model(cls, name: str, implementation: type) -> None:
        """
        Register a model implementation.

        Args:
            name: Model name
            implementation: Model implementation class
        """
        cls._model_registry[name] = implementation

    def __new__(cls, model: str = "vits", **kwargs) -> "Speaker":
        """
        Create a new Speaker instance of the appropriate subclass.

        Args:
            model: Name of the model to use
            **kwargs: Additional model-specific parameters

        Returns:
            Speaker instance

        Raises:
            ModelError: If the model is not supported
        """
        if cls is Speaker:
            # Determine which implementation to use based on model name
            if model.startswith("vits"):
                from fmus_vox.tts.vits import VitsSpeaker
                return VitsSpeaker(model=model, **kwargs)
            elif model.startswith("coqui"):
                from fmus_vox.tts.coqui import CoquiSpeaker
                return CoquiSpeaker(model=model, **kwargs)
            elif model.startswith("fastspeech"):
                from fmus_vox.tts.fastspeech import FastSpeechSpeaker
                return FastSpeechSpeaker(model=model, **kwargs)
            elif model.startswith("elevenlabs") or model.startswith("eleven"):
                from fmus_vox.tts.elevenlabs import ElevenLabsSpeaker
                return ElevenLabsSpeaker(model=model, **kwargs)
            elif model in cls._model_registry:
                implementation = cls._model_registry[model]
                return implementation(model=model, **kwargs)
            else:
                raise ModelError(f"Unsupported TTS model: {model}")
        else:
            # If called from a subclass, use normal instantiation
            return super().__new__(cls)

    def __init__(self, model: str = "vits", voice: str = "default",
                device: Optional[str] = None, **kwargs):
        """
        Initialize the speaker.

        Args:
            model: Name of the model to use
            voice: Voice ID or name to use
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.config = get_config()

        self.model_name = model
        self.voice_id = voice
        self.device = device or self.config.get_device()
        self.model_params = kwargs

        # Voice settings
        self.speed = kwargs.get("speed", 1.0)
        self.pitch = kwargs.get("pitch", 0.0)
        self.style = kwargs.get("style", "neutral")

        # Lazy-loaded model
        self._model = LazyLoader(self._load_model)

        self.logger.debug(f"Initialized {self.__class__.__name__} with model={model}, voice={voice}")

    def _load_model(self) -> Any:
        """
        Load the TTS model.

        Returns:
            Loaded model

        Raises:
            ModelError: If model loading fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    @timed
    def speak(self, text: str) -> Audio:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize

        Returns:
            Audio object with synthesized speech

        Raises:
            SynthesisError: If synthesis fails
        """
        result = self.speak_with_metadata(text)
        return result.audio

    @timed
    def speak_with_metadata(self, text: str) -> SpeechResult:
        """
        Synthesize speech from text with additional metadata.

        Args:
            text: Text to synthesize

        Returns:
            SpeechResult object

        Raises:
            SynthesisError: If synthesis fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    async def speak_async(self, text: str) -> Audio:
        """
        Synthesize speech from text asynchronously.

        Args:
            text: Text to synthesize

        Returns:
            Audio object with synthesized speech

        Raises:
            SynthesisError: If synthesis fails
        """
        result = await self.speak_with_metadata_async(text)
        return result.audio

    async def speak_with_metadata_async(self, text: str) -> SpeechResult:
        """
        Synthesize speech from text asynchronously with additional metadata.

        Args:
            text: Text to synthesize

        Returns:
            SpeechResult object

        Raises:
            SynthesisError: If synthesis fails
        """
        # Default implementation runs synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.speak_with_metadata, text
        )

    def stream(self, text_generator: Generator[str, None, None]) -> Generator[Audio, None, None]:
        """
        Stream synthesis for incoming text chunks.

        Args:
            text_generator: Generator yielding text chunks

        Yields:
            Audio object for each synthesized chunk

        Raises:
            SynthesisError: If synthesis fails
        """
        for text in text_generator:
            if text.strip():  # Skip empty text
                yield self.speak(text)

    # Fluent interface for setting voice properties
    def set_voice(self, voice_id: str) -> "Speaker":
        """Set the voice to use."""
        self.voice_id = voice_id
        return self

    def set_speed(self, speed: float) -> "Speaker":
        """Set the speaking speed (1.0 is normal)."""
        self.speed = speed
        return self

    def set_pitch(self, pitch: float) -> "Speaker":
        """Set the voice pitch in semitones (0.0 is normal)."""
        self.pitch = pitch
        return self

    def set_style(self, style: str) -> "Speaker":
        """Set the speaking style (e.g., 'neutral', 'happy', 'sad')."""
        self.style = style
        return self

    # Alternative names for fluent interface
    def voice(self, voice_id: str) -> "Speaker":
        """Set the voice to use (alias for set_voice)."""
        return self.set_voice(voice_id)

    def speed(self, speed: float) -> "Speaker":
        """Set the speaking speed (alias for set_speed)."""
        return self.set_speed(speed)

    def pitch(self, pitch: float) -> "Speaker":
        """Set the voice pitch (alias for set_pitch)."""
        return self.set_pitch(pitch)

    def style(self, style: str) -> "Speaker":
        """Set the speaking style (alias for set_style)."""
        return self.set_style(style)

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with id, name, and language
        """
        raise NotImplementedError("Subclasses must implement this method")
