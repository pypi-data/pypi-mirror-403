"""
Base Transcriber class for speech-to-text functionality.

This module provides the Transcriber class which is the common interface for
all speech-to-text models in fmus-vox.
"""

import os
from typing import Any, Dict, List, Optional, Union, Tuple, Generator
from pathlib import Path
import asyncio

from fmus_vox.core.audio import Audio
from fmus_vox.core.config import get_config
from fmus_vox.core.errors import TranscriptionError, ModelError
from fmus_vox.core.utils import get_logger, LazyLoader, timed

class TranscriptionResult:
    """
    Container for transcription results, including text, confidence, and timestamps.
    """

    def __init__(self,
                text: str,
                confidence: float = 1.0,
                language: Optional[str] = None,
                segments: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize a transcription result.

        Args:
            text: Transcribed text
            confidence: Confidence score (0.0 to 1.0)
            language: Detected language code
            segments: List of segments with timestamps and text
        """
        self.text = text
        self.confidence = confidence
        self.language = language
        self.segments = segments or []

    def __str__(self) -> str:
        """Return the transcribed text."""
        return self.text

    def __repr__(self) -> str:
        """Return a string representation of the result."""
        return f"TranscriptionResult(text='{self.text[:30]}...', confidence={self.confidence:.2f})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "segments": self.segments
        }

class Transcriber:
    """
    Base class for speech-to-text transcription.

    This class provides the common interface for all transcription models
    and handles model loading, caching, and transcription.

    Args:
        model: Name of the model to use (whisper, wav2vec, etc.)
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

    def __new__(cls, model: str = "whisper", **kwargs) -> "Transcriber":
        """
        Create a new Transcriber instance of the appropriate subclass.

        Args:
            model: Name of the model to use
            **kwargs: Additional model-specific parameters

        Returns:
            Transcriber instance

        Raises:
            ModelError: If the model is not supported
        """
        if cls is Transcriber:
            # Determine which implementation to use based on model name
            if model.startswith("whisper"):
                from fmus_vox.stt.whisper import WhisperTranscriber
                return WhisperTranscriber(model=model, **kwargs)
            elif model.startswith("wav2vec"):
                from fmus_vox.stt.wav2vec import Wav2VecTranscriber
                return Wav2VecTranscriber(model=model, **kwargs)
            elif model.startswith("speechbrain"):
                from fmus_vox.stt.speechbrain import SpeechBrainTranscriber
                return SpeechBrainTranscriber(model=model, **kwargs)
            elif model in cls._model_registry:
                implementation = cls._model_registry[model]
                return implementation(model=model, **kwargs)
            else:
                raise ModelError(f"Unsupported transcription model: {model}")
        else:
            # If called from a subclass, use normal instantiation
            return super().__new__(cls)

    def __init__(self, model: str = "whisper", device: Optional[str] = None, **kwargs):
        """
        Initialize the transcriber.

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

        # Lazy-loaded model
        self._model = LazyLoader(self._load_model)

        self.logger.debug(f"Initialized {self.__class__.__name__} with model={model}")

    def _load_model(self) -> Any:
        """
        Load the transcription model.

        Returns:
            Loaded model

        Raises:
            ModelError: If model loading fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    @timed
    def transcribe(self, audio: Union[str, Audio],
                  language: Optional[str] = None) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio to transcribe (file path or Audio object)
            language: Language code (if None, auto-detect)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        result = self.transcribe_with_metadata(audio, language)
        return result.text

    @timed
    def transcribe_with_metadata(self, audio: Union[str, Audio],
                                language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio to text with additional metadata.

        Args:
            audio: Audio to transcribe (file path or Audio object)
            language: Language code (if None, auto-detect)

        Returns:
            TranscriptionResult object

        Raises:
            TranscriptionError: If transcription fails
        """
        raise NotImplementedError("Subclasses must implement this method")

    async def transcribe_async(self, audio: Union[str, Audio],
                             language: Optional[str] = None) -> str:
        """
        Transcribe audio to text asynchronously.

        Args:
            audio: Audio to transcribe (file path or Audio object)
            language: Language code (if None, auto-detect)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        result = await self.transcribe_with_metadata_async(audio, language)
        return result.text

    async def transcribe_with_metadata_async(self, audio: Union[str, Audio],
                                           language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio to text asynchronously with additional metadata.

        Args:
            audio: Audio to transcribe (file path or Audio object)
            language: Language code (if None, auto-detect)

        Returns:
            TranscriptionResult object

        Raises:
            TranscriptionError: If transcription fails
        """
        # Default implementation runs synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.transcribe_with_metadata, audio, language
        )

    def stream(self, audio_stream: Generator[Audio, None, None],
              language: Optional[str] = None) -> Generator[TranscriptionResult, None, None]:
        """
        Stream transcription for incoming audio chunks.

        Args:
            audio_stream: Generator yielding Audio objects
            language: Language code (if None, auto-detect)

        Yields:
            TranscriptionResult for each processed chunk

        Raises:
            TranscriptionError: If transcription fails
        """
        raise NotImplementedError("Subclasses must implement streaming or raise an error")
