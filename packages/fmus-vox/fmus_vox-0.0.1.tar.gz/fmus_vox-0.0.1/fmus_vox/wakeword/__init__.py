"""
fmus_vox.wakeword - Wake word detection functionality for voice applications.

This module provides interfaces and implementations for wake word detection,
allowing applications to respond to specific trigger phrases.
"""

from typing import Callable, List, Optional, Union

from fmus_vox.core.audio import Audio
from .detector import WakeWordDetector

__all__ = ["WakeWordDetector", "detect_wake_word", "create_detector"]


def detect_wake_word(
    audio: Union[str, Audio],
    wake_word: str = "hey assistant",
    threshold: float = 0.5,
) -> bool:
    """
    Detect if an audio file or buffer contains the wake word.

    Args:
        audio: Audio object or path to audio file.
        wake_word: Wake word to detect.
        threshold: Detection threshold (0-1).

    Returns:
        True if wake word was detected.
    """
    detector = create_detector(wake_word, threshold)
    return detector.detect(audio)


def create_detector(
    wake_word: Union[str, List[str]] = "hey assistant",
    threshold: float = 0.5,
    model_type: str = "porcupine",
) -> WakeWordDetector:
    """
    Create a wake word detector with specified settings.

    Args:
        wake_word: Wake word(s) to detect.
        threshold: Detection threshold (0-1).
        model_type: Type of detector to use ('porcupine' or 'precise').

    Returns:
        Configured WakeWordDetector instance.
    """
    if model_type.lower() == "porcupine":
        from .porcupine import PorcupineDetector
        return PorcupineDetector(wake_word, threshold)
    elif model_type.lower() == "precise":
        from .precise import PreciseDetector
        return PreciseDetector(wake_word, threshold)
    else:
        raise ValueError(f"Unknown wake word detector type: {model_type}")
