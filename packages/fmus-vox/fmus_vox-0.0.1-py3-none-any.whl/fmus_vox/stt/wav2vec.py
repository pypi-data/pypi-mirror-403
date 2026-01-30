"""
Wav2Vec model implementation for speech-to-text.

This module provides the Wav2VecTranscriber class which uses Facebook's
Wav2Vec2 model for speech recognition.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional, Union, Generator
import numpy as np
import torch

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import TranscriptionError, ModelError
from fmus_vox.core.utils import get_logger, download_file, ensure_path_exists
from fmus_vox.stt.transcriber import Transcriber, TranscriptionResult


class Wav2VecTranscriber(Transcriber):
    """
    Transcriber using Facebook's Wav2Vec2 model.

    Wav2Vec2 is a self-supervised learning approach for speech recognition
    that achieves state-of-the-art performance on many benchmarks.

    Args:
        model: Wav2Vec2 model variant (wav2vec2-base, wav2vec2-large, etc.)
        language: Language code (en, es, fr, etc.)
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available Wav2Vec2 models
    _available_models = [
        "wav2vec2-base",
        "wav2vec2-base-960h",
        "wav2vec2-large",
        "wav2vec2-large-960h",
        "wav2vec2-xls-r-300m",
        "wav2vec2-xls-r-1b",
        "wav2vec2-xls-r-2b",
    ]

    # Model mapping to HuggingFace model IDs
    _model_map = {
        "wav2vec2-base": "facebook/wav2vec2-base-960h",
        "wav2vec2-base-960h": "facebook/wav2vec2-base-960h",
        "wav2vec2-large": "facebook/wav2vec2-large-960h",
        "wav2vec2-large-960h": "facebook/wav2vec2-large-960h",
        "wav2vec2-xls-r-300m": "facebook/wav2vec2-xls-r-300m",
        "wav2vec2-xls-r-1b": "facebook/wav2vec2-xls-r-1b",
        "wav2vec2-xls-r-2b": "facebook/wav2vec2-xls-r-2b",
    }

    def __init__(
        self,
        model: str = "wav2vec2-base",
        language: Optional[str] = None,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Wav2Vec transcriber.

        Args:
            model: Wav2Vec2 model variant
            language: Language code (for multilingual models)
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        # Map model name
        if model not in self._model_map:
            # Try with wav2vec prefix
            if not model.startswith("wav2vec"):
                model = f"wav2vec2-{model}"
            if model not in self._model_map:
                raise ModelError(f"Invalid Wav2Vec2 model: {model}. Available: {list(self._model_map.keys())}")

        self.model_id = self._model_map[model]

        # Initialize base class
        super().__init__(model=model, device=device, **kwargs)

        self.language = language

        # Chunking parameters for long audio
        self.chunk_length_s = kwargs.get("chunk_length_s", 30)
        self.stride_length_s = kwargs.get("stride_length_s", 5)

        self.logger.debug(f"Initialized Wav2VecTranscriber with model_id={self.model_id}")

    def _load_model(self) -> Any:
        """
        Load the Wav2Vec2 model.

        Returns:
            Loaded Wav2Vec2 model and processor

        Raises:
            ModelError: If model loading fails
        """
        try:
            from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

            # Set device
            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.logger.info(f"Loading Wav2Vec2 model {self.model_id} on {device}")

            # Load processor and model
            processor = Wav2Vec2Processor.from_pretrained(self.model_id)
            model = Wav2Vec2ForCTC.from_pretrained(self.model_id)

            # Move to device
            model.to(device)

            # Set to eval mode
            model.eval()

            # Return both as tuple
            return (processor, model, device)

        except ImportError:
            raise ModelError("Failed to import transformers. Install with: pip install transformers")
        except Exception as e:
            raise ModelError(f"Failed to load Wav2Vec2 model: {str(e)}")

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
            processor, model, device = self._model.get()

            # Load audio if path is provided
            if isinstance(audio, str):
                audio = Audio.load(audio)

            # Resample to 16kHz if needed (Wav2Vec2 standard)
            if audio.sample_rate != 16000:
                audio = audio.resample(target_sr=16000)

            # Get audio array
            audio_array = audio.data
            if audio_array.ndim > 1:
                # Convert to mono by averaging channels
                audio_array = np.mean(audio_array, axis=-1)

            # Normalize audio
            audio_array = audio_array / np.max(np.abs(audio_array))

            # Prepare input
            inputs = processor(
                audio_array,
                sampling_rate=16000,
                return_tensors="pt"
            ).to(device)

            # Perform transcription
            with torch.no_grad():
                logits = model(inputs.input_values).logits

            # Get predicted IDs
            predicted_ids = torch.argmax(logits, dim=-1)

            # Decode to text
            transcription = processor.batch_decode(predicted_ids)[0]

            # For timestamps, we need to process differently
            segments = []
            if timestamps:
                # Simple chunking for timestamps
                chunk_samples = int(self.chunk_length_s * 16000)
                stride_samples = int(self.stride_length_s * 16000)

                for i, start in enumerate(range(0, len(audio_array), stride_samples)):
                    end = min(start + chunk_samples, len(audio_array))
                    if end - start < 16000:  # Skip very short chunks
                        continue

                    chunk = audio_array[start:end]
                    chunk_inputs = processor(
                        chunk,
                        sampling_rate=16000,
                        return_tensors="pt"
                    ).to(device)

                    with torch.no_grad():
                        chunk_logits = model(chunk_inputs.input_values).logits
                        chunk_ids = torch.argmax(chunk_logits, dim=-1)
                        chunk_text = processor.batch_decode(chunk_ids)[0]

                    if chunk_text.strip():
                        segments.append({
                            "start": start / 16000,
                            "end": end / 16000,
                            "text": chunk_text.strip()
                        })

            # Create result object
            return TranscriptionResult(
                text=transcription.strip(),
                confidence=1.0,  # Wav2Vec2 doesn't provide confidence by default
                language=language or self.language,
                segments=segments if timestamps else None
            )

        except Exception as e:
            raise TranscriptionError(f"Wav2Vec2 transcription failed: {str(e)}")

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
            processor, model, device = self._model.get()

            # Accumulate audio until we have enough
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

                    # Prepare input
                    inputs = processor(
                        buffer_normalized,
                        sampling_rate=16000,
                        return_tensors="pt"
                    ).to(device)

                    # Transcribe
                    with torch.no_grad():
                        logits = model(inputs.input_values).logits
                        predicted_ids = torch.argmax(logits, dim=-1)
                        transcription = processor.batch_decode(predicted_ids)[0]

                    # Create result
                    result = TranscriptionResult(
                        text=transcription.strip(),
                        confidence=1.0,
                        language=language or self.language
                    )

                    yield result

                    # Reset buffer (keep small overlap)
                    overlap_samples = int(0.5 * 16000)  # 0.5 seconds overlap
                    if len(buffer) > overlap_samples:
                        buffer = buffer[-overlap_samples:]
                        buffer_duration = 0.5
                    else:
                        buffer = None
                        buffer_duration = 0.0

            # Process remaining buffer
            if buffer is not None and len(buffer) > 0:
                buffer_normalized = buffer / np.max(np.abs(buffer))
                inputs = processor(
                    buffer_normalized,
                    sampling_rate=16000,
                    return_tensors="pt"
                ).to(device)

                with torch.no_grad():
                    logits = model(inputs.input_values).logits
                    predicted_ids = torch.argmax(logits, dim=-1)
                    transcription = processor.batch_decode(predicted_ids)[0]

                result = TranscriptionResult(
                    text=transcription.strip(),
                    confidence=1.0,
                    language=language or self.language
                )

                yield result

        except Exception as e:
            raise TranscriptionError(f"Wav2Vec2 streaming transcription failed: {str(e)}")
