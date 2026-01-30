"""
fmus_vox.stream.voice_stream - Real-time voice streaming functionality.

This module provides classes for continuous audio streaming and processing,
with support for speech detection, VAD, and real-time transcription.
"""

import threading
import time
import queue
from typing import Callable, Dict, Any, List, Optional, Union, Tuple

import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import StreamError
from .microphone import Microphone


class StreamBuffer:
    """
    Audio buffer for streaming applications.

    This class manages a ring buffer for audio data, providing methods
    to add, retrieve, and manipulate audio frames for streaming processing.
    """

    def __init__(
        self,
        max_duration: float = 10.0,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: np.dtype = np.float32
    ):
        """
        Initialize an audio buffer for streaming.

        Args:
            max_duration: Maximum buffer duration in seconds.
            sample_rate: Sample rate of the audio.
            channels: Number of audio channels.
            dtype: Data type for the buffer.
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_duration = max_duration
        self.dtype = dtype

        # Calculate buffer size in samples
        self.max_samples = int(max_duration * sample_rate * channels)
        self.buffer = np.zeros(self.max_samples, dtype=dtype)

        self.write_pos = 0
        self.total_samples = 0
        self.lock = threading.RLock()

    def write(self, data: Union[np.ndarray, bytes]) -> int:
        """
        Write audio data to the buffer.

        Args:
            data: Audio data to write, as numpy array or bytes.

        Returns:
            Number of samples written.
        """
        # Convert bytes to numpy array if needed
        if isinstance(data, bytes):
            if self.dtype == np.float32:
                data = np.frombuffer(data, dtype=np.float32)
            elif self.dtype == np.int16:
                data = np.frombuffer(data, dtype=np.int16)
            else:
                raise ValueError(f"Unsupported data type for bytes conversion: {self.dtype}")

        # Ensure data is the right dtype
        if data.dtype != self.dtype:
            data = data.astype(self.dtype)

        with self.lock:
            # Determine how many samples to write
            n_samples = min(len(data), self.max_samples)

            # Handle wrap-around if needed
            first_chunk = min(n_samples, self.max_samples - self.write_pos)
            self.buffer[self.write_pos:self.write_pos + first_chunk] = data[:first_chunk]

            # If we need to wrap around
            if first_chunk < n_samples:
                second_chunk = n_samples - first_chunk
                self.buffer[:second_chunk] = data[first_chunk:n_samples]
                self.write_pos = second_chunk
            else:
                self.write_pos = (self.write_pos + first_chunk) % self.max_samples

            self.total_samples += n_samples

        return n_samples

    def read(self, duration: float = None, n_samples: int = None) -> np.ndarray:
        """
        Read audio data from the buffer.

        Args:
            duration: Duration to read in seconds.
            n_samples: Number of samples to read (overrides duration if provided).

        Returns:
            Numpy array containing the requested audio data.
        """
        with self.lock:
            # Calculate how many samples to read
            if n_samples is None:
                if duration is None:
                    # Default to entire buffer
                    n_samples = min(self.total_samples, self.max_samples)
                else:
                    n_samples = int(duration * self.sample_rate * self.channels)

            # Limit to available samples
            n_samples = min(n_samples, min(self.total_samples, self.max_samples))

            if n_samples == 0:
                return np.array([], dtype=self.dtype)

            # Calculate read position
            read_pos = (self.write_pos - n_samples) % self.max_samples

            # Handle wrap-around if needed
            if read_pos < self.write_pos:
                # No wrap-around needed
                return self.buffer[read_pos:self.write_pos].copy()
            else:
                # Need to wrap around
                first_part = self.buffer[read_pos:].copy()
                second_part = self.buffer[:self.write_pos].copy()
                return np.concatenate([first_part, second_part])

    def read_latest(self, duration: float) -> np.ndarray:
        """
        Read the most recent audio data from the buffer.

        Args:
            duration: Duration to read in seconds.

        Returns:
            Numpy array containing the most recent audio data.
        """
        n_samples = int(duration * self.sample_rate * self.channels)
        return self.read(n_samples=n_samples)

    def clear(self) -> None:
        """Clear the buffer."""
        with self.lock:
            self.buffer.fill(0)
            self.write_pos = 0
            self.total_samples = 0

    def to_audio(self, duration: float = None) -> Audio:
        """
        Convert buffer contents to an Audio object.

        Args:
            duration: Duration to convert in seconds. If None, uses all available data.

        Returns:
            Audio object containing the buffer data.
        """
        data = self.read(duration=duration)
        return Audio(
            data,
            sample_rate=self.sample_rate,
            channels=self.channels
        )

    def __len__(self) -> int:
        """Return the number of samples currently in the buffer."""
        return min(self.total_samples, self.max_samples)


class VoiceStream:
    """
    Real-time voice processing stream.

    This class provides functionality for continuous voice processing,
    including voice activity detection, speech segmentation, and
    real-time transcription.
    """

    def __init__(
        self,
        input_device: Optional[Union[int, Microphone]] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        buffer_duration: float = 30.0,
        vad_mode: str = "normal",
        min_silence_duration: float = 0.5,
        min_speech_duration: float = 0.3,
        **kwargs
    ):
        """
        Initialize a voice stream for continuous processing.

        Args:
            input_device: Microphone device index or Microphone instance.
                          If None, the default input device is used.
            sample_rate: Sample rate for audio processing.
            channels: Number of audio channels.
            buffer_duration: Maximum duration of audio buffer in seconds.
            vad_mode: Voice activity detection sensitivity ('aggressive',
                      'normal', or 'relaxed').
            min_silence_duration: Minimum silence duration to consider a
                                  speech segment complete.
            min_speech_duration: Minimum speech duration to consider a
                                 speech segment valid.
            **kwargs: Additional parameters for the microphone.
        """
        # Set up microphone input
        if isinstance(input_device, Microphone):
            self.microphone = input_device
        else:
            self.microphone = Microphone(
                device_index=input_device,
                sample_rate=sample_rate,
                channels=channels,
                format="float32",
                **kwargs
            )

        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_duration = buffer_duration

        # Set up buffers
        self.audio_buffer = StreamBuffer(
            max_duration=buffer_duration,
            sample_rate=sample_rate,
            channels=channels
        )

        # VAD parameters
        self.vad_mode = vad_mode
        self.min_silence_duration = min_silence_duration
        self.min_speech_duration = min_speech_duration

        # Speech segmentation state
        self.is_speech_active = False
        self.speech_start_time = 0
        self.last_speech_end_time = 0
        self.silence_start_time = 0

        # State variables
        self._is_running = False
        self._stop_event = threading.Event()
        self._processing_thread = None

        # Callbacks
        self.callbacks = {
            "on_audio": [],
            "on_speech_start": [],
            "on_speech_end": [],
            "on_speech": [],
            "on_vad": [],
        }

        # Try to import VAD
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad()
            self._set_vad_aggressiveness()
        except ImportError:
            self.vad = None

    def _set_vad_aggressiveness(self) -> None:
        """Set the VAD aggressiveness based on the mode setting."""
        if self.vad is None:
            return

        # Convert string mode to numeric level
        if self.vad_mode == "aggressive":
            level = 3
        elif self.vad_mode == "normal":
            level = 2
        elif self.vad_mode == "relaxed":
            level = 1
        else:
            level = 2  # Default to normal

        self.vad.set_mode(level)

    def on_audio(self, callback: Callable[[np.ndarray, Dict[str, Any]], None]) -> None:
        """
        Register a callback for raw audio data.

        Args:
            callback: Function that takes (audio_data, metadata) parameters.
        """
        self.callbacks["on_audio"].append(callback)

    def on_speech_start(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for when speech begins.

        Args:
            callback: Function that takes a metadata dictionary.
        """
        self.callbacks["on_speech_start"].append(callback)

    def on_speech_end(self, callback: Callable[[Audio, Dict[str, Any]], None]) -> None:
        """
        Register a callback for when speech ends.

        Args:
            callback: Function that takes (audio, metadata) parameters.
        """
        self.callbacks["on_speech_end"].append(callback)

    def on_speech(self, callback: Callable[[Audio, Dict[str, Any]], None]) -> None:
        """
        Register a callback for complete speech segments.

        Equivalent to on_speech_end but with a more intuitive name.

        Args:
            callback: Function that takes (audio, metadata) parameters.
        """
        self.callbacks["on_speech_end"].append(callback)

    def on_vad(self, callback: Callable[[bool, Dict[str, Any]], None]) -> None:
        """
        Register a callback for voice activity detection events.

        Args:
            callback: Function that takes (is_speech, metadata) parameters.
        """
        self.callbacks["on_vad"].append(callback)

    def _run_callbacks(self, event_type: str, *args) -> None:
        """
        Run all registered callbacks for an event type.

        Args:
            event_type: The type of event ('on_audio', 'on_speech_start', etc.)
            *args: Arguments to pass to the callbacks.
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(*args)
                except Exception as e:
                    # Log but don't crash
                    print(f"Error in {event_type} callback: {str(e)}")

    def start(self) -> None:
        """Start the voice stream processing."""
        if self._is_running:
            return

        # Clear state
        self._stop_event.clear()
        self._is_running = True
        self.audio_buffer.clear()

        # Reset speech detection state
        self.is_speech_active = False
        self.speech_start_time = 0
        self.last_speech_end_time = 0
        self.silence_start_time = 0

        # Start the microphone
        self.microphone.open()
        self.microphone.start_recording()

        # Start processing thread
        self._processing_thread = threading.Thread(target=self._process_stream)
        self._processing_thread.daemon = True
        self._processing_thread.start()

    def stop(self) -> None:
        """Stop the voice stream processing."""
        if not self._is_running:
            return

        self._is_running = False
        self._stop_event.set()

        # Stop the microphone
        try:
            self.microphone.stop_recording()
            self.microphone.close()
        except:
            pass

        # Wait for processing thread to end
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)

        self._processing_thread = None

    def _process_stream(self) -> None:
        """Main processing loop for the voice stream."""
        chunk_duration = 0.03  # 30ms chunks for VAD
        chunk_samples = int(chunk_duration * self.sample_rate)
        processing_interval = 0.01  # 10ms processing interval

        # Check if we have VAD
        has_vad = self.vad is not None

        # Processing loop
        while self._is_running and not self._stop_event.is_set():
            start_time = time.time()

            # Read a chunk of audio
            if self.channels == 1:
                audio_chunk = self.microphone.read(chunk_samples)
            else:
                # If stereo, we need to convert to mono for VAD
                stereo_chunk = self.microphone.read(chunk_samples)
                mono_samples = np.frombuffer(stereo_chunk, dtype=np.float32)
                mono_samples = mono_samples.reshape(-1, self.channels).mean(axis=1)
                audio_chunk = mono_samples.tobytes()

            # Add to buffer
            self.audio_buffer.write(audio_chunk)

            # Run audio callbacks
            audio_data = np.frombuffer(audio_chunk, dtype=np.float32)
            metadata = {
                "timestamp": time.time(),
                "sample_rate": self.sample_rate,
                "channels": self.channels,
            }
            self._run_callbacks("on_audio", audio_data, metadata)

            # Voice activity detection
            is_speech = False
            if has_vad:
                try:
                    # WebRTC VAD requires 16-bit PCM
                    pcm_data = np.frombuffer(audio_chunk, dtype=np.float32)
                    pcm_data = (pcm_data * 32767).astype(np.int16).tobytes()
                    is_speech = self.vad.is_speech(pcm_data, self.sample_rate)
                except Exception as e:
                    # VAD can fail if the chunk is not exactly the right size
                    print(f"VAD error: {str(e)}")

            # Run VAD callbacks
            vad_metadata = {
                "timestamp": time.time(),
                "sample_rate": self.sample_rate,
            }
            self._run_callbacks("on_vad", is_speech, vad_metadata)

            # Speech segmentation logic
            now = time.time()

            if is_speech:
                if not self.is_speech_active:
                    # Start of speech
                    self.is_speech_active = True
                    self.speech_start_time = now

                    # Run speech start callbacks
                    speech_start_metadata = {
                        "timestamp": now,
                    }
                    self._run_callbacks("on_speech_start", speech_start_metadata)

                # Reset silence counter
                self.silence_start_time = 0
            else:
                # Not speech
                if self.is_speech_active:
                    # In speech mode but got silence
                    if self.silence_start_time == 0:
                        # Start of silence
                        self.silence_start_time = now
                    elif now - self.silence_start_time >= self.min_silence_duration:
                        # Silence duration exceeded threshold, end speech segment
                        speech_duration = now - self.speech_start_time - (now - self.silence_start_time)

                        if speech_duration >= self.min_speech_duration:
                            # Valid speech segment
                            # Get the speech audio from buffer
                            speech_audio = self.audio_buffer.to_audio(
                                duration=speech_duration + self.min_silence_duration
                            )

                            # Run speech end callbacks
                            speech_end_metadata = {
                                "start_time": self.speech_start_time,
                                "end_time": now,
                                "duration": speech_duration,
                            }
                            self._run_callbacks("on_speech_end", speech_audio, speech_end_metadata)

                        # Reset speech detection state
                        self.is_speech_active = False
                        self.speech_start_time = 0
                        self.last_speech_end_time = now
                        self.silence_start_time = 0

            # Sleep to maintain processing interval
            elapsed = time.time() - start_time
            if elapsed < processing_interval:
                time.sleep(processing_interval - elapsed)

    def __enter__(self):
        """Start the stream when used as a context manager."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the stream when exiting context manager."""
        self.stop()

    def __del__(self):
        """Clean up resources when garbage collected."""
        self.stop()
