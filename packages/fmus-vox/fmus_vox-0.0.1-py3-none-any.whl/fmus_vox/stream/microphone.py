"""
fmus_vox.stream.microphone - Enhanced microphone audio streaming implementation.

This module provides comprehensive functionality for capturing audio from microphone devices,
with support for device selection, audio visualization, and real-time processing.
"""

import queue
import threading
import time
import collections
from typing import Optional, Union, Callable, Dict, Any, List, Tuple, Deque

import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import DeviceError, DependencyError

try:
    import pyaudio
except ImportError:
    pyaudio = None


class AudioFilter:
    """
    Base class for real-time audio filters.

    Subclasses should implement the process method to perform
    audio processing on incoming audio data.
    """

    def __init__(self, name: str = "AudioFilter"):
        """
        Initialize an audio filter.

        Args:
            name: Name of the filter for identification
        """
        self.name = name
        self.enabled = True

    def process(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio data.

        Args:
            data: Audio data as numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Processed audio data
        """
        # Base implementation just returns the data unchanged
        return data

    def enable(self):
        """Enable the filter."""
        self.enabled = True

    def disable(self):
        """Disable the filter."""
        self.enabled = False


class NoiseReduction(AudioFilter):
    """
    Noise reduction filter.

    Reduces background noise in audio recordings.
    """

    def __init__(self, strength: float = 0.5):
        """
        Initialize noise reduction filter.

        Args:
            strength: Noise reduction strength (0.0 to 1.0)
        """
        super().__init__("NoiseReduction")
        self.strength = max(0.0, min(1.0, strength))
        self._noise_profile = None
        self._initialized = False

    def calibrate(self, noise_sample: np.ndarray):
        """
        Calibrate the noise profile from a sample of background noise.

        Args:
            noise_sample: Audio sample containing only background noise
        """
        try:
            import noisereduce as nr
            self._noise_profile = noise_sample
            self._initialized = True
        except ImportError:
            raise DependencyError(
                "noisereduce package is required for noise reduction. "
                "Install with: pip install noisereduce"
            )

    def process(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise reduction to the audio data."""
        if not self.enabled:
            return data

        try:
            import noisereduce as nr

            # If we haven't been calibrated, use the first part of the
            # audio as the noise profile
            if not self._initialized:
                noise_len = min(int(len(data) * 0.1), sample_rate // 4)  # Use first 100ms or 250ms as noise
                self._noise_profile = data[:noise_len]
                self._initialized = True

            # Apply noise reduction
            return nr.reduce_noise(
                y=data,
                sr=sample_rate,
                y_noise=self._noise_profile,
                prop_decrease=self.strength
            )
        except ImportError:
            # Return unprocessed data if noisereduce isn't available
            return data


class Normalization(AudioFilter):
    """
    Audio normalization filter.

    Normalizes audio volume to a target level.
    """

    def __init__(self, target_db: float = -3.0):
        """
        Initialize normalization filter.

        Args:
            target_db: Target dB level to normalize to
        """
        super().__init__("Normalization")
        self.target_db = target_db

    def process(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Normalize audio volume."""
        if not self.enabled or len(data) == 0:
            return data

        # Calculate current dB level
        eps = np.finfo(float).eps  # To avoid log(0)
        current_db = 20 * np.log10(np.max(np.abs(data)) + eps)

        # Calculate gain
        gain = 10 ** ((self.target_db - current_db) / 20)

        # Apply gain
        return data * gain


class AudioLevelMeter:
    """
    Audio level meter for real-time visualization.

    Provides RMS and peak level measurements for audio visualization.
    """

    def __init__(self, window_size: int = 10):
        """
        Initialize audio level meter.

        Args:
            window_size: Size of the averaging window in frames
        """
        self.window_size = window_size
        self.rms_values: Deque[float] = collections.deque(maxlen=window_size)
        self.peak_values: Deque[float] = collections.deque(maxlen=window_size)

    def process(self, data: np.ndarray) -> Dict[str, float]:
        """
        Process audio data and calculate levels.

        Args:
            data: Audio data as numpy array

        Returns:
            Dictionary with rms and peak levels
        """
        if len(data) == 0:
            return {"rms": 0.0, "peak": 0.0, "avg_rms": 0.0, "avg_peak": 0.0}

        # Calculate RMS level
        rms = np.sqrt(np.mean(np.square(data)))

        # Calculate peak level
        peak = np.max(np.abs(data))

        # Add to history
        self.rms_values.append(rms)
        self.peak_values.append(peak)

        # Calculate averages
        avg_rms = sum(self.rms_values) / len(self.rms_values)
        avg_peak = sum(self.peak_values) / len(self.peak_values)

        return {
            "rms": rms,
            "peak": peak,
            "avg_rms": avg_rms,
            "avg_peak": avg_peak
        }


class Microphone:
    """
    Enhanced class for recording audio from a microphone device.

    This class provides both blocking and streaming interfaces for
    capturing audio from microphone input devices, with support for
    device selection, audio visualization, and real-time processing.
    """

    # Map of common formats to PyAudio format constants
    FORMAT_MAP = {
        "float32": None,  # Will be set if pyaudio is imported
        "int32": None,
        "int24": None,
        "int16": None,
        "int8": None,
        "uint8": None,
    }

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        format: str = "float32",
        chunk_size: int = 1024,
        **kwargs
    ):
        """
        Initialize a microphone input stream.

        Args:
            device_index: Index of the input device to use. None for default.
            sample_rate: Sample rate to record at.
            channels: Number of audio channels to record.
            format: Audio format ('float32', 'int16', etc.)
            chunk_size: Size of audio chunks to process at once.
            **kwargs: Additional parameters for PyAudio.
        """
        if pyaudio is None:
            raise DependencyError(
                "PyAudio is not installed. Install with: pip install pyaudio"
            )

        # Initialize format map with actual pyaudio constants
        if not Microphone.FORMAT_MAP["float32"]:
            Microphone.FORMAT_MAP = {
                "float32": pyaudio.paFloat32,
                "int32": pyaudio.paInt32,
                "int24": pyaudio.paInt24,
                "int16": pyaudio.paInt16,
                "int8": pyaudio.paInt8,
                "uint8": pyaudio.paUInt8,
            }

        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.chunk_size = chunk_size
        self.kwargs = kwargs

        self._pyaudio_instance = None
        self._stream = None
        self._audio_buffer = queue.Queue()
        self._is_recording = False
        self._stop_event = threading.Event()

        # Audio processing
        self._filters: List[AudioFilter] = []
        self._level_meter = AudioLevelMeter()
        self._visualization_callback = None

    def __enter__(self):
        """Start the microphone stream when used as a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the microphone stream when exiting context manager."""
        self.close()

    def open(self):
        """
        Open the microphone stream.

        Raises:
            DeviceError: If the specified device cannot be opened.
        """
        try:
            self._pyaudio_instance = pyaudio.PyAudio()

            # Get pyaudio format from string format
            pa_format = Microphone.FORMAT_MAP.get(self.format.lower())
            if pa_format is None:
                raise ValueError(f"Unsupported audio format: {self.format}")

            self._stream = self._pyaudio_instance.open(
                input=True,
                output=False,
                start=True,
                frames_per_buffer=self.chunk_size,
                rate=self.sample_rate,
                channels=self.channels,
                format=pa_format,
                input_device_index=self.device_index,
                stream_callback=self._audio_callback,
                **self.kwargs
            )

        except Exception as e:
            if self._pyaudio_instance:
                self._pyaudio_instance.terminate()
                self._pyaudio_instance = None
            raise DeviceError(f"Failed to open microphone: {str(e)}")

        return self

    def close(self):
        """Close the microphone stream and release resources."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._pyaudio_instance:
            self._pyaudio_instance.terminate()
            self._pyaudio_instance = None

        # Clear the buffer
        while not self._audio_buffer.empty():
            try:
                self._audio_buffer.get_nowait()
            except queue.Empty:
                break

        self._is_recording = False
        self._stop_event.set()

    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert raw audio bytes to numpy array.

        Args:
            audio_bytes: Raw audio data as bytes

        Returns:
            Audio data as numpy array
        """
        if self.format == "float32":
            return np.frombuffer(audio_bytes, dtype=np.float32)
        elif self.format == "int32":
            return np.frombuffer(audio_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif self.format == "int24":
            # For int24, we need to convert it to int32 first
            # This is a bit more complex, we'll use a simplified approach
            return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif self.format == "int16":
            return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif self.format == "int8":
            return np.frombuffer(audio_bytes, dtype=np.int8).astype(np.float32) / 128.0
        elif self.format == "uint8":
            return (np.frombuffer(audio_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _numpy_to_bytes(self, audio_array: np.ndarray) -> bytes:
        """
        Convert numpy array to raw audio bytes.

        Args:
            audio_array: Audio data as numpy array

        Returns:
            Raw audio data as bytes
        """
        if self.format == "float32":
            return audio_array.astype(np.float32).tobytes()
        elif self.format == "int32":
            return (audio_array * 2147483648.0).astype(np.int32).tobytes()
        elif self.format == "int24":
            # int24 is tricky, we'll use int16 as approximation
            # (this would need proper implementation in production)
            return (audio_array * 32768.0).astype(np.int16).tobytes()
        elif self.format == "int16":
            return (audio_array * 32768.0).astype(np.int16).tobytes()
        elif self.format == "int8":
            return (audio_array * 128.0).astype(np.int8).tobytes()
        elif self.format == "uint8":
            return ((audio_array * 128.0) + 128.0).astype(np.uint8).tobytes()
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio to handle incoming audio data."""
        if self._is_recording:
            # Process the audio data if we have filters
            if self._filters:
                # Convert bytes to numpy array
                audio_data = self._bytes_to_numpy(in_data)

                # Apply each filter in sequence
                for filter in self._filters:
                    if filter.enabled:
                        audio_data = filter.process(audio_data, self.sample_rate)

                # Convert back to bytes
                processed_data = self._numpy_to_bytes(audio_data)
                self._audio_buffer.put(processed_data)

                # Compute levels and call visualization callback if set
                if self._visualization_callback:
                    levels = self._level_meter.process(audio_data)
                    self._visualization_callback(levels)
            else:
                # No processing needed
                self._audio_buffer.put(in_data)

                # Still compute levels if we have a visualization callback
                if self._visualization_callback:
                    audio_data = self._bytes_to_numpy(in_data)
                    levels = self._level_meter.process(audio_data)
                    self._visualization_callback(levels)

        return (None, pyaudio.paContinue)

    def add_filter(self, filter: AudioFilter) -> "Microphone":
        """
        Add an audio processing filter.

        Args:
            filter: The audio filter to add

        Returns:
            Self for method chaining
        """
        self._filters.append(filter)
        return self

    def remove_filter(self, filter_name: str) -> bool:
        """
        Remove an audio processing filter by name.

        Args:
            filter_name: Name of the filter to remove

        Returns:
            True if filter was removed, False if not found
        """
        for i, filter in enumerate(self._filters):
            if filter.name == filter_name:
                self._filters.pop(i)
                return True
        return False

    def set_visualization_callback(
        self, callback: Callable[[Dict[str, float]], None]
    ) -> "Microphone":
        """
        Set a callback for audio level visualization.

        The callback will be called with a dictionary containing:
        - rms: Root mean square level (0.0 to 1.0)
        - peak: Peak level (0.0 to 1.0)
        - avg_rms: Average RMS over window
        - avg_peak: Average peak over window

        Args:
            callback: Function to call with audio level data

        Returns:
            Self for method chaining
        """
        self._visualization_callback = callback
        return self

    def read(self, num_frames: Optional[int] = None) -> bytes:
        """
        Read audio data from the microphone.

        Args:
            num_frames: Number of frames to read. If None, reads one chunk.

        Returns:
            Raw audio data as bytes.
        """
        if not self._stream:
            self.open()

        chunk_size = num_frames if num_frames is not None else self.chunk_size

        # Calculate how many chunks we need to read
        num_chunks = (chunk_size + self.chunk_size - 1) // self.chunk_size

        # Read the specified number of chunks
        chunks = []
        for _ in range(num_chunks):
            try:
                chunk = self._audio_buffer.get(timeout=1.0)
                chunks.append(chunk)
            except queue.Empty:
                break

        # Concatenate all chunks
        data = b''.join(chunks)

        # If we need to truncate the data to match num_frames exactly
        if num_frames is not None:
            bytes_per_sample = 4 if self.format == "float32" else 2  # Assuming int16 otherwise
            bytes_per_frame = bytes_per_sample * self.channels
            data = data[:num_frames * bytes_per_frame]

        return data

    def start_recording(self):
        """Start recording audio to internal buffer."""
        if not self._stream:
            self.open()
        self._is_recording = True
        self._stop_event.clear()

    def stop_recording(self) -> Audio:
        """
        Stop recording and return the recorded audio.

        Returns:
            Audio object containing the recorded audio
        """
        self._is_recording = False

        # Wait for any remaining data to be processed
        time.sleep(0.1)

        # Get all data from the buffer
        chunks = []
        while not self._audio_buffer.empty():
            try:
                chunk = self._audio_buffer.get_nowait()
                chunks.append(chunk)
            except queue.Empty:
                break

        # Concatenate all chunks
        data = b''.join(chunks)

        # Convert to numpy array
        audio_data = self._bytes_to_numpy(data)

        # Create Audio object
        return Audio(audio_data, self.sample_rate)

    def record_until_silence(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.0,
        max_seconds: Optional[float] = None,
        pre_buffer_seconds: float = 0.5
    ) -> Audio:
        """
        Record until silence is detected.

        Args:
            silence_threshold: Threshold for silence detection (0.0 to 1.0)
            silence_duration: Duration of silence to stop recording (seconds)
            max_seconds: Maximum recording duration (seconds)
            pre_buffer_seconds: Seconds of audio to include before speech starts

        Returns:
            Audio object containing the recorded audio
        """
        if not self._stream:
            self.open()

        # Clear the buffer
        while not self._audio_buffer.empty():
            try:
                self._audio_buffer.get_nowait()
            except queue.Empty:
                break

        # Start recording
        self._is_recording = True
        self._stop_event.clear()

        # Pre-buffer for catching the start of speech
        pre_buffer = []
        pre_buffer_size = int(pre_buffer_seconds * self.sample_rate / self.chunk_size)

        # Recording loop
        chunks = []
        silence_count = 0
        max_count = None if max_seconds is None else int(max_seconds * self.sample_rate / self.chunk_size)
        speech_detected = False

        try:
            while True:
                # Check if we've reached the maximum duration
                if max_count is not None and len(chunks) >= max_count:
                    break

                # Get audio chunk
                try:
                    chunk = self._audio_buffer.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Convert to numpy for level detection
                chunk_data = self._bytes_to_numpy(chunk)

                # Calculate audio level
                level = np.max(np.abs(chunk_data))

                # Check if this is speech
                is_speech = level > silence_threshold

                if not speech_detected:
                    # We're still waiting for speech to start
                    if is_speech:
                        # Speech has started, add pre-buffer to chunks
                        speech_detected = True
                        chunks.extend(pre_buffer)
                        chunks.append(chunk)
                        silence_count = 0
                    else:
                        # Still silence, update pre-buffer (circular buffer)
                        pre_buffer.append(chunk)
                        if len(pre_buffer) > pre_buffer_size:
                            pre_buffer.pop(0)
                else:
                    # We're recording speech
                    chunks.append(chunk)

                    if is_speech:
                        # Reset silence counter
                        silence_count = 0
                    else:
                        # Increment silence counter
                        silence_count += 1

                        # Check if we've reached the silence duration
                        silence_frames = int(silence_duration * self.sample_rate / self.chunk_size)
                        if silence_count >= silence_frames:
                            break

                # Check for stop event
                if self._stop_event.is_set():
                    break
        finally:
            # Stop recording
            self._is_recording = False

        # If we never detected speech, return empty audio
        if not speech_detected:
            return Audio(np.array([], dtype=np.float32), self.sample_rate)

        # Concatenate all chunks
        data = b''.join(chunks)

        # Convert to numpy array
        audio_data = self._bytes_to_numpy(data)

        # Create Audio object
        return Audio(audio_data, self.sample_rate)

    def record(self, seconds: float, visualization_callback: Optional[Callable] = None) -> Audio:
        """
        Record audio for a specified duration.

        Args:
            seconds: Duration to record in seconds
            visualization_callback: Optional callback for visualization during recording

        Returns:
            Audio object containing the recorded audio
        """
        if not self._stream:
            self.open()

        # Set visualization callback if provided
        old_callback = self._visualization_callback
        if visualization_callback:
            self._visualization_callback = visualization_callback

        # Clear the buffer
        while not self._audio_buffer.empty():
            try:
                self._audio_buffer.get_nowait()
            except queue.Empty:
                break

        # Start recording
        self._is_recording = True
        self._stop_event.clear()

        # Calculate number of frames to record
        num_frames = int(seconds * self.sample_rate)
        bytes_per_sample = 4 if self.format == "float32" else 2  # Assuming int16 otherwise
        bytes_per_frame = bytes_per_sample * self.channels
        total_bytes = num_frames * bytes_per_frame

        # Recording loop
        chunks = []
        bytes_recorded = 0

        try:
            while bytes_recorded < total_bytes:
                # Check for stop event
                if self._stop_event.is_set():
                    break

                # Get audio chunk
                try:
                    chunk = self._audio_buffer.get(timeout=0.1)
                    chunks.append(chunk)
                    bytes_recorded += len(chunk)
                except queue.Empty:
                    continue

            # Wait a little bit to make sure we get all data
            time.sleep(0.1)

            # Get any remaining data
            while not self._audio_buffer.empty() and bytes_recorded < total_bytes:
                try:
                    chunk = self._audio_buffer.get_nowait()
                    chunks.append(chunk)
                    bytes_recorded += len(chunk)
                except queue.Empty:
                    break
        finally:
            # Stop recording
            self._is_recording = False

            # Restore original visualization callback
            self._visualization_callback = old_callback

        # Concatenate all chunks
        data = b''.join(chunks)

        # Trim to exact length
        data = data[:total_bytes]

        # Convert to numpy array
        audio_data = self._bytes_to_numpy(data)

        # Create Audio object
        return Audio(audio_data, self.sample_rate)

    @staticmethod
    def list_devices() -> List[Dict[str, Any]]:
        """
        List available audio input devices.

        Returns:
            List of dictionaries containing device information
        """
        if pyaudio is None:
            raise DependencyError(
                "PyAudio is not installed. Install with: pip install pyaudio"
            )

        p = pyaudio.PyAudio()

        devices = []

        try:
            # Get device count
            device_count = p.get_device_count()

            # Iterate over all devices
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)

                # Only include input devices
                if device_info.get('maxInputChannels', 0) > 0:
                    devices.append({
                        'index': device_info.get('index', i),
                        'name': device_info.get('name', f"Device {i}"),
                        'channels': device_info.get('maxInputChannels', 0),
                        'sample_rates': [
                            int(r) for r in device_info.get('supportedSampleRates', [44100, 48000])
                        ],
                        'default': device_info.get('isDefaultInputDevice', False)
                    })
        finally:
            p.terminate()

        return devices

    @staticmethod
    def get_default_device() -> Optional[Dict[str, Any]]:
        """
        Get the default audio input device.

        Returns:
            Default device information or None if not found
        """
        devices = Microphone.list_devices()

        # Find default device
        for device in devices:
            if device.get('default', False):
                return device

        # If no default device is marked, return the first one
        if devices:
            return devices[0]

        return None

    def calibrate_noise_profile(self, seconds: float = 2.0) -> None:
        """
        Calibrate noise reduction filter with ambient noise.

        Records ambient noise to calibrate the noise reduction filter.

        Args:
            seconds: Duration to record ambient noise in seconds
        """
        # Find noise reduction filter
        noise_filter = None
        for filter in self._filters:
            if isinstance(filter, NoiseReduction):
                noise_filter = filter
                break

        # If no noise reduction filter exists, create one
        if noise_filter is None:
            noise_filter = NoiseReduction()
            self.add_filter(noise_filter)

        # Record ambient noise
        print("Recording ambient noise for calibration...")

        # Temporarily disable all filters
        enabled_filters = []
        for filter in self._filters:
            if filter.enabled:
                enabled_filters.append(filter)
                filter.enabled = False

        # Record ambient noise
        noise_audio = self.record(seconds)

        # Re-enable filters
        for filter in enabled_filters:
            filter.enabled = True

        # Calibrate noise filter
        noise_filter.calibrate(noise_audio.data)
        print("Noise profile calibrated.")

    def create_vad_detector(self, threshold: float = 0.02, window_size: int = 10) -> None:
        """
        Create a Voice Activity Detector filter.

        Args:
            threshold: Threshold for voice detection (0.0 to 1.0)
            window_size: Window size for smoothing in frames
        """
        class VAD(AudioFilter):
            def __init__(self, threshold: float, window_size: int):
                super().__init__("VAD")
                self.threshold = threshold
                self.window_size = window_size
                self.energy_history = collections.deque(maxlen=window_size)
                self.speech_detected = False
                self.callback = None

            def set_callback(self, callback: Callable[[bool], None]):
                self.callback = callback

            def process(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
                # Calculate energy
                energy = np.mean(np.square(data))
                self.energy_history.append(energy)

                # Calculate average energy
                avg_energy = sum(self.energy_history) / len(self.energy_history)

                # Detect speech
                is_speech = avg_energy > self.threshold

                # Call callback if state changed
                if is_speech != self.speech_detected and self.callback:
                    self.callback(is_speech)

                self.speech_detected = is_speech

                # Return data unchanged
                return data

        # Create VAD filter
        vad = VAD(threshold, window_size)
        self.add_filter(vad)

        return vad


# Convenient alias
Mic = Microphone
