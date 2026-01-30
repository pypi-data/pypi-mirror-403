"""
Voice cloning functionality for fmus-vox.

This module provides the VoiceCloner class which is the base for all
voice cloning implementations.
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fmus_vox.core.audio import Audio
from fmus_vox.core.config import get_config
from fmus_vox.core.errors import VoiceError, ModelError
from fmus_vox.core.utils import get_logger, LazyLoader, timed

class Voice:
    """
    Container for voice information and metadata.
    """

    def __init__(self,
                voice_id: str,
                name: Optional[str] = None,
                reference_audio: Optional[Audio] = None,
                embeddings: Optional[Any] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a voice.

        Args:
            voice_id: Unique identifier for the voice
            name: Display name for the voice
            reference_audio: Reference audio for the voice
            embeddings: Voice embeddings or model-specific data
            metadata: Additional voice metadata
        """
        self.voice_id = voice_id
        self.name = name or voice_id
        self.reference_audio = reference_audio
        self.embeddings = embeddings
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation (without audio data)."""
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "metadata": self.metadata
        }

class VoiceCloner:
    """
    Base class for voice cloning.

    This class provides the common interface for all voice cloning models
    and handles voice management, cloning, and synthesis.

    Args:
        model: Name of the model to use (yourtts, etc.)
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

    def __new__(cls, model: str = "yourtts", **kwargs) -> "VoiceCloner":
        """
        Create a new VoiceCloner instance of the appropriate subclass.

        Args:
            model: Name of the model to use
            **kwargs: Additional model-specific parameters

        Returns:
            VoiceCloner instance

        Raises:
            ModelError: If the model is not supported
        """
        if cls is VoiceCloner:
            # Determine which implementation to use based on model name
            if model.startswith("yourtts"):
                from fmus_vox.voice.yourtts import YourTTSCloner
                return YourTTSCloner(model=model, **kwargs)
            elif model.startswith("sv2tts"):
                from fmus_vox.voice.sv2tts import SV2TTSCloner
                return SV2TTSCloner(model=model, **kwargs)
            elif model in cls._model_registry:
                implementation = cls._model_registry[model]
                return implementation(model=model, **kwargs)
            else:
                raise ModelError(f"Unsupported voice cloning model: {model}")
        else:
            # If called from a subclass, use normal instantiation
            return super().__new__(cls)

    def __init__(self, model: str = "yourtts", device: Optional[str] = None, **kwargs):
        """
        Initialize the voice cloner.

        Args:
            model: Name of the model to use
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.config = get_config()

        self.model_name = model
        self.device = device or self.config.get_device()
        self.model_params = kwargs

        # Dictionary of registered voices
        self.voices = {}

        # Lazy-loaded models
        self._encoder = LazyLoader(self._load_encoder)
        self._synthesizer = LazyLoader(self._load_synthesizer)

        self.logger.debug(f"Initialized {self.__class__.__name__} with model={model}")

    def _load_encoder(self) -> Any:
        """
        Load the voice encoder model.

        Returns:
            Loaded encoder model

        Raises:
            ModelError: If model loading fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    def _load_synthesizer(self) -> Any:
        """
        Load the speech synthesizer model.

        Returns:
            Loaded synthesizer model

        Raises:
            ModelError: If model loading fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    @timed
    def add_reference(self, audio: Union[str, Audio],
                     name: Optional[str] = None) -> str:
        """
        Add a reference voice from audio.

        Args:
            audio: Reference audio (file path or Audio object)
            name: Display name for the voice (if None, use generated ID)

        Returns:
            Voice ID that can be used for synthesis

        Raises:
            VoiceError: If reference processing fails
        """
        try:
            # Load audio if path is provided
            if isinstance(audio, str):
                audio = Audio.load(audio)
                # Use filename as name if not provided
                if name is None:
                    name = Path(audio).stem

            # Resample if needed
            if audio.sample_rate != 16000:
                audio = audio.resample(target_sr=16000)

            # Generate voice ID
            voice_id = str(uuid.uuid4())

            # Process for voice embedding (to be implemented by subclasses)
            embeddings = self._process_reference(audio)

            # Create voice object
            voice = Voice(
                voice_id=voice_id,
                name=name or voice_id,
                reference_audio=audio,
                embeddings=embeddings
            )

            # Store in dictionary
            self.voices[voice_id] = voice

            return voice_id

        except Exception as e:
            raise VoiceError(f"Failed to add reference voice: {str(e)}")

    def _process_reference(self, audio: Audio) -> Any:
        """
        Process reference audio to extract voice characteristics.

        Args:
            audio: Reference audio

        Returns:
            Processed voice embeddings or model-specific data

        Raises:
            VoiceError: If processing fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    @timed
    def synthesize(self, text: str, voice_id: str) -> Audio:
        """
        Synthesize text with a cloned voice.

        Args:
            text: Text to synthesize
            voice_id: ID of the voice to use

        Returns:
            Audio object with synthesized speech

        Raises:
            VoiceError: If synthesis fails or voice ID is invalid
        """
        try:
            # Check if voice exists
            if voice_id not in self.voices:
                raise VoiceError(f"Voice ID not found: {voice_id}")

            # Get voice
            voice = self.voices[voice_id]

            # Synthesize speech (to be implemented by subclasses)
            audio = self._synthesize_with_voice(text, voice)

            return audio

        except Exception as e:
            raise VoiceError(f"Failed to synthesize speech: {str(e)}")

    def _synthesize_with_voice(self, text: str, voice: Voice) -> Audio:
        """
        Synthesize text with a specific voice.

        Args:
            text: Text to synthesize
            voice: Voice to use

        Returns:
            Audio object with synthesized speech

        Raises:
            VoiceError: If synthesis fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_voice(self, voice_id: str) -> Voice:
        """
        Get a voice by ID.

        Args:
            voice_id: ID of the voice to get

        Returns:
            Voice object

        Raises:
            VoiceError: If voice ID is invalid
        """
        if voice_id not in self.voices:
            raise VoiceError(f"Voice ID not found: {voice_id}")

        return self.voices[voice_id]

    def list_voices(self) -> List[Dict[str, Any]]:
        """
        List all registered voices.

        Returns:
            List of voice dictionaries with id, name, and metadata
        """
        return [voice.to_dict() for voice in self.voices.values()]

    def remove_voice(self, voice_id: str) -> None:
        """
        Remove a voice.

        Args:
            voice_id: ID of the voice to remove

        Raises:
            VoiceError: If voice ID is invalid
        """
        if voice_id not in self.voices:
            raise VoiceError(f"Voice ID not found: {voice_id}")

        del self.voices[voice_id]
