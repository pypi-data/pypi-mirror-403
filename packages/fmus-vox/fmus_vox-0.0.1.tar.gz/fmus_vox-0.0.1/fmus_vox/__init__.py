"""
fmus-vox: A human-oriented, powerful speech processing library.

This library provides a comprehensive suite of tools for audio processing,
speech-to-text, text-to-speech, and voice interaction with exceptional
developer experience and memorable APIs.
"""

__version__ = "0.0.1"

# Top-level imports for easy access
from fmus_vox.core.audio import Audio
from fmus_vox.stt import transcribe, Transcriber
from fmus_vox.tts import speak, Speaker
from fmus_vox.voice import clone_voice, VoiceCloner
from fmus_vox.wakeword import detect_wake_word, WakeWordDetector
from fmus_vox.stream import VoiceStream
from fmus_vox.chatbot import Conversation, chat
