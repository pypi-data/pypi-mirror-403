"""
SpeechBrain model implementation for speech-to-text.

This module provides the SpeechBrainTranscriber class which uses SpeechBrain's
pre-trained models for speech recognition.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional, Union, Generator
import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import TranscriptionError, ModelError
from fmus_vox.core.utils import get_logger
from fmus_vox.stt.transcriber import Transcriber, TranscriptionResult


class SpeechBrainTranscriber(Transcriber):
    """
    Transcriber using SpeechBrain's pre-trained models.

    SpeechBrain provides various speech recognition models including
    CRDNn, Transformer, and Conformer architectures.

    Args:
        model: SpeechBrain model variant
        language: Language code (en, fr, de, etc.)
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available SpeechBrain models
    _available_models = [
        "crdnn",
        "transformer",
        "conformer",
        "wav2vec2",
    ]

    def __init__(
        self,
        model: str = "crdnn",
        language: Optional[str] = None,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the SpeechBrain transcriber.

        Args:
            model: SpeechBrain model variant
            language: Language code
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        # Initialize base class
        super().__init__(model=model, device=device, **kwargs)

        self.language = language or "en"

        self.logger.debug(f"Initialized SpeechBrainTranscriber with model={model}")

    def _load_model(self) -> Any:
        """
        Load the SpeechBrain model.

        Returns:
            Loaded SpeechBrain model

        Raises:
            ModelError: If model loading fails
        """
        try:
            from speechbrain.inference.ASR import EncoderDecoderASR

            # Set device
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.logger.info(f"Loading SpeechBrain model {self.model_name} on {device}")

            # Select model based on name
            if self.model_name == "crdnn":
                # CRDNN model for English
                model_id = "speechbrain/asr-crdnn-commonvoice-en"
            elif self.model_name == "transformer":
                # Transformer model
                model_id = "speechbrain/asr-transformer-transformerlm-librispeech"
            elif self.model_name == "conformer":
                # Conformer model
                model_id = "speechbrain/asr-conformer-transformerlm-librispeech"
            elif self.model_name == "wav2vec2":
                # Wav2Vec2 based model
                model_id = "speechbrain/asr-wav2vec2-commonvoice-en"
            else:
                raise ModelError(f"Unknown SpeechBrain model: {self.model_name}")

            # Load the model
            asr_model = EncoderDecoderASR.from_hparams(
                source=model_id,
                run_opts={"device": device}
            )

            return asr_model

        except ImportError:
            raise ModelError("Failed to import speechbrain. Install with: pip install speechbrain")
        except Exception as e:
            raise ModelError(f"Failed to load SpeechBrain model: {str(e)}")

    def transcribe_with_metadata(
        self,
        audio: Union[str, Audio],
        language: Optional[str] = None,
        timestamps: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe audio to text with additional metadata.

        Args:
            audio: Audio to transcribe (file path or Audio object)
            language: Language code (overrides instance language)
            timestamps: Whether to include timestamps in the result

        Returns:
            TranscriptionResult object

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            model = self._model.get()

            # Load audio if path is provided
            if isinstance(audio, str):
                audio = Audio.load(audio)

            # Resample to 16kHz if needed (SpeechBrain standard)
            if audio.sample_rate != 16000:
                audio = audio.resample(target_sr=16000)

            # Get audio array
            audio_array = audio.data
            if audio_array.ndim > 1:
                # Convert to mono by averaging channels
                audio_array = np.mean(audio_array, axis=-1)

            # Normalize audio
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            audio_array = audio_array / np.max(np.abs(audio_array))

            # Perform transcription
            if hasattr(model, "transcribe_file"):
                # For models that support file transcription
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    # Save audio to temp file
                    audio.save(tmp_path)

                    try:
                        result_text = model.transcribe_file(tmp_path)
                    finally:
                        os.unlink(tmp_path)
            else:
                # For models that transcribe arrays
                result_text = model.transcribe(audio_array)[0]

            # SpeechBrain doesn't provide timestamps by default
            segments = []
            if timestamps and hasattr(model, "transcribe_with_timestamps"):
                # Try to get timestamps if available
                try:
                    timed_result = model.transcribe_with_timestamps(audio_array)
                    segments = self._parse_timestamps(timed_result)
                except:
                    pass

            # Create result object
            return TranscriptionResult(
                text=result_text.strip(),
                confidence=1.0,  # SpeechBrain doesn't provide confidence by default
                language=language or self.language,
                segments=segments if timestamps else None
            )

        except Exception as e:
            raise TranscriptionError(f"SpeechBrain transcription failed: {str(e)}")

    def _parse_timestamps(self, timed_result) -> List[Dict[str, Any]]:
        """
        Parse timestamp information from SpeechBrain result.

        Args:
            timed_result: Result with timestamps

        Returns:
            List of segment dictionaries
        """
        segments = []

        # SpeechBrain may return timestamps in different formats
        # This is a placeholder for actual parsing logic
        if isinstance(timed_result, dict):
            if "segments" in timed_result:
                for seg in timed_result["segments"]:
                    segments.append({
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "")
                    })
            elif "words" in timed_result:
                for word in timed_result["words"]:
                    segments.append({
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                        "text": word.get("word", "")
                    })

        return segments

    def stream(
        self,
        audio_stream: Generator[Audio, None, None],
        language: Optional[str] = None
    ) -> Generator[TranscriptionResult, None, None]:
        """
        Stream transcription for incoming audio chunks.

        Args:
            audio_stream: Generator yielding Audio objects
            language: Language code

        Yields:
            TranscriptionResult for each processed chunk

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            model = self._model.get()

            # We'll accumulate audio until we have enough for a meaningful transcription
            buffer = None
            buffer_duration = 0.0
            target_duration = 5.0  # Process in 5-second chunks

            for audio_chunk in audio_stream:
                # Resample if needed
                if audio_chunk.sample_rate != 16000:
                    audio_chunk = audio_chunk.resample(target_sr=16000)

                # Get audio array
                audio_array = audio_chunk.data
                if audio_array.ndim > 1:
                    audio_array = np.mean(audio_array, axis=-1)

                # Add to buffer
                if buffer is None:
                    buffer = audio_array
                else:
                    buffer = np.concatenate([buffer, audio_array])

                buffer_duration += audio_chunk.duration

                # Process when we have enough audio
                if buffer_duration >= target_duration:
                    # Normalize
                    buffer_normalized = buffer / np.max(np.abs(buffer))
                    if buffer_normalized.dtype != np.float32:
                        buffer_normalized = buffer_normalized.astype(np.float32)

                    # Transcribe
                    result_text = model.transcribe(buffer_normalized)[0]

                    # Create result
                    yield TranscriptionResult(
                        text=result_text.strip(),
                        confidence=1.0,
                        language=language or self.language
                    )

                    # Reset buffer (keep a small overlap to avoid cutting words)
                    overlap_samples = int(0.5 * 16000)  # 0.5 seconds overlap
                    if len(buffer) > overlap_samples:
                        buffer = buffer[-overlap_samples:]
                        buffer_duration = 0.5
                    else:
                        buffer = None
                        buffer_duration = 0.0

            # Process any remaining audio in the buffer
            if buffer is not None and len(buffer) > 0:
                buffer_normalized = buffer / np.max(np.abs(buffer))
                if buffer_normalized.dtype != np.float32:
                    buffer_normalized = buffer_normalized.astype(np.float32)

                result_text = model.transcribe(buffer_normalized)[0]

                yield TranscriptionResult(
                    text=result_text.strip(),
                    confidence=1.0,
                    language=language or self.language
                )

        except Exception as e:
            raise TranscriptionError(f"SpeechBrain streaming transcription failed: {str(e)}")
