"""
WebSocket streaming functionality for real-time audio.

This module provides WebSocket support for streaming audio data
and transcription results in real-time.
"""

import asyncio
import json
import time
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
from pathlib import Path

from fmus_vox.core.audio import Audio
from fmus_vox.core.utils import get_logger
from fmus_vox.stream.voice_stream import VoiceStream


class AudioWebSocket:
    """
    WebSocket handler for streaming audio data.

    This class manages WebSocket connections for real-time audio streaming,
    supporting bidirectional communication with audio input and output.

    Args:
        sample_rate: Audio sample rate
        channels: Number of audio channels
        format: Audio format (float32, int16, etc.)
        chunk_size: Size of audio chunks for streaming
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        format: str = "float32",
        chunk_size: int = 4096
    ):
        """
        Initialize the WebSocket audio stream.

        Args:
            sample_rate: Audio sample rate
            channels: Number of audio channels (1=mono, 2=stereo)
            format: Audio format
            chunk_size: Size of audio chunks
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.chunk_size = chunk_size

        # Callbacks
        self.on_audio_received: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        self.on_synthesis: Optional[Callable] = None

        # State
        self._is_connected = False
        self._is_streaming = False

        # Buffers
        self._input_buffer: bytes = b""
        self._output_buffer: bytes = b""

        self.logger.debug(f"Initialized AudioWebSocket with sample_rate={sample_rate}, channels={channels}")

    async def connect(self, uri: str) -> None:
        """
        Connect to a WebSocket server.

        Args:
            uri: WebSocket URI to connect to

        Raises:
            ConnectionError: If connection fails
        """
        try:
            import websockets

            self.logger.info(f"Connecting to WebSocket: {uri}")
            self._websocket = await websockets.connect(uri)
            self._is_connected = True

            # Start listener task
            asyncio.create_task(self._listen())

        except ImportError:
            raise ImportError("websockets library required. Install with: pip install websockets")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if self._is_connected:
            self._is_connected = False
            self._is_streaming = False

            if hasattr(self, "_websocket"):
                await self._websocket.close()

            self.logger.info("Disconnected from WebSocket")

    async def _listen(self) -> None:
        """Listen for incoming messages from the WebSocket."""
        try:
            async for message in self._websocket:
                try:
                    # Parse message
                    if isinstance(message, bytes):
                        await self._handle_audio_data(message)
                    elif isinstance(message, str):
                        await self._handle_text_message(message)
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")

        except Exception as e:
            self.logger.error(f"Error in listener: {e}")
            self._is_connected = False

    async def _handle_audio_data(self, data: bytes) -> None:
        """
        Handle incoming audio data.

        Args:
            data: Raw audio bytes
        """
        # Add to input buffer
        self._input_buffer += data

        # Process chunks when we have enough data
        bytes_per_sample = 4 if self.format == "float32" else 2
        chunk_bytes = self.chunk_size * self.channels * bytes_per_sample

        while len(self._input_buffer) >= chunk_bytes:
            chunk = self._input_buffer[:chunk_bytes]
            self._input_buffer = self._input_buffer[chunk_bytes:]

            # Convert to Audio object
            import numpy as np

            if self.format == "float32":
                audio_array = np.frombuffer(chunk, dtype=np.float32)
            else:
                audio_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

            # Reshape for multi-channel
            if self.channels > 1:
                audio_array = audio_array.reshape(-1, self.channels)

            audio = Audio(audio_array, self.sample_rate)

            # Call callback if registered
            if self.on_audio_received:
                if asyncio.iscoroutinefunction(self.on_audio_received):
                    await self.on_audio_received(audio)
                else:
                    self.on_audio_received(audio)

    async def _handle_text_message(self, message: str) -> None:
        """
        Handle incoming text message.

        Args:
            message: JSON message string
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "transcription":
                if self.on_transcription:
                    if asyncio.iscoroutinefunction(self.on_transcription):
                        await self.on_transcription(data)
                    else:
                        self.on_transcription(data)

            elif msg_type == "synthesis":
                if self.on_synthesis:
                    if asyncio.iscoroutinefunction(self.on_synthesis):
                        await self.on_synthesis(data)
                    else:
                        self.on_synthesis(data)

        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON message: {message}")

    async def send_audio(self, audio: Audio) -> None:
        """
        Send audio data through the WebSocket.

        Args:
            audio: Audio object to send
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to WebSocket")

        # Convert audio to bytes
        import numpy as np

        audio_array = audio.data
        if audio_array.ndim == 1:
            audio_array = audio_array.reshape(-1, 1)

        audio_array = audio_array.flatten()

        if self.format == "float32":
            audio_bytes = audio_array.astype(np.float32).tobytes()
        else:
            audio_bytes = (audio_array * 32767.0).astype(np.int16).tobytes()

        # Send in chunks
        bytes_per_sample = 4 if self.format == "float32" else 2
        chunk_bytes = self.chunk_size * self.channels * bytes_per_sample

        for i in range(0, len(audio_bytes), chunk_bytes):
            chunk = audio_bytes[i:i+chunk_bytes]
            await self._websocket.send(chunk)

            # Small delay to avoid overwhelming the receiver
            await asyncio.sleep(0.001)

    async def send_text(self, data: Dict[str, Any]) -> None:
        """
        Send a text message through the WebSocket.

        Args:
            data: Dictionary to send as JSON
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to WebSocket")

        message = json.dumps(data)
        await self._websocket.send(message)

    async def send_transcription(self, text: str, confidence: float = 1.0) -> None:
        """
        Send a transcription result.

        Args:
            text: Transcribed text
            confidence: Confidence score
        """
        await self.send_text({
            "type": "transcription",
            "text": text,
            "confidence": confidence,
            "timestamp": time.time()
        })

    async def send_synthesis(self, audio: Audio) -> None:
        """
        Send synthesized speech.

        Args:
            audio: Audio to send
        """
        await self.send_audio(audio)

    @property
    def is_connected(self) -> bool:
        """Check if connected to WebSocket."""
        return self._is_connected

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming


class WebSocketVoiceStream(VoiceStream):
    """
    VoiceStream with WebSocket support for remote audio processing.

    This extends VoiceStream to add WebSocket connectivity for real-time
    audio streaming over the network.

    Args:
        ws_uri: WebSocket URI to connect to
        **kwargs: Additional arguments for VoiceStream
    """

    def __init__(self, ws_uri: Optional[str] = None, **kwargs):
        """
        Initialize the WebSocket voice stream.

        Args:
            ws_uri: WebSocket URI to connect to
            **kwargs: Additional arguments for VoiceStream
        """
        super().__init__(**kwargs)

        self.ws_uri = ws_uri
        self._ws_client: Optional[AudioWebSocket] = None

    async def connect_websocket(self, uri: Optional[str] = None) -> None:
        """
        Connect to a WebSocket server.

        Args:
            uri: WebSocket URI (uses self.ws_uri if not provided)
        """
        uri = uri or self.ws_uri
        if not uri:
            raise ValueError("No WebSocket URI provided")

        self._ws_client = AudioWebSocket(
            sample_rate=self.sample_rate,
            channels=self.channels
        )

        # Set up callbacks
        self._ws_client.on_audio_received = self._on_ws_audio

        await self._ws_client.connect(uri)

    async def disconnect_websocket(self) -> None:
        """Disconnect from the WebSocket server."""
        if self._ws_client:
            await self._ws_client.disconnect()
            self._ws_client = None

    async def _on_ws_audio(self, audio: Audio) -> None:
        """
        Handle audio received from WebSocket.

        Args:
            audio: Received audio
        """
        # Process through voice stream
        self.process_audio(audio)

    async def stream_to_websocket(
        self,
        audio_generator: AsyncIterator[Audio]
    ) -> None:
        """
        Stream audio to a WebSocket connection.

        Args:
            audio_generator: Async generator of Audio objects
        """
        if not self._ws_client:
            raise ConnectionError("Not connected to WebSocket")

        async for audio in audio_generator:
            await self._ws_client.send_audio(audio)


async def create_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    on_client_connect: Optional[Callable] = None,
    on_audio_receive: Optional[Callable] = None
) -> None:
    """
    Create a WebSocket server for audio streaming.

    Args:
        host: Host to bind to
        port: Port to bind to
        on_client_connect: Callback when a client connects
        on_audio_receive: Callback when audio is received

    Raises:
        ImportError: If websockets library is not installed
    """
    try:
        import websockets
    except ImportError:
        raise ImportError("websockets library required. Install with: pip install websockets")

    logger = get_logger(__name__)

    async def handler(websocket, path):
        """Handle WebSocket connection."""
        logger.info(f"Client connected from {websocket.remote_address}")

        # Call connect callback if provided
        if on_client_connect:
            if asyncio.iscoroutinefunction(on_client_connect):
                await on_client_connect(websocket)
            else:
                on_client_connect(websocket)

        try:
            async for message in websocket:
                # Handle audio data (bytes) or control messages (text)
                if isinstance(message, bytes):
                    if on_audio_receive:
                        if asyncio.iscoroutinefunction(on_audio_receive):
                            await on_audio_receive(websocket, message)
                        else:
                            on_audio_receive(websocket, message)

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            logger.info(f"Client disconnected")

    logger.info(f"Starting WebSocket server on {host}:{port}")

    async with websockets.serve(handler, host, port):
        # Keep server running
        await asyncio.Future()  # Run forever
