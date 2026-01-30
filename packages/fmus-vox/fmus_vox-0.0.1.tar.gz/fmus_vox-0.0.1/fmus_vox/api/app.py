"""
FastAPI application for fmus-vox.

This module provides a FastAPI application with endpoints for interacting
with the fmus-vox library functionality.
"""

import os
import io
import tempfile
import asyncio
import uvicorn
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Body, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from fmus_vox import Audio, transcribe, speak, clone_voice, chat
from fmus_vox.core.errors import FmusVoxError
from fmus_vox.stream.microphone import Microphone
from fmus_vox.stream.audioplayer import AudioPlayer
from fmus_vox.stream.voice_stream import VoiceStream, StreamBuffer
from fmus_vox.api.models import (
    TranscriptionRequest,
    TranscriptionResponse,
    TTSRequest,
    AudioResponse,
    VoiceCloningRequest,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ModelInfoResponse,
    ErrorResponse
)

# Create FastAPI app
app = FastAPI(
    title="fmus-vox API",
    description="API for human-oriented speech processing with fmus-vox",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directory for audio files
os.makedirs("temp", exist_ok=True)

# Active streaming connections
active_connections = {}

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "fmus-vox API",
        "version": "0.0.1",
        "description": "Human-oriented speech processing API",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.0.1"
    }

@app.get("/models", response_model=Dict[str, List[str]], tags=["General"])
async def list_models():
    """List available models for each functionality."""
    return {
        "stt": ["whisper"],
        "tts": ["vits"],
        "voice_cloning": ["yourtts", "sv2tts"]
    }

@app.get("/models/{model_type}/{model_name}", response_model=ModelInfoResponse, tags=["General"])
async def get_model_info(model_type: str, model_name: str):
    """Get information about a specific model."""
    # Check if model type is valid
    if model_type not in ["stt", "tts", "voice_cloning"]:
        raise HTTPException(status_code=404, detail=f"Model type '{model_type}' not found")

    # Dictionary mapping model names to info for each type
    model_info = {
        "stt": {
            "whisper": {
                "name": "Whisper",
                "description": "OpenAI's Whisper speech recognition model",
                "languages": ["en", "fr", "de", "es", "it", "ja", "zh", "ru"],
                "features": ["timestamps", "language_detection"]
            }
        },
        "tts": {
            "vits": {
                "name": "VITS",
                "description": "Conditional Variational Autoencoder with Adversarial Learning for End-to-End TTS",
                "voices": ["default", "female", "male"],
                "features": ["speed_control", "style_control"]
            }
        },
        "voice_cloning": {
            "yourtts": {
                "name": "YourTTS",
                "description": "Zero-shot multi-speaker TTS model",
                "features": ["zero_shot_cloning", "multi_language"]
            },
            "sv2tts": {
                "name": "SV2TTS",
                "description": "Voice cloning with speaker verification and Tacotron 2",
                "features": ["zero_shot_cloning"]
            }
        }
    }

    # Check if model exists
    if model_name not in model_info.get(model_type, {}):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found for type '{model_type}'")

    return model_info[model_type][model_name]

# STT Endpoints

@app.post("/stt/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text"])
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    model: str = Form("whisper", description="STT model to use"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en', 'fr')"),
    timestamps: bool = Form(False, description="Include timestamps in the result"),
):
    """
    Transcribe audio file to text.

    Accepts audio in various formats and returns the transcription.
    Optionally includes timestamps for each segment.
    """
    try:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.filename.split('.')[-1]}") as temp:
            temp.write(await audio_file.read())
            temp_path = temp.name

        # Load audio
        audio = Audio.load(temp_path)

        # Remove temp file
        os.unlink(temp_path)

        # Perform transcription
        result = transcribe(audio, model=model, language=language, timestamps=timestamps)

        # Format response based on timestamps flag
        if timestamps and isinstance(result, dict):
            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "language": result.get("language", language)
            }
        else:
            return {
                "text": result if isinstance(result, str) else result.get("text", ""),
                "segments": [],
                "language": language
            }

    except FmusVoxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

@app.websocket("/stt/stream")
async def stream_transcribe(websocket: WebSocket):
    """
    Streaming transcription endpoint.

    Accepts streaming audio input and returns real-time transcription.
    Uses WebSocket for bidirectional communication.
    """
    await websocket.accept()

    # Initialize streaming resources
    connection_id = str(id(websocket))
    voice_stream = None

    try:
        # Receive configuration
        config = await websocket.receive_json()
        model = config.get("model", "whisper")
        language = config.get("language")

        # Create stream buffer and voice stream
        buffer = StreamBuffer(max_duration=60.0, sample_rate=16000, channels=1)
        voice_stream = VoiceStream(sample_rate=16000, channels=1)

        # Track this connection
        active_connections[connection_id] = voice_stream

        # Set up speech detection callback
        async def on_speech_end(audio, info):
            # Transcribe the audio
            try:
                result = transcribe(audio, model=model, language=language)

                # Send transcription result
                await websocket.send_json({
                    "type": "transcription",
                    "text": result if isinstance(result, str) else result.get("text", ""),
                    "duration": audio.duration
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error transcribing: {str(e)}"
                })

        # Set up speech detection callback
        voice_stream.on_speech_end(lambda audio, info: asyncio.create_task(on_speech_end(audio, info)))

        # Set up VAD callback
        async def on_vad(is_speech, info):
            await websocket.send_json({
                "type": "vad",
                "is_speech": is_speech
            })

        voice_stream.on_vad(lambda is_speech, info: asyncio.create_task(on_vad(is_speech, info)))

        # Start the voice stream
        voice_stream.start()

        # Send ready message
        await websocket.send_json({
            "type": "ready",
            "message": "Streaming transcription started"
        })

        # Process audio chunks
        while True:
            # Receive audio chunk
            audio_data = await websocket.receive_bytes()

            # Add to stream buffer
            buffer.write(audio_data)

            # Process the audio
            chunk = buffer.read_latest(0.5)  # Read latest 500ms
            voice_stream.process_audio(chunk)

    except WebSocketDisconnect:
        print(f"Client disconnected: {connection_id}")
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
        except:
            pass
        print(f"Error in streaming transcription: {str(e)}")
    finally:
        # Clean up resources
        if voice_stream:
            voice_stream.stop()

        # Remove from active connections
        if connection_id in active_connections:
            del active_connections[connection_id]

        # Close websocket if still connected
        try:
            await websocket.close()
        except:
            pass

# TTS Endpoints

@app.post("/tts/speak", tags=["Text-to-Speech"])
async def synthesize_speech(
    request: TTSRequest = Body(..., description="TTS request parameters"),
):
    """
    Synthesize text to speech.

    Converts text to speech using the specified model and voice,
    and returns the audio file.
    """
    try:
        # Synthesize speech
        audio = speak(
            request.text,
            model=request.model,
            voice=request.voice,
            speed=request.speed
        )

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        audio.save(temp_path)

        # Return audio file
        return FileResponse(
            temp_path,
            media_type="audio/wav",
            filename=f"speech_{hash(request.text)}.wav",
            background=BackgroundTasks().add_task(os.unlink, temp_path)
        )

    except FmusVoxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")

@app.websocket("/tts/stream")
async def stream_tts(websocket: WebSocket):
    """
    Streaming TTS endpoint.

    Accepts text input and streams the synthesized audio.
    Uses WebSocket for bidirectional communication.
    """
    await websocket.accept()

    try:
        # Receive configuration
        config = await websocket.receive_json()
        model = config.get("model", "vits")
        voice = config.get("voice", "default")
        speed = config.get("speed", 1.0)
        text = config.get("text", "")

        if not text:
            await websocket.send_json({
                "type": "error",
                "message": "No text provided for synthesis"
            })
            return

        # Synthesize speech
        audio = speak(text, model=model, voice=voice, speed=speed)

        # Send audio metadata
        await websocket.send_json({
            "type": "metadata",
            "sample_rate": audio.sample_rate,
            "channels": audio.channels,
            "duration": audio.duration,
            "format": "float32"
        })

        # Stream audio in chunks
        chunk_size = 4096  # Bytes per chunk
        audio_bytes = audio.data.tobytes()

        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i+chunk_size]
            await websocket.send_bytes(chunk)
            await asyncio.sleep(0.01)  # Small delay to prevent overwhelming the client

        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "message": "TTS streaming complete"
        })

    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
        except:
            pass
        print(f"Error in streaming TTS: {str(e)}")
    finally:
        # Close websocket if still connected
        try:
            await websocket.close()
        except:
            pass

# Voice Cloning Endpoints

@app.post("/voice/clone", tags=["Voice Cloning"])
async def clone_voice_endpoint(
    text: str = Form(..., description="Text to synthesize with cloned voice"),
    reference_audio: UploadFile = File(..., description="Reference audio for voice cloning"),
    model: str = Form("yourtts", description="Voice cloning model to use"),
):
    """
    Clone voice and synthesize text.

    Uses a reference audio file to clone a voice, then
    synthesizes the provided text with the cloned voice.
    """
    try:
        # Save uploaded reference to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{reference_audio.filename.split('.')[-1]}") as temp:
            temp.write(await reference_audio.read())
            temp_path = temp.name

        # Load reference audio
        reference = Audio.load(temp_path)

        # Remove temp file
        os.unlink(temp_path)

        # Clone voice and synthesize
        audio = clone_voice(reference, text, model=model)

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        audio.save(temp_path)

        # Return audio file
        return FileResponse(
            temp_path,
            media_type="audio/wav",
            filename=f"cloned_voice_{hash(text)}.wav",
            background=BackgroundTasks().add_task(os.unlink, temp_path)
        )

    except FmusVoxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cloning voice: {str(e)}")

# Chatbot Endpoints

@app.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat_endpoint(
    request: ChatRequest = Body(..., description="Chat request parameters"),
):
    """
    Generate a chat response.

    Sends a message to the chatbot and returns the generated response.
    """
    try:
        # Generate response
        response = chat(
            request.message,
            context=request.context
        )

        return {
            "response": response,
            "context": request.context
        }

    except FmusVoxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chat response: {str(e)}")

@app.websocket("/chat/stream")
async def stream_chat(websocket: WebSocket):
    """
    Streaming chat endpoint.

    Streams chat responses token by token using WebSocket communication.
    """
    await websocket.accept()

    try:
        # Receive message
        data = await websocket.receive_json()
        message = data.get("message", "")
        context = data.get("context", [])

        if not message:
            await websocket.send_json({
                "type": "error",
                "message": "No message provided"
            })
            return

        # Send processing message
        await websocket.send_json({
            "type": "status",
            "message": "Processing your message..."
        })

        # Generate response (in a real implementation, this would stream tokens)
        response = chat(message, context=context)

        # Simulate streaming by sending response in chunks
        words = response.split()
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3])
            await websocket.send_json({
                "type": "token",
                "text": chunk
            })
            await asyncio.sleep(0.2)  # Simulate thinking time

        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "message": "Chat response complete",
            "context": context
        })

    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
        except:
            pass
        print(f"Error in streaming chat: {str(e)}")
    finally:
        # Close websocket if still connected
        try:
            await websocket.close()
        except:
            pass

# Audio Device Endpoints

@app.get("/audio/devices/input", tags=["Audio Devices"])
async def list_input_devices():
    """List available audio input devices."""
    try:
        devices = Microphone.list_devices()
        return {
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing input devices: {str(e)}")

@app.get("/audio/devices/output", tags=["Audio Devices"])
async def list_output_devices():
    """List available audio output devices."""
    try:
        devices = AudioPlayer.list_devices()
        return {
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing output devices: {str(e)}")

# API server function
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False, debug: bool = False):
    """
    Start the API server.

    Args:
        host: Host to bind the server to
        port: Port to bind the server to
        reload: Enable auto-reload for development
        debug: Enable debug mode
    """
    uvicorn.run(
        "fmus_vox.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info"
    )

# Cleanup handler
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when shutting down."""
    # Close any active voice streams
    for connection_id, voice_stream in active_connections.items():
        try:
            voice_stream.stop()
        except:
            pass

    # Clear active connections
    active_connections.clear()
