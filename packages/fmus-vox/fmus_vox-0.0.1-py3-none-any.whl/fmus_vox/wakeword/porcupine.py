"""
fmus_vox.wakeword.porcupine - Porcupine wake word detector implementation.

This module provides wake word detection using Picovoice's Porcupine engine.
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
    import pvporcupine
except ImportError:
    pvporcupine = None


class PorcupineDetector(WakeWordDetector):
    """
    Wake word detector using Picovoice's Porcupine engine.

    This implementation uses the Porcupine wake word detection engine
    which supports both pre-made and custom wake words.
    """

    def __init__(
        self,
        wake_words: Union[str, List[str]],
        threshold: float = 0.5,
        access_key: Optional[str] = None,
        model_path: Optional[str] = None,
        sensitivities: Optional[List[float]] = None,
        **kwargs
    ):
        """
        Initialize the Porcupine wake word detector.

        Args:
            wake_words: Single wake word or list of wake words to detect.
            threshold: Detection sensitivity threshold (0-1).
            access_key: Picovoice access key. If None, will use the key from config.
            model_path: Path to Porcupine model file. If None, use default.
            sensitivities: List of sensitivity values for each wake word.
            **kwargs: Additional parameters to pass to Porcupine.
        """
        super().__init__(wake_words, threshold, **kwargs)

        if pvporcupine is None:
            raise DependencyError(
                "Porcupine is not installed. Install with: pip install pvporcupine"
            )

        self.access_key = access_key or config.get("porcupine.access_key")
        if not self.access_key:
            raise ValueError(
                "Porcupine access key is required. Provide it as parameter or "
                "set it in the configuration as porcupine.access_key"
            )

        self.model_path = model_path

        # Convert string wake words to keywords Porcupine understands
        self.keyword_paths = []
        for word in self.wake_words:
            if os.path.isfile(word):
                # User provided a direct path to a Porcupine keyword file (.ppn)
                self.keyword_paths.append(word)
            else:
                # Try to use a built-in keyword
                self.keyword_paths.append(word)

        # Set sensitivity for each keyword
        if sensitivities:
            self.sensitivities = sensitivities
        else:
            # Convert threshold to Porcupine sensitivity (0-1)
            self.sensitivities = [self.threshold] * len(self.wake_words)

        self.porcupine = None
        self.stream_thread = None
        self.stream_source = None

    def load_model(self) -> None:
        """
        Load the Porcupine wake word detection model.

        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=self.keyword_paths if all(isinstance(kw, str) and not os.path.isfile(kw)
                                                for kw in self.keyword_paths) else None,
                keyword_paths=self.keyword_paths if any(os.path.isfile(kw)
                                                       for kw in self.keyword_paths) else None,
                sensitivities=self.sensitivities,
                model_path=self.model_path
            )
        except Exception as e:
            raise ModelLoadError(f"Failed to load Porcupine model: {str(e)}")

    def detect(self, audio: Union[str, Audio]) -> bool:
        """
        Detect if the audio contains any of the configured wake words.

        Args:
            audio: Audio object or path to audio file to analyze.

        Returns:
            True if a wake word was detected, False otherwise.
        """
        if self.porcupine is None:
            self.load_model()

        # Convert to Audio object if string path
        if isinstance(audio, str):
            audio = Audio.load(audio)

        # Resample to required sample rate
        if audio.sample_rate != self.porcupine.sample_rate:
            audio = audio.resample(self.porcupine.sample_rate)

        # Convert to PCM-16 (required format for Porcupine)
        pcm = audio.to_int16().to_numpy()

        # Process audio in chunks
        chunk_size = self.porcupine.frame_length
        detected = False

        for i in range(0, len(pcm), chunk_size):
            chunk = pcm[i:i + chunk_size]

            # Pad if chunk is smaller than required frame length
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

            result = self.porcupine.process(chunk)

            if result >= 0:  # Wake word detected
                detected = True
                wake_word = self.wake_words[result]

                # Call any registered callbacks for this wake word
                if wake_word in self.callbacks:
                    metadata = {
                        "wake_word": wake_word,
                        "index": result,
                        "timestamp": i / self.porcupine.sample_rate,
                    }
                    for callback in self.callbacks[wake_word]:
                        callback(metadata)

                break

        return detected

    def start_streaming(self, stream_source=None) -> None:
        """
        Start continuous wake word detection from a stream.

        Args:
            stream_source: Optional audio stream source. If None, will
                          use the default microphone.
        """
        if self.porcupine is None:
            self.load_model()

        super().start_streaming(stream_source)

        from fmus_vox.stream import Microphone

        self.stream_source = stream_source or Microphone(
            sample_rate=self.porcupine.sample_rate,
            format="int16",
            channels=1,
        )

        def _stream_processor():
            with self.stream_source as stream:
                while self._is_running:
                    audio_chunk = stream.read(self.porcupine.frame_length)
                    pcm = np.frombuffer(audio_chunk, dtype=np.int16)

                    if len(pcm) != self.porcupine.frame_length:
                        continue

                    result = self.porcupine.process(pcm)

                    if result >= 0:  # Wake word detected
                        wake_word = self.wake_words[result]

                        # Call any registered callbacks for this wake word
                        if wake_word in self.callbacks:
                            metadata = {
                                "wake_word": wake_word,
                                "index": result,
                                "timestamp": None,
                            }
                            for callback in self.callbacks[wake_word]:
                                callback(metadata)

        self.stream_thread = threading.Thread(target=_stream_processor)
        self.stream_thread.daemon = True
        self.stream_thread.start()

    def stop_streaming(self) -> None:
        """Stop continuous wake word detection."""
        super().stop_streaming()

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)

        self.stream_thread = None

    def __del__(self):
        """Clean up resources when the detector is garbage collected."""
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
