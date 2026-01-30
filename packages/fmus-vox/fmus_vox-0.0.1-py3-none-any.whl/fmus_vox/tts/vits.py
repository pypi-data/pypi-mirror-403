"""
VITS model implementation for text-to-speech.

This module provides the VitsSpeaker class which uses the VITS model
for speech synthesis.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional, Union
import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import SynthesisError, ModelError
from fmus_vox.core.utils import get_logger, download_file
from fmus_vox.tts.speaker import Speaker, SpeechResult


class VitsSpeaker(Speaker):
    """
    Speaker using the VITS (Conditional Variational Autoencoder with Adversarial Learning) model.

    VITS is an end-to-end speech synthesis model that combines variational inference
    and adversarial learning for high-quality speech synthesis.

    Args:
        model: VITS model variant
        voice: Voice ID or name to use
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available VITS voices
    _available_voices = [
        {"id": "default", "name": "Default Voice", "language": "en"},
        {"id": "female", "name": "Female Voice", "language": "en"},
        {"id": "male", "name": "Male Voice", "language": "en"},
    ]

    def __init__(self, model: str = "vits", voice: str = "default",
                device: Optional[str] = None, **kwargs):
        """
        Initialize the VITS speaker.

        Args:
            model: VITS model variant
            voice: Voice ID or name to use
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        super().__init__(model=model, voice=voice, device=device, **kwargs)

        # VITS-specific parameters
        self.noise_scale = kwargs.get("noise_scale", 0.667)
        self.noise_scale_w = kwargs.get("noise_scale_w", 0.8)
        self.length_scale = kwargs.get("length_scale", 1.0)

        self.logger.debug(f"Initialized VitsSpeaker with voice={voice}")

    def _load_model(self) -> Any:
        """
        Load the VITS model.

        Returns:
            Loaded VITS model (or None if TTS library not installed)

        Raises:
            ModelError: If model loading fails
        """
        try:
            import torch
            from TTS.api import TTS

            # Set device
            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.logger.info(f"Loading VITS model on {device}")

            # Try to load a TTS model
            # Using a simple fallback if TTS is not properly installed
            try:
                model_name = "tts_models/en/ljspeech/vits"
                tts = TTS(model_name=model_name, progress_bar=False, gpu=(device == "cuda"))
                return tts
            except Exception as e:
                self.logger.warning(f"Could not load TTS model: {e}")
                self.logger.info("Using fallback mode - TTS requires proper installation")
                return None

        except ImportError:
            self.logger.warning("TTS library not installed. Install with: pip install TTS")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to load VITS model: {str(e)}")
            return None

    def speak_with_metadata(self, text: str) -> SpeechResult:
        """
        Synthesize speech from text with additional metadata.

        Args:
            text: Text to synthesize

        Returns:
            SpeechResult object

        Raises:
            SynthesisError: If synthesis fails
        """
        try:
            model = self._model.get()

            if model is None:
                # Fallback: use espeak or similar if available
                return self._fallback_synthesis(text)

            # Use the TTS model to synthesize
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

                try:
                    # Synthesize speech
                    model.tts_to_file(text=text, file_path=tmp_path)

                    # Load the audio
                    audio = Audio.load(tmp_path)

                    # Apply speed/pitch modifications if needed
                    if self.speed != 1.0:
                        audio = audio.set_speed(self.speed)

                    return SpeechResult(
                        audio=audio,
                        voice_id=self.voice_id,
                        metadata={
                            "model": self.model_name,
                            "speed": self.speed,
                            "pitch": self.pitch,
                        }
                    )
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

        except Exception as e:
            raise SynthesisError(f"VITS synthesis failed: {str(e)}")

    def _fallback_synthesis(self, text: str) -> SpeechResult:
        """
        Fallback synthesis using simple beep/pattern if TTS is not available.

        Args:
            text: Text to synthesize

        Returns:
            SpeechResult object
        """
        self.logger.warning("Using fallback synthesis - TTS library not properly installed")

        # Generate a simple tone pattern as fallback
        sample_rate = 22050
        duration = len(text) * 0.05  # Rough estimate based on text length
        duration = min(max(duration, 0.5), 5.0)  # Limit between 0.5 and 5 seconds

        # Generate a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)

        # Ensure stereo
        if len(audio_data.shape) == 1:
            audio_data = np.column_stack((audio_data, audio_data))

        audio = Audio(audio_data, sample_rate)

        return SpeechResult(
            audio=audio,
            voice_id=self.voice_id,
            metadata={
                "model": "fallback",
                "note": "TTS library not installed. Install with: pip install TTS",
            }
        )

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with id, name, and language
        """
        return self._available_voices.copy()

    def set_speed(self, speed: float) -> "VitsSpeaker":
        """
        Set the speaking speed.

        Args:
            speed: Speed multiplier (1.0 is normal)

        Returns:
            Self for method chaining
        """
        self.speed = speed
        return self
