"""
Tacotron 2 synthesizer module for SV2TTS.

This module provides functions to load and use the Tacotron 2 synthesizer
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
    Load the Tacotron 2 synthesizer model.

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

        # Import synthesizer model
        from fmus_vox.voice.sv2tts_utils.synthesizer_model import Tacotron

        # Load model
        _model = Tacotron(checkpoint_path=model_path, session=session)
        _is_loaded = True

    except Exception as e:
        raise Exception(f"Failed to load synthesizer model: {str(e)}")

def is_loaded() -> bool:
    """
    Check if the model is loaded.

    Returns:
        True if loaded, False otherwise
    """
    global _is_loaded
    return _is_loaded

def synthesize_spectrograms(texts: List[str], embeddings: List[np.ndarray]) -> List[np.ndarray]:
    """
    Synthesize mel spectrograms from text and speaker embeddings.

    Args:
        texts: List of texts to synthesize
        embeddings: List of speaker embeddings

    Returns:
        List of synthesized mel spectrograms

    Raises:
        Exception: If model is not loaded or synthesis fails
    """
    global _model, _is_loaded

    if not _is_loaded or _model is None:
        raise Exception("Synthesizer model not loaded")

    # Check inputs
    if len(texts) != len(embeddings):
        raise Exception("Number of texts and embeddings must match")

    # Synthesize
    try:
        # Process texts
        from fmus_vox.voice.sv2tts_utils.text import text_to_sequence

        sequences = [text_to_sequence(text) for text in texts]

        # Generate spectrograms
        specs = _model.synthesize(sequences, embeddings)
        return specs

    except Exception as e:
        raise Exception(f"Failed to synthesize spectrograms: {str(e)}")

def preprocess_text(text: str) -> List[int]:
    """
    Preprocess text for synthesis.

    Args:
        text: Text to preprocess

    Returns:
        Sequence of token IDs
    """
    try:
        from fmus_vox.voice.sv2tts_utils.text import text_to_sequence
        return text_to_sequence(text)
    except Exception as e:
        raise Exception(f"Failed to preprocess text: {str(e)}")

# Stub class for future implementation
class Synthesizer:
    """
    Tacotron 2 synthesizer for SV2TTS.

    Note:
        This is a stub class for future implementation. Currently, the module uses
        functional API.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the synthesizer.

        Args:
            model_path: Path to the model file
            device: Device to use (cpu or cuda)
        """
        load_model(model_path, device)

    def synthesize_spectrograms(self, texts: List[str], embeddings: List[np.ndarray]) -> List[np.ndarray]:
        """
        Synthesize mel spectrograms from text and speaker embeddings.

        Args:
            texts: List of texts to synthesize
            embeddings: List of speaker embeddings

        Returns:
            List of synthesized mel spectrograms
        """
        return synthesize_spectrograms(texts, embeddings)

    def is_loaded(self) -> bool:
        """
        Check if the model is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return is_loaded()
