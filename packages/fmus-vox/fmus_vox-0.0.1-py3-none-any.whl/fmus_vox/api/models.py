"""
Pydantic models for the API.

This module defines the data models used for request and response
validation in the API endpoints.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# Error model
class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")

# Health check model
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")

# Model info model
class ModelInfoResponse(BaseModel):
    """Model information response."""

    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    languages: Optional[List[str]] = Field(None, description="Supported languages")
    voices: Optional[List[str]] = Field(None, description="Available voices")
    features: List[str] = Field([], description="Model features")

# Transcription models
class TranscriptionSegment(BaseModel):
    """Segment of a transcription with timestamps."""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Text content")

class TranscriptionRequest(BaseModel):
    """Request model for transcription."""

    model: str = Field("whisper", description="STT model to use")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'fr')")
    timestamps: bool = Field(False, description="Include timestamps in the result")

class TranscriptionResponse(BaseModel):
    """Response model for transcription."""

    text: str = Field(..., description="Transcribed text")
    segments: List[TranscriptionSegment] = Field([], description="Segments with timestamps")
    language: Optional[str] = Field(None, description="Detected or specified language")

# TTS models
class TTSRequest(BaseModel):
    """Request model for text-to-speech."""

    text: str = Field(..., description="Text to synthesize")
    model: str = Field("vits", description="TTS model to use")
    voice: str = Field("default", description="Voice to use")
    speed: float = Field(1.0, description="Speaking speed (0.5-2.0)", ge=0.5, le=2.0)

class AudioResponse(BaseModel):
    """Response model for audio data."""

    format: str = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Sample rate")
    duration: float = Field(..., description="Audio duration in seconds")
    url: Optional[str] = Field(None, description="URL to audio file (if applicable)")

# Voice cloning models
class VoiceCloningRequest(BaseModel):
    """Request model for voice cloning."""

    text: str = Field(..., description="Text to synthesize with cloned voice")
    model: str = Field("yourtts", description="Voice cloning model to use")

# Chatbot models
class ChatRequest(BaseModel):
    """Request model for chat."""

    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field({}, description="Chat context (e.g., conversation history)")

class ChatResponse(BaseModel):
    """Response model for chat."""

    response: str = Field(..., description="Assistant response")
    context: Dict[str, Any] = Field({}, description="Updated chat context")
