"""
fmus_vox.wakeword.detector - Base class for wake word detection.

This module provides the abstract base class for all wake word detector implementations.
"""

import abc
from typing import Callable, List, Optional, Union, Dict, Any

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import ModelLoadError


class WakeWordDetector(abc.ABC):
    """
    Base class for wake word detection implementations.

    This abstract class defines the interface that all wake word detectors
    must implement.
    """

    def __init__(
        self,
        wake_words: Union[str, List[str]],
        threshold: float = 0.5,
        **kwargs
    ):
        """
        Initialize the wake word detector.

        Args:
            wake_words: Single wake word or list of wake words to detect.
            threshold: Detection sensitivity threshold (0-1).
            **kwargs: Additional detector-specific parameters.
        """
        self.wake_words = [wake_words] if isinstance(wake_words, str) else wake_words
        self.threshold = threshold
        self.model = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self._is_running = False

    def add_callback(self, wake_word: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be called when a specific wake word is detected.

        Args:
            wake_word: The wake word to trigger the callback.
            callback: Function to call when the wake word is detected.
                      Should accept a dict with metadata about the detection.
        """
        if wake_word not in self.callbacks:
            self.callbacks[wake_word] = []
        self.callbacks[wake_word].append(callback)

    def remove_callback(self, wake_word: str, callback: Callable = None) -> None:
        """
        Remove callback(s) for a specific wake word.

        Args:
            wake_word: The wake word to remove callbacks for.
            callback: Specific callback to remove. If None, all callbacks
                      for the wake word are removed.
        """
        if callback is None:
            self.callbacks.pop(wake_word, None)
        elif wake_word in self.callbacks:
            self.callbacks[wake_word] = [cb for cb in self.callbacks[wake_word]
                                       if cb != callback]

    @abc.abstractmethod
    def load_model(self) -> None:
        """
        Load the wake word detection model.

        This method must be implemented by subclasses to load the
        specific wake word model.

        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        pass

    @abc.abstractmethod
    def detect(self, audio: Union[str, Audio]) -> bool:
        """
        Detect if the audio contains any of the configured wake words.

        Args:
            audio: Audio object or path to audio file to analyze.

        Returns:
            True if a wake word was detected, False otherwise.
        """
        pass

    def start_streaming(self, stream_source=None) -> None:
        """
        Start continuous wake word detection from a stream.

        Args:
            stream_source: Optional audio stream source. If None, will
                          use the default microphone.
        """
        if self._is_running:
            return

        self._is_running = True
        # Actual implementation will be provided by subclasses

    def stop_streaming(self) -> None:
        """Stop continuous wake word detection."""
        self._is_running = False
        # Actual implementation will be provided by subclasses

    @property
    def is_running(self) -> bool:
        """Return True if the detector is currently running."""
        return self._is_running

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(wake_words={self.wake_words}, threshold={self.threshold})"
