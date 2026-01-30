"""
Phonemizer utility for text-to-phoneme conversion.

This module provides the Phonemizer class which converts text to
phonetic transcriptions for various languages.
"""

import os
import re
import json
from typing import Dict, List, Optional, Union

from fmus_vox.core.utils import get_logger, download_if_not_exists
from fmus_vox.core.errors import PhonemizerError

class Phonemizer:
    """
    Text to phoneme converter for multiple languages.

    This class provides methods to convert text to phonetic transcriptions,
    which can improve the quality of speech synthesis.

    Args:
        language: Default language for phonemization
        backend: Phonemization backend ('espeak', 'gruut', or 'external')
        **kwargs: Additional backend-specific parameters
    """

    # Map of language codes to full names and backend-specific codes
    LANGUAGE_MAP = {
        "en": {"name": "English", "espeak": "en-us", "gruut": "en-us"},
        "fr": {"name": "French", "espeak": "fr-fr", "gruut": "fr-fr"},
        "de": {"name": "German", "espeak": "de-de", "gruut": "de-de"},
        "es": {"name": "Spanish", "espeak": "es-es", "gruut": "es-es"},
        "it": {"name": "Italian", "espeak": "it-it", "gruut": "it-it"},
        "pt": {"name": "Portuguese", "espeak": "pt-br", "gruut": "pt-br"},
        "ru": {"name": "Russian", "espeak": "ru-ru", "gruut": None},
        "nl": {"name": "Dutch", "espeak": "nl", "gruut": "nl"},
        "pl": {"name": "Polish", "espeak": "pl", "gruut": None},
        "zh": {"name": "Chinese", "espeak": "zh", "gruut": None},
        "ja": {"name": "Japanese", "espeak": "ja", "gruut": None},
        "ko": {"name": "Korean", "espeak": "ko", "gruut": None},
    }

    def __init__(self, language: str = "en", backend: str = "auto", **kwargs):
        """
        Initialize the phonemizer.

        Args:
            language: Default language for phonemization
            backend: Phonemization backend ('espeak', 'gruut', 'external', or 'auto')
            **kwargs: Additional backend-specific parameters
        """
        self.logger = get_logger(f"{__name__}.Phonemizer")

        # Validate language
        if language not in self.LANGUAGE_MAP:
            supported = ", ".join(self.LANGUAGE_MAP.keys())
            self.logger.warning(
                f"Language '{language}' not supported. Using 'en' instead. "
                f"Supported languages: {supported}"
            )
            language = "en"

        self.language = language
        self._backend = None
        self._backend_name = None

        # Choose backend
        if backend == "auto":
            # Try to use gruut first, fall back to espeak
            backend = self._auto_select_backend()

        # Initialize chosen backend
        if backend == "espeak":
            self._init_espeak_backend(**kwargs)
        elif backend == "gruut":
            self._init_gruut_backend(**kwargs)
        elif backend == "external":
            self._init_external_backend(**kwargs)
        else:
            raise PhonemizerError(f"Unsupported phonemizer backend: {backend}")

    def _auto_select_backend(self) -> str:
        """
        Automatically select the best available backend.

        Returns:
            Name of the selected backend
        """
        # Try to import gruut
        try:
            import gruut
            return "gruut"
        except ImportError:
            self.logger.debug("gruut not found, trying espeak")

        # Try to check if espeak is installed
        try:
            import subprocess
            result = subprocess.run(["espeak", "--version"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "espeak"
        except (FileNotFoundError, ImportError):
            self.logger.debug("espeak not found")

        # Fall back to external if neither is available
        return "external"

    def _init_espeak_backend(self, **kwargs):
        """
        Initialize the espeak backend.

        Args:
            **kwargs: Additional espeak-specific parameters

        Raises:
            PhonemizerError: If espeak initialization fails
        """
        try:
            # Attempt to import phonemizer
            try:
                from phonemizer.backend import EspeakBackend
                from phonemizer.backend.espeak.wrapper import EspeakWrapper
            except ImportError:
                raise PhonemizerError(
                    "phonemizer not installed. Install with "
                    "'pip install phonemizer' and ensure espeak is in your PATH."
                )

            # Get language code for espeak
            lang_code = self.LANGUAGE_MAP[self.language]["espeak"]

            # Create backend
            self._backend = EspeakBackend(
                language=lang_code,
                with_stress=kwargs.get("with_stress", True),
                preserve_punctuation=kwargs.get("preserve_punctuation", True),
                punctuation_marks=kwargs.get("punctuation_marks", ";:,.!?¡¿—…""-()"),
                with_variations=kwargs.get("with_variations", False)
            )

            self._backend_name = "espeak"
            self.logger.debug(f"Initialized espeak backend with language={lang_code}")

        except Exception as e:
            raise PhonemizerError(f"Failed to initialize espeak backend: {str(e)}")

    def _init_gruut_backend(self, **kwargs):
        """
        Initialize the gruut backend.

        Args:
            **kwargs: Additional gruut-specific parameters

        Raises:
            PhonemizerError: If gruut initialization fails
        """
        try:
            # Attempt to import gruut
            try:
                import gruut
            except ImportError:
                raise PhonemizerError(
                    "gruut not installed. Install with "
                    "'pip install gruut gruut-lang-en'"
                )

            # Get language code for gruut
            lang_code = self.LANGUAGE_MAP[self.language]["gruut"]

            if lang_code is None:
                raise PhonemizerError(f"Language '{self.language}' not supported by gruut")

            # Initialize gruut tokenizer
            try:
                from gruut import sentences
                self._backend = sentences
                self._gruut_lang = lang_code
            except Exception as e:
                raise PhonemizerError(f"Failed to initialize gruut: {str(e)}")

            self._backend_name = "gruut"
            self.logger.debug(f"Initialized gruut backend with language={lang_code}")

        except Exception as e:
            raise PhonemizerError(f"Failed to initialize gruut backend: {str(e)}")

    def _init_external_backend(self, **kwargs):
        """
        Initialize the external backend which uses pre-computed mappings.

        Args:
            **kwargs: Additional parameters

        Raises:
            PhonemizerError: If initialization fails
        """
        try:
            # Set dictionary path
            dict_path = kwargs.get("dict_path", None)

            if dict_path is None:
                # Use built-in dictionaries
                from fmus_vox.core.config import get_config
                config = get_config()

                data_dir = config.get(
                    "paths.data_dir",
                    os.path.expanduser("~/.fmus-vox/data")
                )
                os.makedirs(data_dir, exist_ok=True)

                dict_path = os.path.join(data_dir, f"phoneme_dict_{self.language}.json")

                # Download if not exists
                if not os.path.exists(dict_path):
                    # This is a placeholder - in production, we'd download from a real URL
                    dict_url = f"https://example.com/fmus-vox/dicts/phoneme_dict_{self.language}.json"
                    try:
                        download_if_not_exists(dict_url, dict_path)
                    except Exception as e:
                        # Create a minimal dictionary if download fails
                        self.logger.warning(
                            f"Failed to download phoneme dictionary, creating minimal: {str(e)}"
                        )
                        with open(dict_path, "w") as f:
                            json.dump({}, f)

            # Load dictionary
            with open(dict_path, "r") as f:
                self._phoneme_dict = json.load(f)

            self._backend = self._phoneme_dict
            self._backend_name = "external"
            self.logger.debug(f"Initialized external phoneme dictionary from {dict_path}")

        except Exception as e:
            raise PhonemizerError(f"Failed to initialize external backend: {str(e)}")

    def phonemize(self, text: str, language: Optional[str] = None) -> str:
        """
        Convert text to phonemes.

        Args:
            text: Text to convert
            language: Language code (if None, uses default language)

        Returns:
            Phonetic transcription of the text

        Raises:
            PhonemizerError: If phonemization fails
        """
        # Use default language if not specified
        lang = language or self.language

        # Validate language
        if lang not in self.LANGUAGE_MAP:
            raise PhonemizerError(f"Unsupported language: {lang}")

        # Clean text
        text = text.strip()
        if not text:
            return ""

        try:
            # Dispatch to appropriate backend
            if self._backend_name == "espeak":
                return self._phonemize_espeak(text, lang)
            elif self._backend_name == "gruut":
                return self._phonemize_gruut(text, lang)
            elif self._backend_name == "external":
                return self._phonemize_external(text, lang)
            else:
                raise PhonemizerError(f"No phonemizer backend initialized")
        except Exception as e:
            raise PhonemizerError(f"Phonemization failed: {str(e)}")

    def _phonemize_espeak(self, text: str, language: str) -> str:
        """
        Phonemize text using espeak backend.

        Args:
            text: Text to convert
            language: Language code

        Returns:
            Phonetic transcription
        """
        # Check if language matches current configuration
        lang_code = self.LANGUAGE_MAP[language]["espeak"]
        if lang_code != self._backend.language:
            # Reconfigure backend for this language
            from phonemizer.backend import EspeakBackend
            self._backend = EspeakBackend(
                language=lang_code,
                with_stress=self._backend.with_stress,
                preserve_punctuation=self._backend.preserve_punctuation,
                punctuation_marks=self._backend.punctuation_marks,
                with_variations=self._backend.with_variations
            )

        # Phonemize
        phonemes = self._backend.phonemize([text], strip=True)[0]
        return phonemes

    def _phonemize_gruut(self, text: str, language: str) -> str:
        """
        Phonemize text using gruut backend.

        Args:
            text: Text to convert
            language: Language code

        Returns:
            Phonetic transcription
        """
        # Check if language is supported
        gruut_lang = self.LANGUAGE_MAP[language]["gruut"]
        if gruut_lang is None:
            raise PhonemizerError(f"Language '{language}' not supported by gruut")

        # Generate phonemes
        phonemes = []
        for sentence in self._backend(text, lang=gruut_lang):
            for word in sentence:
                if hasattr(word, "phonemes") and word.phonemes:
                    # Join phonemes for this word
                    word_phonemes = " ".join(word.phonemes)
                    phonemes.append(word_phonemes)
                else:
                    # Pass through unknown words
                    phonemes.append(word.text)

        return " ".join(phonemes)

    def _phonemize_external(self, text: str, language: str) -> str:
        """
        Phonemize text using external dictionary.

        Args:
            text: Text to convert
            language: Language code

        Returns:
            Phonetic transcription
        """
        # Simple word-by-word lookup
        words = re.findall(r'\b\w+\b', text.lower())
        result = []

        for word in words:
            if word in self._phoneme_dict:
                result.append(self._phoneme_dict[word])
            else:
                # Just use the word itself if not in dictionary
                result.append(word)

        return " ".join(result)

# Create alias for backward compatibility
def phonemize(text: str, language: str = "en") -> str:
    """
    Convert text to phonemes (convenience function).

    Args:
        text: Text to convert
        language: Language code

    Returns:
        Phonetic transcription
    """
    phonemizer = Phonemizer(language=language)
    return phonemizer.phonemize(text)
