"""
ElevenLabs API implementation for text-to-speech.

This module provides the ElevenLabsSpeaker class which uses ElevenLabs'
cloud API for high-quality text-to-speech synthesis.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional
import requests

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import SynthesisError, ModelError
from fmus_vox.core.utils import get_logger
from fmus_vox.tts.speaker import Speaker, SpeechResult


class ElevenLabsSpeaker(Speaker):
    """
    Speaker using ElevenLabs' cloud TTS API.

    ElevenLabs provides high-quality neural TTS with realistic
    voices and natural prosody.

    Args:
        model: Always "elevenlabs" for this speaker
        voice: Voice ID or name to use
        api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
        model_id: ElevenLabs model to use (eleven_monolingual_v1, eleven_multilingual_v2, etc.)
        **kwargs: Additional parameters
    """

    # API endpoint
    _api_base = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        model: str = "elevenlabs",
        voice: str = "default",
        api_key: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        **kwargs
    ):
        """
        Initialize the ElevenLabs speaker.

        Args:
            model: Always "elevenlabs" for this speaker
            voice: Voice ID or name to use
            api_key: ElevenLabs API key
            model_id: ElevenLabs model to use
            **kwargs: Additional parameters
        """
        # Skip parent init to avoid model loading issues
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.model_name = model
        self.voice_id = voice
        self.device = "cpu"
        self.model_params = kwargs

        # ElevenLabs specific settings
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ModelError("ElevenLabs API key required. Set ELEVENLABS_API_KEY env var or pass api_key parameter.")

        self.model_id = model_id
        self.stability = kwargs.get("stability", 0.5)
        self.similarity_boost = kwargs.get("similarity_boost", 0.75)
        self.speed = kwargs.get("speed", 1.0)

        # Cache available voices
        self._voices_cache: Optional[List[Dict[str, Any]]] = None

        self.logger.debug(f"Initialized ElevenLabsSpeaker with voice={voice}, model_id={model_id}")

    def _load_model(self) -> Any:
        """No model to load for cloud API."""
        return None

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs API.

        Returns:
            List of voice dictionaries
        """
        if self._voices_cache is not None:
            return self._voices_cache

        try:
            response = requests.get(
                f"{self._api_base}/voices",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            voices = []

            for voice in data.get("voices", []):
                voices.append({
                    "id": voice["voice_id"],
                    "name": voice["name"],
                    "language": ", ".join(voice.get("labels", {}).values()),
                    "category": voice.get("category", "unknown")
                })

            self._voices_cache = voices
            return voices

        except Exception as e:
            self.logger.warning(f"Failed to fetch voices: {e}")
            return []

    def _resolve_voice_id(self, voice: str) -> str:
        """
        Resolve voice name to voice ID.

        Args:
            voice: Voice name or ID

        Returns:
            Voice ID
        """
        # If it looks like an ID (UUID format), use it directly
        if len(voice) == 36 and voice.count("-") == 4:
            return voice

        # Otherwise try to find by name
        voices = self._get_voices()
        for v in voices:
            if v["name"].lower() == voice.lower() or v["id"] == voice:
                return v["id"]

        # Default to first available voice
        if voices:
            self.logger.warning(f"Voice '{voice}' not found, using '{voices[0]['name']}'")
            return voices[0]["id"]

        raise ModelError(f"No voices available. Please check your API key.")

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
            # Resolve voice ID
            voice_id = self._resolve_voice_id(self.voice_id)

            # Prepare request
            url = f"{self._api_base}/text-to-speech/{voice_id}"

            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                }
            }

            # Add speed if not 1.0
            if self.speed != 1.0:
                # ElevenLabs uses rate parameter for speed
                payload["voice_settings"]["rate"] = self.speed

            # Make request
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                error_msg = response.text
                raise SynthesisError(f"ElevenLabs API error: {error_msg}")

            # Save to temp file and load as Audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            try:
                audio = Audio.load(tmp_path)

                return SpeechResult(
                    audio=audio,
                    voice_id=voice_id,
                    metadata={
                        "model": self.model_name,
                        "model_id": self.model_id,
                        "stability": self.stability,
                        "similarity_boost": self.similarity_boost,
                        "speed": self.speed,
                    }
                )
            finally:
                os.unlink(tmp_path)

        except requests.RequestException as e:
            raise SynthesisError(f"Failed to connect to ElevenLabs API: {str(e)}")
        except Exception as e:
            raise SynthesisError(f"ElevenLabs synthesis failed: {str(e)}")

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with id, name, and language
        """
        return self._get_voices()

    def set_voice(self, voice_id: str) -> "ElevenLabsSpeaker":
        """
        Set the voice to use.

        Args:
            voice_id: Voice ID or name

        Returns:
            Self for method chaining
        """
        self.voice_id = voice_id
        # Clear cache to force refresh
        self._voices_cache = None
        return self

    def set_stability(self, stability: float) -> "ElevenLabsSpeaker":
        """
        Set voice stability (0-1).

        Lower values are more variable, higher values are more stable.

        Args:
            stability: Stability value (0-1)

        Returns:
            Self for method chaining
        """
        self.stability = max(0.0, min(1.0, stability))
        return self

    def set_similarity_boost(self, boost: float) -> "ElevenLabsSpeaker":
        """
        Set voice similarity boost (0-1).

        Higher values are more similar to the original voice.

        Args:
            boost: Similarity boost value (0-1)

        Returns:
            Self for method chaining
        """
        self.similarity_boost = max(0.0, min(1.0, boost))
        return self
