"""
Whisper model implementation for speech-to-text.

This module provides the WhisperTranscriber class which uses OpenAI's Whisper
model for transcription.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional, Union, Generator
import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import TranscriptionError, ModelError
from fmus_vox.core.utils import get_logger, download_file, ensure_path_exists
from fmus_vox.stt.transcriber import Transcriber, TranscriptionResult

class WhisperTranscriber(Transcriber):
    """
    Transcriber using OpenAI's Whisper model.

    Whisper is a general-purpose speech recognition model that can transcribe
    speech in multiple languages and translate it to English.

    Args:
        model: Whisper model size/variant (tiny, base, small, medium, large)
        device: Computation device (cpu, cuda, auto)
        download_root: Directory to download and store models
        **kwargs: Additional model-specific parameters
    """

    # Available Whisper models
    _available_models = [
        "whisper-tiny", "whisper-base", "whisper-small",
        "whisper-medium", "whisper-large", "whisper-large-v2", "whisper-large-v3"
    ]

    # Model size mapping (without whisper- prefix)
    _model_size_map = {
        "tiny": "tiny",
        "base": "base",
        "small": "small",
        "medium": "medium",
        "large": "large",
        "large-v2": "large-v2",
        "large-v3": "large-v3"
    }

    def __init__(self, model: str = "whisper-base",
                device: Optional[str] = None,
                download_root: Optional[str] = None,
                **kwargs):
        """
        Initialize the Whisper transcriber.

        Args:
            model: Whisper model size/variant (tiny, base, small, medium, large)
            device: Computation device (cpu, cuda, auto)
            download_root: Directory to download and store models
            **kwargs: Additional model-specific parameters
        """
        # Map model name if needed
        if not model.startswith("whisper-"):
            model = f"whisper-{model}"

        # Get model size
        self.model_size = self._get_model_size(model)

        # Initialize base class
        super().__init__(model=model, device=device, **kwargs)

        # Set download root
        self.download_root = download_root or self.config.get("models_dir")

        # Additional parameters
        self.beam_size = kwargs.get("beam_size", 5)
        self.temperature = kwargs.get("temperature", 0.0)
        self.language_detection = kwargs.get("language_detection", True)

        self.logger.debug(f"Initialized WhisperTranscriber with model_size={self.model_size}")

    def _get_model_size(self, model: str) -> str:
        """Get the Whisper model size from the model name."""
        # Remove whisper- prefix if present
        if model.startswith("whisper-"):
            model = model[8:]

        # Check if model size is valid
        if model not in self._model_size_map:
            raise ModelError(f"Invalid Whisper model size: {model}. "
                          f"Available sizes: {list(self._model_size_map.keys())}")

        return self._model_size_map[model]

    def _load_model(self) -> Any:
        """
        Load the Whisper model.

        Returns:
            Loaded Whisper model

        Raises:
            ModelError: If model loading fails
        """
        try:
            import torch
            import whisper

            # Set device
            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.logger.info(f"Loading Whisper model {self.model_size} on {device}")

            # Load the model
            model = whisper.load_model(self.model_size, device=device, download_root=self.download_root)

            return model

        except ImportError:
            raise ModelError("Failed to import whisper. Please install it with 'pip install openai-whisper'")
        except Exception as e:
            raise ModelError(f"Failed to load Whisper model: {str(e)}")

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
        try:
            # Ensure model is loaded
            model = self._model.get()

            # Load audio if path is provided
            if isinstance(audio, str):
                audio = Audio.load(audio)

            # Resample to 16 kHz if needed
            if audio.sample_rate != 16000:
                audio = audio.resample(target_sr=16000)

            # Prepare transcription options
            options = {
                "beam_size": self.beam_size,
                "temperature": self.temperature,
            }

            # Set language if provided
            if language is not None:
                options["language"] = language

            # For file-based processing, we need a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                audio.save(tmp_path)

                try:
                    # Run transcription
                    result = model.transcribe(tmp_path, **options)
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_path)

            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })

            # Create result object
            transcription_result = TranscriptionResult(
                text=result["text"].strip(),
                confidence=result.get("confidence", 1.0),
                language=result.get("language"),
                segments=segments
            )

            return transcription_result

        except Exception as e:
            raise TranscriptionError(f"Whisper transcription failed: {str(e)}")

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
        try:
            # Ensure model is loaded
            model = self._model.get()

            # We'll accumulate audio until we have enough for a meaningful transcription
            buffer = None
            buffer_duration = 0.0
            target_duration = 5.0  # Process in 5-second chunks

            for audio_chunk in audio_stream:
                # Resample if needed
                if audio_chunk.sample_rate != 16000:
                    audio_chunk = audio_chunk.resample(target_sr=16000)

                # Add to buffer
                if buffer is None:
                    buffer = audio_chunk.data
                else:
                    buffer = np.concatenate([buffer, audio_chunk.data])

                buffer_duration += audio_chunk.duration

                # Process when we have enough audio
                if buffer_duration >= target_duration:
                    # Create Audio object from buffer
                    buffer_audio = Audio(buffer, 16000)

                    # Transcribe the buffer
                    result = self.transcribe_with_metadata(buffer_audio, language)

                    # Reset buffer (keep a small overlap to avoid cutting words)
                    overlap_samples = int(0.5 * 16000)  # 0.5 seconds overlap
                    if len(buffer) > overlap_samples:
                        buffer = buffer[-overlap_samples:]
                        buffer_duration = 0.5
                    else:
                        buffer = None
                        buffer_duration = 0.0

                    yield result

            # Process any remaining audio in the buffer
            if buffer is not None and len(buffer) > 0:
                buffer_audio = Audio(buffer, 16000)
                result = self.transcribe_with_metadata(buffer_audio, language)
                yield result

        except Exception as e:
            raise TranscriptionError(f"Whisper streaming transcription failed: {str(e)}")
