"""
SV2TTS voice cloning implementation for fmus-vox.

This module provides the SV2TTSCloner implementation which uses the
SV2TTS (Tacotron+WaveRNN) architecture for voice cloning.
"""

import os
import numpy as np
from typing import Any, Dict, List, Optional, Union

from fmus_vox.core.audio import Audio
from fmus_vox.core.config import get_config
from fmus_vox.core.errors import VoiceError, ModelError
from fmus_vox.core.utils import get_logger, download_if_not_exists, timed
from fmus_vox.voice.cloner import Voice, VoiceCloner

class SV2TTSCloner(VoiceCloner):
    """
    SV2TTS voice cloning implementation.

    This class implements voice cloning using the SV2TTS architecture
    (Speaker Encoder + Tacotron 2 + WaveRNN).

    Args:
        model: Model name/variant (sv2tts, sv2tts-hq, or path to model)
        device: Computation device (cpu, cuda, auto)
        **kwargs: Additional model-specific parameters
    """

    # Available pre-trained models
    AVAILABLE_MODELS = {
        "sv2tts": {
            "encoder_url": "https://github.com/CorentinJ/Real-Time-Voice-Cloning/raw/master/encoder/saved_models/pretrained.pt",
            "synthesizer_url": "https://github.com/CorentinJ/Real-Time-Voice-Cloning/raw/master/synthesizer/saved_models/pretrained/pretrained.pt",
            "vocoder_url": "https://github.com/CorentinJ/Real-Time-Voice-Cloning/raw/master/vocoder/saved_models/pretrained/pretrained.pt",
            "languages": ["en"],
        },
        "sv2tts-hq": {
            "encoder_url": "https://example.com/fmus-vox/models/sv2tts-hq/encoder.pt",
            "synthesizer_url": "https://example.com/fmus-vox/models/sv2tts-hq/synthesizer.pt",
            "vocoder_url": "https://example.com/fmus-vox/models/sv2tts-hq/vocoder.pt",
            "languages": ["en"],
        }
    }

    def __init__(self, model: str = "sv2tts", device: Optional[str] = None, **kwargs):
        """
        Initialize the SV2TTSCloner.

        Args:
            model: Model name/variant (sv2tts, sv2tts-hq, or path to model)
            device: Computation device (cpu, cuda, auto)
            **kwargs: Additional model-specific parameters
        """
        # Call parent constructor
        super().__init__(model=model, device=device, **kwargs)

        # Attributes specific to SV2TTS
        self.encoder = None
        self.synthesizer = None
        self.vocoder = None

        # Use only english for now
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
            # Import dependencies
            try:
                # We'll use lazy import for SV2TTS
                from fmus_vox.voice.sv2tts_utils import encoder
            except ImportError:
                raise ModelError(
                    "SV2TTS dependencies not installed. Install with "
                    "'pip install numpy==1.19.3 tensorflow==1.15.0 librosa==0.8.0 inflect unidecode webrtcvad==2.0.10'"
                )

            # Determine paths
            config = get_config()
            models_dir = config.get("paths.models_dir", os.path.expanduser("~/.fmus-vox/models"))
            os.makedirs(models_dir, exist_ok=True)

            sv2tts_dir = os.path.join(models_dir, "sv2tts")
            os.makedirs(sv2tts_dir, exist_ok=True)

            encoder_dir = os.path.join(sv2tts_dir, "encoder")
            os.makedirs(encoder_dir, exist_ok=True)

            encoder_path = os.path.join(encoder_dir, "model.pt")

            # Download encoder if not exists
            if self.model_name in self.AVAILABLE_MODELS:
                download_if_not_exists(
                    self.AVAILABLE_MODELS[self.model_name]["encoder_url"],
                    encoder_path
                )
            else:
                # Check if model_name is a directory with models
                if os.path.isdir(self.model_name):
                    encoder_path = os.path.join(self.model_name, "encoder.pt")
                    if not os.path.exists(encoder_path):
                        raise ModelError(f"Encoder model not found at {encoder_path}")
                else:
                    raise ModelError(f"Model path not found: {self.model_name}")

            # Load encoder
            device = "cuda" if self.device == "cuda" else "cpu"
            encoder.load_model(encoder_path, device=device)

            self.logger.debug(f"Loaded speaker encoder model from {encoder_path}")
            return encoder

        except Exception as e:
            raise ModelError(f"Failed to load speaker encoder: {str(e)}")

    def _load_synthesizer(self):
        """
        Load the Tacotron synthesizer model.

        Returns:
            Synthesizer model

        Raises:
            ModelError: If model loading fails
        """
        try:
            # Import dependencies
            try:
                from fmus_vox.voice.sv2tts_utils import synthesizer
            except ImportError:
                raise ModelError("SV2TTS dependencies not installed")

            # Determine paths
            config = get_config()
            models_dir = config.get("paths.models_dir", os.path.expanduser("~/.fmus-vox/models"))

            sv2tts_dir = os.path.join(models_dir, "sv2tts")
            os.makedirs(sv2tts_dir, exist_ok=True)

            synth_dir = os.path.join(sv2tts_dir, "synthesizer")
            os.makedirs(synth_dir, exist_ok=True)

            synth_path = os.path.join(synth_dir, "model.pt")

            # Download synthesizer if not exists
            if self.model_name in self.AVAILABLE_MODELS:
                download_if_not_exists(
                    self.AVAILABLE_MODELS[self.model_name]["synthesizer_url"],
                    synth_path
                )
            else:
                # Check if model_name is a directory with models
                if os.path.isdir(self.model_name):
                    synth_path = os.path.join(self.model_name, "synthesizer.pt")
                    if not os.path.exists(synth_path):
                        raise ModelError(f"Synthesizer model not found at {synth_path}")
                else:
                    raise ModelError(f"Model path not found: {self.model_name}")

            # Load synthesizer
            device = "cuda" if self.device == "cuda" else "cpu"
            synthesizer.load_model(synth_path, device=device)

            self.logger.debug(f"Loaded synthesizer model from {synth_path}")
            return synthesizer

        except Exception as e:
            raise ModelError(f"Failed to load synthesizer: {str(e)}")

    def _load_vocoder(self):
        """
        Load the WaveRNN vocoder model.

        Returns:
            Vocoder model

        Raises:
            ModelError: If model loading fails
        """
        try:
            # Import dependencies
            try:
                from fmus_vox.voice.sv2tts_utils import vocoder
            except ImportError:
                raise ModelError("SV2TTS dependencies not installed")

            # Determine paths
            config = get_config()
            models_dir = config.get("paths.models_dir", os.path.expanduser("~/.fmus-vox/models"))

            sv2tts_dir = os.path.join(models_dir, "sv2tts")
            os.makedirs(sv2tts_dir, exist_ok=True)

            vocoder_dir = os.path.join(sv2tts_dir, "vocoder")
            os.makedirs(vocoder_dir, exist_ok=True)

            vocoder_path = os.path.join(vocoder_dir, "model.pt")

            # Download vocoder if not exists
            if self.model_name in self.AVAILABLE_MODELS:
                download_if_not_exists(
                    self.AVAILABLE_MODELS[self.model_name]["vocoder_url"],
                    vocoder_path
                )
            else:
                # Check if model_name is a directory with models
                if os.path.isdir(self.model_name):
                    vocoder_path = os.path.join(self.model_name, "vocoder.pt")
                    if not os.path.exists(vocoder_path):
                        raise ModelError(f"Vocoder model not found at {vocoder_path}")
                else:
                    raise ModelError(f"Model path not found: {self.model_name}")

            # Load vocoder
            device = "cuda" if self.device == "cuda" else "cpu"
            vocoder.load_model(vocoder_path, device=device)

            self.logger.debug(f"Loaded vocoder model from {vocoder_path}")
            return vocoder

        except Exception as e:
            raise ModelError(f"Failed to load vocoder: {str(e)}")

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

            # Get waveform
            wav = audio.to_numpy()

            # Compute embedding
            embedding = encoder.embed_utterance(wav)

            return embedding

        except Exception as e:
            raise VoiceError(f"Failed to process reference audio: {str(e)}")

    def _synthesize_with_voice(self, text: str, voice: Voice) -> Audio:
        """
        Synthesize text with SV2TTS using a specific voice.

        Args:
            text: Text to synthesize
            voice: Voice to use

        Returns:
            Audio object with synthesized speech

        Raises:
            VoiceError: If synthesis fails
        """
        try:
            # Load models if not loaded
            synthesizer = self._synthesizer.get()

            # We delay vocoder loading until we actually need it
            vocoder = self._load_vocoder()

            # Process text through synthesizer
            texts = [text]
            embeds = [voice.embeddings]
            specs = synthesizer.synthesize_spectrograms(texts, embeds)
            spec = specs[0]

            # Generate waveform
            generated_wav = vocoder.infer_waveform(spec)

            # Create Audio object
            audio = Audio(
                waveform=generated_wav,
                sample_rate=16000  # SV2TTS uses 16kHz
            )

            return audio

        except Exception as e:
            raise VoiceError(f"Failed to synthesize speech: {str(e)}")

# Register model
VoiceCloner.register_model("sv2tts", SV2TTSCloner)
