"""
Custom exceptions for fmus-vox.

This module contains all the custom exceptions used throughout the library
to provide clear and informative error messages.
"""

class FmusVoxError(Exception):
    """Base exception class for all fmus-vox errors."""
    pass

class AudioError(FmusVoxError):
    """Exception raised for errors in audio processing."""
    pass

class DeviceError(FmusVoxError):
    """Exception raised for errors with audio devices."""
    pass

class ModelError(FmusVoxError):
    """Exception raised for errors related to models."""
    pass

class ModelLoadError(ModelError):
    """Exception raised when a model fails to load."""
    pass

class DependencyError(FmusVoxError):
    """Exception raised when a required dependency is missing."""
    pass

class TranscriptionError(FmusVoxError):
    """Exception raised for errors in speech-to-text operations."""
    pass

class SynthesisError(FmusVoxError):
    """Exception raised for errors in text-to-speech operations."""
    pass

class VoiceError(FmusVoxError):
    """Exception raised for errors in voice manipulation operations."""
    pass

class PhonemizerError(FmusVoxError):
    """Exception raised for errors in phonemization operations."""
    pass

class WakewordError(FmusVoxError):
    """Exception raised for errors in wake word detection."""
    pass

class StreamError(FmusVoxError):
    """Exception raised for errors in audio streaming."""
    pass

class ChatbotError(FmusVoxError):
    """Exception raised for errors in chatbot operations."""
    pass

class ConfigError(FmusVoxError):
    """Exception raised for configuration errors."""
    pass
