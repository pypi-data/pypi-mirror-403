"""
Speaker encoder module for SV2TTS.

This module provides functions to load and use the speaker encoder model
for the SV2TTS voice cloning system.
"""

import numpy as np
from typing import Optional, Union
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
    Load the speaker encoder model.

    Args:
        model_path: Path to the model file
        device: Device to use (cpu or cuda)
    """
    global _model, _device, _is_loaded

    try:
        # Lazy import to avoid dependency issues
        import tensorflow as tf
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

        # Set device
        _device = device
        if device == "cuda":
            # Configure TensorFlow to use GPU
            config = tf.compat.v1.ConfigProto()
            config.gpu_options.allow_growth = True
            session = tf.compat.v1.Session(config=config)
        else:
            # Force CPU
            config = tf.compat.v1.ConfigProto(device_count={'GPU': 0})
            session = tf.compat.v1.Session(config=config)

        # Import encoder model
        from fmus_vox.voice.sv2tts_utils.encoder_model import SpeakerEncoder

        # Load model
        _model = SpeakerEncoder(model_path, session)
        _is_loaded = True

    except Exception as e:
        raise Exception(f"Failed to load speaker encoder model: {str(e)}")

def is_loaded() -> bool:
    """
    Check if the model is loaded.

    Returns:
        True if loaded, False otherwise
    """
    global _is_loaded
    return _is_loaded

def embed_utterance(wav: np.ndarray) -> np.ndarray:
    """
    Compute the embedding for a single utterance.

    Args:
        wav: Audio waveform as a numpy array

    Returns:
        Speaker embedding as a numpy array

    Raises:
        Exception: If model is not loaded or embedding fails
    """
    global _model, _is_loaded

    if not _is_loaded or _model is None:
        raise Exception("Speaker encoder model not loaded")

    # Compute embedding
    try:
        # Normalize if needed
        if wav.dtype != np.float32:
            wav = wav.astype(np.float32)

        if np.abs(wav).max() > 1.0:
            wav = wav / np.abs(wav).max()

        # Trim silence
        from fmus_vox.voice.sv2tts_utils.audio import preprocess_wav
        wav = preprocess_wav(wav)

        # Compute embedding
        embedding = _model.embed_utterance(wav)
        return embedding

    except Exception as e:
        raise Exception(f"Failed to compute speaker embedding: {str(e)}")

def embed_speaker(wavs: Union[list, np.ndarray]) -> np.ndarray:
    """
    Compute the embedding for multiple utterances from the same speaker.

    Args:
        wavs: List of audio waveforms as numpy arrays

    Returns:
        Speaker embedding as a numpy array

    Raises:
        Exception: If model is not loaded or embedding fails
    """
    global _model, _is_loaded

    if not _is_loaded or _model is None:
        raise Exception("Speaker encoder model not loaded")

    # Compute embeddings
    try:
        # Normalize and preprocess
        from fmus_vox.voice.sv2tts_utils.audio import preprocess_wav

        processed_wavs = []
        for wav in wavs:
            if wav.dtype != np.float32:
                wav = wav.astype(np.float32)

            if np.abs(wav).max() > 1.0:
                wav = wav / np.abs(wav).max()

            wav = preprocess_wav(wav)
            processed_wavs.append(wav)

        # Compute embedding
        embedding = _model.embed_speaker(processed_wavs)
        return embedding

    except Exception as e:
        raise Exception(f"Failed to compute speaker embedding: {str(e)}")

# Stub class for future implementation
class SpeakerEncoder:
    """
    Speaker encoder for SV2TTS.

    Note:
        This is a stub class for future implementation. Currently, the module uses
        functional API.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the speaker encoder.

        Args:
            model_path: Path to the model file
            device: Device to use (cpu or cuda)
        """
        load_model(model_path, device)

    def embed_utterance(self, wav: np.ndarray) -> np.ndarray:
        """
        Compute the embedding for a single utterance.

        Args:
            wav: Audio waveform as a numpy array

        Returns:
            Speaker embedding as a numpy array
        """
        return embed_utterance(wav)

    def embed_speaker(self, wavs: list) -> np.ndarray:
        """
        Compute the embedding for multiple utterances from the same speaker.

        Args:
            wavs: List of audio waveforms as numpy arrays

        Returns:
            Speaker embedding as a numpy array
        """
        return embed_speaker(wavs)

    def is_loaded(self) -> bool:
        """
        Check if the model is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return is_loaded()
