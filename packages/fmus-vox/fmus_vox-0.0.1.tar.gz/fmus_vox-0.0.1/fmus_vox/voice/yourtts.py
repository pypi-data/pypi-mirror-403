"""
YourTTS voice cloning implementation for fmus-vox.

This module provides the YourTTSCloner implementation which uses the
YourTTS model from COQUI TTS for voice cloning.
"""

import os
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple

from fmus_vox.core.audio import Audio
from fmus_vox.core.config import get_config
from fmus_vox.core.errors import VoiceError, ModelError
from fmus_vox.core.utils import get_logger, download_if_not_exists, timed
from fmus_vox.voice.cloner import Voice, VoiceCloner

class YourTTSCloner(VoiceCloner):
    """
    YourTTS voice cloning implementation.

    This class implements voice cloning using the YourTTS model from COQUI TTS.

    Args:
        model: Model name/path (yourtts, yourtts-multi, or path to model)
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available pre-trained models
    AVAILABLE_MODELS = {
        "yourtts": {
            "url": "https://huggingface.co/coqui/yourtts/resolve/main/model.pth",
            "config_url": "https://huggingface.co/coqui/yourtts/raw/main/config.json",
            "languages": ["en"],
        },
        "yourtts-multi": {
            "url": "https://huggingface.co/coqui/yourtts-multi/resolve/main/model.pth",
            "config_url": "https://huggingface.co/coqui/yourtts-multi/raw/main/config.json",
            "languages": ["en", "fr", "de", "es", "it", "pt", "pl", "nl", "ru"],
        }
    }

    def __init__(self, model: str = "yourtts", device: Optional[str] = None, **kwargs):
        """
        Initialize the YourTTSCloner.

        Args:
            model: Model name/path (yourtts, yourtts-multi, or path to model)
            device: Computation device (cpu, cuda, auto)
            language: Target language for synthesis (default: auto-detect)
            **kwargs: Additional model-specific parameters
        """
        # Set default language from kwargs or config
        self.language = kwargs.pop("language", None) or get_config().get("voice.language", "en")

        # Call parent constructor
        super().__init__(model=model, device=device, **kwargs)

        # Attributes specific to YourTTS
        self.speaker_manager = None
        self.phonemizer = None

        # Check language support
        if self.model_name in self.AVAILABLE_MODELS:
            if self.language not in self.AVAILABLE_MODELS[self.model_name]["languages"]:
                supported = ", ".join(self.AVAILABLE_MODELS[self.model_name]["languages"])
                self.logger.warning(
                    f"Language '{self.language}' not supported by {self.model_name}. "
                    f"Supported languages: {supported}. Using 'en' instead."
                )
                self.language = "en"

    def _load_encoder(self):
        """
        Load the speaker encoder model.

        Returns:
            Speaker encoder model

        Raises:
            ModelError: If model loading fails
        """
        try:
            # Import TTS modules
            try:
                from TTS.utils.speakers import SpeakerManager
            except ImportError:
                raise ModelError("TTS not installed. Install with 'pip install TTS'")

            # Determine paths
            config = get_config()
            models_dir = config.get("paths.models_dir", os.path.expanduser("~/.fmus-vox/models"))
            os.makedirs(models_dir, exist_ok=True)

            # Path to encoder
            encoder_path = os.path.join(models_dir, "encoder", "model.pth")
            encoder_config_path = os.path.join(models_dir, "encoder", "config.json")

            # Download encoder if not exists
            download_if_not_exists(
                "https://huggingface.co/coqui/speaker-encoder/resolve/main/model.pth",
                encoder_path
            )
            download_if_not_exists(
                "https://huggingface.co/coqui/speaker-encoder/raw/main/config.json",
                encoder_config_path
            )

            # Create speaker manager
            self.speaker_manager = SpeakerManager(
                encoder_model_path=encoder_path,
                encoder_config_path=encoder_config_path,
                use_cuda=self.device == "cuda"
            )

            self.logger.debug("Loaded speaker encoder model")
            return self.speaker_manager

        except Exception as e:
            raise ModelError(f"Failed to load speaker encoder: {str(e)}")

    def _load_synthesizer(self):
        """
        Load the YourTTS synthesizer model.

        Returns:
            YourTTS model

        Raises:
            ModelError: If model loading fails
        """
        try:
            # Import TTS modules
            try:
                from TTS.utils.speakers import SpeakerManager
                from TTS.tts.models import setup_model
                from TTS.config.shared_configs import load_config
                from TTS.utils.audio import AudioProcessor
            except ImportError:
                raise ModelError("TTS not installed. Install with 'pip install TTS'")

            # Determine paths
            config = get_config()
            models_dir = config.get("paths.models_dir", os.path.expanduser("~/.fmus-vox/models"))
            os.makedirs(models_dir, exist_ok=True)

            yourtts_dir = os.path.join(models_dir, self.model_name)
            os.makedirs(yourtts_dir, exist_ok=True)

            model_path = os.path.join(yourtts_dir, "model.pth")
            config_path = os.path.join(yourtts_dir, "config.json")

            # Check if model is a pre-defined model or custom path
            if self.model_name in self.AVAILABLE_MODELS:
                # Download model if not exists
                download_if_not_exists(
                    self.AVAILABLE_MODELS[self.model_name]["url"],
                    model_path
                )
                download_if_not_exists(
                    self.AVAILABLE_MODELS[self.model_name]["config_url"],
                    config_path
                )
            else:
                # Assume model_name is a path
                if os.path.isdir(self.model_name):
                    model_path = os.path.join(self.model_name, "model.pth")
                    config_path = os.path.join(self.model_name, "config.json")
                else:
                    raise ModelError(f"Model path not found: {self.model_name}")

            # Load YourTTS
            model_config = load_config(config_path)
            self.audio_processor = AudioProcessor(**model_config.audio)

            # Setup model
            model = setup_model(model_config)

            # Load checkpoint
            checkpoint = torch.load(model_path, map_location=torch.device(self.device))
            model.load_state_dict(checkpoint["model"])

            # Set device
            model.to(self.device)
            model.eval()

            # Load phonemizer
            if "phoneme_language" in model_config and model_config.phoneme_language is not None:
                try:
                    from fmus_vox.core.phonemizer import Phonemizer
                    self.phonemizer = Phonemizer(language=model_config.phoneme_language)
                except Exception as e:
                    self.logger.warning(f"Failed to load phonemizer: {str(e)}")

            self.logger.debug(f"Loaded YourTTS model from {model_path}")
            return model

        except Exception as e:
            raise ModelError(f"Failed to load YourTTS model: {str(e)}")

    def _process_reference(self, audio: Audio) -> np.ndarray:
        """
        Process reference audio to extract speaker embedding.

        Args:
            audio: Reference audio

        Returns:
            Speaker embedding

        Raises:
            VoiceError: If processing fails
        """
        try:
            # Ensure encoder is loaded
            encoder = self._encoder.get()

            # Convert Audio to numpy
            waveform = audio.to_numpy()

            # Extract embedding
            embedding = encoder.compute_embedding(waveform)

            return embedding

        except Exception as e:
            raise VoiceError(f"Failed to process reference audio: {str(e)}")

    def _synthesize_with_voice(self, text: str, voice: Voice) -> Audio:
        """
        Synthesize text with YourTTS using a specific voice.

        Args:
            text: Text to synthesize
            voice: Voice to use

        Returns:
            Audio object with synthesized speech

        Raises:
            VoiceError: If synthesis fails
        """
        try:
            # Ensure synthesizer is loaded
            model = self._synthesizer.get()

            # Check if phonemizer is available
            if self.phonemizer is not None:
                phonemes = self.phonemizer.phonemize(text, self.language)
            else:
                phonemes = None

            # Run inference
            outputs = model.inference(
                text=text,
                speaker_embedding=voice.embeddings,
                language_id=self.language if hasattr(model, "language_manager") else None,
                phoneme_ids=phonemes
            )

            # Get waveform
            waveform = outputs["wav"]

            # Create Audio object
            audio = Audio(
                waveform=waveform,
                sample_rate=self.audio_processor.sample_rate
            )

            return audio

        except Exception as e:
            raise VoiceError(f"Failed to synthesize speech: {str(e)}")

# Import torch here to avoid issues with lazy loading
try:
    import torch
except ImportError:
    pass

# Register model
VoiceCloner.register_model("yourtts", YourTTSCloner)
