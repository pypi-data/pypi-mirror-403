"""
WaveRNN vocoder module for SV2TTS.

This module provides functions to load and use the WaveRNN vocoder
model for the SV2TTS voice cloning system.
"""

import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import os
import warnings

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Globals
_model = None
_device = None
_is_loaded = False

def load_model(model_path: str, device: str = "cpu") -> None:
    """
    Load the WaveRNN vocoder model.

    Args:
        model_path: Path to the model file
        device: Device to use (cpu or cuda)
    """
    global _model, _device, _is_loaded

    try:
        # Lazy import to avoid dependency issues
        if device == "cuda":
            try:
                import torch
                torch.cuda.set_device(0)  # Use first GPU
            except Exception as e:
                device = "cpu"
                print(f"CUDA not available, falling back to CPU: {str(e)}")

        # Set device
        _device = device

        # Import vocoder model
        from fmus_vox.voice.sv2tts_utils.vocoder_model import WaveRNN

        # Load model
        _model = WaveRNN.load_model(model_path, device)
        _is_loaded = True

    except Exception as e:
        raise Exception(f"Failed to load vocoder model: {str(e)}")

def is_loaded() -> bool:
    """
    Check if the model is loaded.

    Returns:
        True if loaded, False otherwise
    """
    global _is_loaded
    return _is_loaded

def infer_waveform(mel: np.ndarray, progress_callback: Optional[callable] = None) -> np.ndarray:
    """
    Generate a waveform from a mel spectrogram.

    Args:
        mel: Mel spectrogram
        progress_callback: Optional callback function for progress updates

    Returns:
        Audio waveform

    Raises:
        Exception: If model is not loaded or inference fails
    """
    global _model, _is_loaded

    if not _is_loaded or _model is None:
        raise Exception("Vocoder model not loaded")

    # Generate waveform
    try:
        # Convert to appropriate type if needed
        if not isinstance(mel, np.ndarray):
            mel = np.array(mel)

        # Generate waveform
        wav = _model.generate_waveform(mel, progress_callback)
        return wav

    except Exception as e:
        raise Exception(f"Failed to generate waveform: {str(e)}")

def preprocess_mel(mel: np.ndarray) -> np.ndarray:
    """
    Preprocess a mel spectrogram for vocoding.

    Args:
        mel: Mel spectrogram

    Returns:
        Preprocessed mel spectrogram
    """
    try:
        # Normalize if needed
        if not isinstance(mel, np.ndarray):
            mel = np.array(mel)

        # Normalize
        if mel.max() > 1.0 or mel.min() < -1.0:
            mel = 2 * (mel - mel.min()) / (mel.max() - mel.min()) - 1

        return mel

    except Exception as e:
        raise Exception(f"Failed to preprocess mel spectrogram: {str(e)}")

# Stub class for future implementation
class Vocoder:
    """
    WaveRNN vocoder for SV2TTS.

    Note:
        This is a stub class for future implementation. Currently, the module uses
        functional API.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the vocoder.

        Args:
            model_path: Path to the model file
            device: Device to use (cpu or cuda)
        """
        load_model(model_path, device)

    def infer_waveform(self, mel: np.ndarray, progress_callback: Optional[callable] = None) -> np.ndarray:
        """
        Generate a waveform from a mel spectrogram.

        Args:
            mel: Mel spectrogram
            progress_callback: Optional callback function for progress updates

        Returns:
            Audio waveform
        """
        return infer_waveform(mel, progress_callback)

    def is_loaded(self) -> bool:
        """
        Check if the model is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return is_loaded()
