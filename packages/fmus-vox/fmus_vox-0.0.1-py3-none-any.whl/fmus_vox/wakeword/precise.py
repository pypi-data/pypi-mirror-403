"""
fmus_vox.wakeword.precise - Mycroft Precise wake word detector implementation.

This module provides wake word detection using Mycroft's Precise engine.
"""

import os
import threading
from typing import List, Union, Dict, Any, Optional

import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import ModelLoadError, DependencyError
from fmus_vox.core.config import config
from .detector import WakeWordDetector

try:
    from precise_runner import PreciseRunner, PreciseEngine
except ImportError:
    PreciseRunner = None
    PreciseEngine = None


class PreciseDetector(WakeWordDetector):
    """
    Wake word detector using Mycroft's Precise engine.

    This implementation uses the Mycroft Precise wake word detection engine
    which supports custom wake word models.
    """

    def __init__(
        self,
        wake_words: Union[str, List[str]],
        threshold: float = 0.5,
        model_path: Optional[str] = None,
        chunk_size: int = 2048,
        **kwargs
    ):
        """
        Initialize the Precise wake word detector.

        Args:
            wake_words: Model path or list of model paths for wake word detection.
                        Note: Precise only supports one active model at a time.
            threshold: Detection threshold (0-1).
            model_path: Path to Precise model file (.pb).
                        If provided, overrides wake_words.
            chunk_size: Audio chunk size for processing.
            **kwargs: Additional parameters.
        """
        super().__init__(wake_words, threshold, **kwargs)

        if PreciseRunner is None or PreciseEngine is None:
            raise DependencyError(
                "Mycroft Precise is not installed. Install with: "
                "pip install precise-runner"
            )

        # Precise only supports one model at a time, use the first one
        self.model_path = model_path or self.wake_words[0]

        if not os.path.isfile(self.model_path):
            raise ValueError(
                f"Precise model file not found: {self.model_path}. "
                "Precise requires a direct path to a model file."
            )

        self.chunk_size = chunk_size
        self.engine = None
        self.runner = None
        self.stream_thread = None
        self.stream_source = None
        self.detection_buffer = []
        self.buffer_size = 5  # Number of chunks to buffer for sliding window

    def load_model(self) -> None:
        """
        Load the Precise wake word detection model.

        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        try:
            self.engine = PreciseEngine(self.model_path, self.chunk_size)
            self.engine.threshold = self.threshold
        except Exception as e:
            raise ModelLoadError(f"Failed to load Precise model: {str(e)}")

    def detect(self, audio: Union[str, Audio]) -> bool:
        """
        Detect if the audio contains the wake word.

        Args:
            audio: Audio object or path to audio file to analyze.

        Returns:
            True if wake word was detected, False otherwise.
        """
        if self.engine is None:
            self.load_model()

        # Convert to Audio object if string path
        if isinstance(audio, str):
            audio = Audio.load(audio)

        # Resample to required sample rate (16000 Hz for Precise)
        if audio.sample_rate != 16000:
            audio = audio.resample(16000)

        # Convert to PCM-16 (required format for Precise)
        pcm = audio.to_int16().to_numpy()

        # Process audio in chunks
        chunk_size = self.chunk_size
        detected = False

        # Initialize a detection buffer for a sliding window approach
        detection_buffer = []

        for i in range(0, len(pcm), chunk_size):
            chunk = pcm[i:i + chunk_size]

            # Pad if chunk is smaller than required size
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

            # Check if wake word detected in this chunk
            prob = self.engine.predict(chunk)
            detection_buffer.append(prob)

            # Only keep the most recent buffer_size chunks
            if len(detection_buffer) > self.buffer_size:
                detection_buffer.pop(0)

            # If any detection in the buffer exceeds threshold, consider it detected
            if any(p >= self.threshold for p in detection_buffer):
                detected = True
                wake_word = self.model_path

                # Call any registered callbacks
                if wake_word in self.callbacks:
                    metadata = {
                        "wake_word": wake_word,
                        "confidence": max(detection_buffer),
                        "timestamp": i / 16000,
                    }
                    for callback in self.callbacks[wake_word]:
                        callback(metadata)

                break

        return detected

    def _on_prediction(self, prob):
        """
        Callback for PreciseRunner when prediction is made.

        Args:
            prob: Prediction probability (0-1).
        """
        self.detection_buffer.append(prob)

        # Only keep the most recent buffer_size predictions
        if len(self.detection_buffer) > self.buffer_size:
            self.detection_buffer.pop(0)

        # If any detection in the buffer exceeds threshold, trigger callbacks
        if any(p >= self.threshold for p in self.detection_buffer):
            wake_word = self.model_path

            # Call any registered callbacks
            if wake_word in self.callbacks:
                metadata = {
                    "wake_word": wake_word,
                    "confidence": max(self.detection_buffer),
                    "timestamp": None,
                }
                for callback in self.callbacks[wake_word]:
                    callback(metadata)

    def _on_activation(self):
        """
        Callback for PreciseRunner when wake word is detected.
        """
        wake_word = self.model_path

        # Call any registered callbacks
        if wake_word in self.callbacks:
            metadata = {
                "wake_word": wake_word,
                "confidence": max(self.detection_buffer) if self.detection_buffer else self.threshold,
                "timestamp": None,
            }
            for callback in self.callbacks[wake_word]:
                callback(metadata)

    def start_streaming(self, stream_source=None) -> None:
        """
        Start continuous wake word detection from a stream.

        Args:
            stream_source: Optional audio stream source. If None, will
                          use the default microphone.
        """
        if self.engine is None:
            self.load_model()

        super().start_streaming(stream_source)

        # If stream_source is provided, we need a custom implementation
        if stream_source is not None:
            from fmus_vox.stream import Microphone

            self.stream_source = stream_source
            self.detection_buffer = []

            def _stream_processor():
                with self.stream_source as stream:
                    while self._is_running:
                        audio_chunk = stream.read(self.chunk_size)
                        pcm = np.frombuffer(audio_chunk, dtype=np.int16)

                        if len(pcm) != self.chunk_size:
                            continue

                        prob = self.engine.predict(pcm)
                        self._on_prediction(prob)

                        # If probability exceeds threshold, consider it an activation
                        if prob >= self.threshold:
                            self._on_activation()

            self.stream_thread = threading.Thread(target=_stream_processor)
            self.stream_thread.daemon = True
            self.stream_thread.start()

        # Otherwise use PreciseRunner which handles microphone input
        else:
            self.runner = PreciseRunner(
                self.engine,
                on_activation=self._on_activation,
                on_prediction=self._on_prediction,
                trigger_level=self.threshold
            )
            self.runner.start()

    def stop_streaming(self) -> None:
        """Stop continuous wake word detection."""
        super().stop_streaming()

        if self.runner:
            self.runner.stop()
            self.runner = None

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)
            self.stream_thread = None

        self.detection_buffer = []

    def __del__(self):
        """Clean up resources when the detector is garbage collected."""
        self.stop_streaming()
        if self.engine:
            del self.engine
            self.engine = None
