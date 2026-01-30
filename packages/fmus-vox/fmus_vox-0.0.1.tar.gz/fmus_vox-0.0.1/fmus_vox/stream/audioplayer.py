"""
fmus_vox.stream.audioplayer - Audio playback functionality.

This module provides classes for audio playback with support for file playback,
streaming playback, and real-time audio output processing.
"""

import threading
import time
import queue
from typing import Optional, Union, Callable, Dict, Any, List, Tuple

import numpy as np

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import DeviceError, DependencyError

try:
    import pyaudio
except ImportError:
    pyaudio = None


class AudioEffect:
    """
    Base class for real-time audio output effects.

    Subclasses should implement the process method to perform
    audio processing on outgoing audio data.
    """

    def __init__(self, name: str = "AudioEffect"):
        """
        Initialize an audio effect.

        Args:
            name: Name of the effect for identification
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
        """Enable the effect."""
        self.enabled = True

    def disable(self):
        """Disable the effect."""
        self.enabled = False


class Equalizer(AudioEffect):
    """
    Simple equalizer effect for audio playback.

    Applies gain adjustments to different frequency bands.
    """

    def __init__(self, bands: Dict[str, float] = None):
        """
        Initialize equalizer with frequency band gains.

        Args:
            bands: Dictionary of frequency bands and their gains (in dB)
                  Default bands: "low", "mid", "high"
        """
        super().__init__("Equalizer")

        # Default bands if none provided
        if bands is None:
            self.bands = {
                "low": 0.0,   # 20-250 Hz
                "mid": 0.0,   # 250-4000 Hz
                "high": 0.0,  # 4000-20000 Hz
            }
        else:
            self.bands = bands

        # Initialize filters
        self._initialized = False
        self._coeffs = {}

    def set_gain(self, band: str, gain_db: float) -> None:
        """
        Set gain for a specific frequency band.

        Args:
            band: Band name ("low", "mid", "high", or custom band)
            gain_db: Gain in decibels (-12 to +12 recommended)
        """
        if band in self.bands:
            self.bands[band] = gain_db
            self._initialized = False  # Force recalculation of filters
        else:
            raise ValueError(f"Unknown band: {band}. Available bands: {list(self.bands.keys())}")

    def _initialize_filters(self, sample_rate: int) -> None:
        """
        Initialize filter coefficients based on sample rate.

        Implements simple FFT-based filtering.

        Args:
            sample_rate: Audio sample rate
        """
        try:
            from scipy import signal
        except ImportError:
            self._initialized = False
            return

        # Define frequency ranges for bands
        freq_ranges = {
            "low": (20, 250),
            "mid": (250, 4000),
            "high": (4000, 20000),
        }

        # Custom frequency ranges if provided
        for band in self.bands:
            if band not in freq_ranges and "-" in band:
                try:
                    low, high = band.split("-")
                    freq_ranges[band] = (float(low), float(high))
                except (ValueError, TypeError):
                    pass

        # Create filters for each band
        nyquist = sample_rate / 2
        self._coeffs = {}

        for band, (low_freq, high_freq) in freq_ranges.items():
            if band in self.bands:
                # Normalize frequencies to Nyquist
                low_norm = low_freq / nyquist
                high_norm = min(high_freq / nyquist, 0.99)

                # Skip bands outside our frequency range
                if low_norm >= 1.0 or high_norm <= 0:
                    continue

                # Design bandpass filter
                if band == "low":
                    # Lowpass for low band
                    b, a = signal.butter(2, high_norm, btype='lowpass')
                elif band == "high":
                    # Highpass for high band
                    b, a = signal.butter(2, low_norm, btype='highpass')
                else:
                    # Bandpass for other bands
                    b, a = signal.butter(2, [low_norm, high_norm], btype='bandpass')

                self._coeffs[band] = (b, a)

        self._initialized = True

    def process(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply equalization to the audio data."""
        if not self.enabled or len(data) == 0:
            return data

        try:
            from scipy import signal
        except ImportError:
            return data

        # Initialize filters if needed
        if not self._initialized:
            self._initialize_filters(sample_rate)

        if not self._initialized:
            return data

        # Apply each band filter
        result = np.zeros_like(data)

        for band, (b, a) in self._coeffs.items():
            # Filter the band
            filtered = signal.lfilter(b, a, data)

            # Apply gain
            gain_db = self.bands[band]
            gain_linear = 10 ** (gain_db / 20.0)

            # Add to result
            result += filtered * gain_linear

        return result


class AudioPlayer:
    """
    Class for playing audio from files or streams.

    This class provides functionality for audio playback with support for
    real-time effects processing and audio format conversion.
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
        sample_rate: int = 44100,
        channels: int = 2,
        format: str = "float32",
        buffer_size: int = 1024,
        **kwargs
    ):
        """
        Initialize an audio player.

        Args:
            device_index: Index of the output device to use. None for default.
            sample_rate: Sample rate for playback.
            channels: Number of audio channels for playback.
            format: Audio format ('float32', 'int16', etc.)
            buffer_size: Size of audio buffer chunks for playback.
            **kwargs: Additional parameters for PyAudio.
        """
        if pyaudio is None:
            raise DependencyError(
                "PyAudio is not installed. Install with: pip install pyaudio"
            )

        # Initialize format map with actual pyaudio constants
        if not AudioPlayer.FORMAT_MAP["float32"]:
            AudioPlayer.FORMAT_MAP = {
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
        self.buffer_size = buffer_size
        self.kwargs = kwargs

        self._pyaudio_instance = None
        self._stream = None
        self._audio_buffer = queue.Queue()
        self._is_playing = False
        self._stop_event = threading.Event()
        self._play_thread = None
        self._audio_position = 0
        self._audio_data = None
        self._total_frames = 0

        # Audio effects
        self._effects: List[AudioEffect] = []

        # Callbacks
        self._on_complete = None
        self._on_position_change = None

    def __enter__(self):
        """Open the audio stream when used as a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the audio stream when exiting context manager."""
        self.close()

    def open(self):
        """
        Open the audio playback stream.

        Raises:
            DeviceError: If the specified device cannot be opened.
        """
        try:
            self._pyaudio_instance = pyaudio.PyAudio()

            # Get pyaudio format from string format
            pa_format = AudioPlayer.FORMAT_MAP.get(self.format.lower())
            if pa_format is None:
                raise ValueError(f"Unsupported audio format: {self.format}")

            self._stream = self._pyaudio_instance.open(
                output=True,
                input=False,
                start=False,
                format=pa_format,
                channels=self.channels,
                rate=self.sample_rate,
                frames_per_buffer=self.buffer_size,
                output_device_index=self.device_index,
                stream_callback=self._audio_callback,
                **self.kwargs
            )

        except Exception as e:
            if self._pyaudio_instance:
                self._pyaudio_instance.terminate()
                self._pyaudio_instance = None
            raise DeviceError(f"Failed to open audio output device: {str(e)}")

        return self

    def close(self):
        """Close the audio playback stream and release resources."""
        self.stop()

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._pyaudio_instance:
            self._pyaudio_instance.terminate()
            self._pyaudio_instance = None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio to handle outgoing audio data."""
        if not self._is_playing or self._audio_data is None:
            # Return silence if not playing
            return (bytes(frame_count * self.channels * 4), pyaudio.paContinue)

        if self._audio_position >= self._total_frames:
            # End of playback
            self._is_playing = False
            self._stop_event.set()

            # Run on_complete callback in a separate thread to avoid blocking
            if self._on_complete:
                threading.Thread(target=self._on_complete).start()

            return (bytes(frame_count * self.channels * 4), pyaudio.paComplete)

        # Calculate how many frames to read
        frames_to_read = min(frame_count, self._total_frames - self._audio_position)

        # Get audio data for this chunk
        start_idx = self._audio_position * self.channels
        end_idx = start_idx + frames_to_read * self.channels
        audio_chunk = self._audio_data[start_idx:end_idx]

        # Apply effects
        if self._effects:
            for effect in self._effects:
                if effect.enabled:
                    audio_chunk = effect.process(audio_chunk, self.sample_rate)

        # Convert to bytes based on format
        if self.format == "float32":
            output_data = audio_chunk.astype(np.float32).tobytes()
        elif self.format == "int32":
            output_data = (audio_chunk * 2147483648.0).astype(np.int32).tobytes()
        elif self.format == "int24":
            # int24 is tricky, we'll use int16 as approximation
            output_data = (audio_chunk * 32768.0).astype(np.int16).tobytes()
        elif self.format == "int16":
            output_data = (audio_chunk * 32768.0).astype(np.int16).tobytes()
        elif self.format == "int8":
            output_data = (audio_chunk * 128.0).astype(np.int8).tobytes()
        elif self.format == "uint8":
            output_data = ((audio_chunk * 128.0) + 128.0).astype(np.uint8).tobytes()
        else:
            output_data = bytes(frames_to_read * self.channels * 4)

        # If we didn't read enough frames, pad with silence
        if len(audio_chunk) < frame_count * self.channels:
            bytes_per_sample = 4 if self.format == "float32" else 2  # Simplified
            silence_bytes = bytes((frame_count - frames_to_read) * self.channels * bytes_per_sample)
            output_data += silence_bytes

        # Update position
        self._audio_position += frames_to_read

        # Trigger position change callback
        if self._on_position_change:
            position_sec = self._audio_position / self.sample_rate
            duration_sec = self._total_frames / self.sample_rate
            threading.Thread(
                target=self._on_position_change,
                args=(position_sec, duration_sec)
            ).start()

        return (output_data, pyaudio.paContinue)

    def add_effect(self, effect: AudioEffect) -> "AudioPlayer":
        """
        Add an audio processing effect.

        Args:
            effect: The audio effect to add

        Returns:
            Self for method chaining
        """
        self._effects.append(effect)
        return self

    def remove_effect(self, effect_name: str) -> bool:
        """
        Remove an audio processing effect by name.

        Args:
            effect_name: Name of the effect to remove

        Returns:
            True if effect was removed, False if not found
        """
        for i, effect in enumerate(self._effects):
            if effect.name == effect_name:
                self._effects.pop(i)
                return True
        return False

    def on_playback_complete(self, callback: Callable[[], None]) -> "AudioPlayer":
        """
        Set callback for when playback completes.

        Args:
            callback: Function to call when playback finishes

        Returns:
            Self for method chaining
        """
        self._on_complete = callback
        return self

    def on_position_change(self, callback: Callable[[float, float], None]) -> "AudioPlayer":
        """
        Set callback for playback position updates.

        The callback will be called with current position (seconds) and
        total duration (seconds) as arguments.

        Args:
            callback: Function to call with position updates

        Returns:
            Self for method chaining
        """
        self._on_position_change = callback
        return self

    def play(self, audio: Union[Audio, np.ndarray, str]) -> None:
        """
        Play audio from an Audio object, numpy array, or file.

        Args:
            audio: Audio data to play. Can be:
                  - Audio object
                  - Numpy array (float32, -1.0 to 1.0 range)
                  - String path to audio file
        """
        self.stop()

        # Load audio data
        if isinstance(audio, str):
            self._load_audio_file(audio)
        elif isinstance(audio, Audio):
            self._load_audio_object(audio)
        elif isinstance(audio, np.ndarray):
            self._audio_data = audio
            self._total_frames = len(audio) // max(1, self.channels)
        else:
            raise ValueError("Audio must be an Audio object, numpy array, or file path")

        # Reset playback position
        self._audio_position = 0

        # Start playback
        self._start_playback()

    def _load_audio_file(self, file_path: str) -> None:
        """
        Load audio data from a file.

        Args:
            file_path: Path to the audio file
        """
        try:
            import soundfile as sf
        except ImportError:
            raise DependencyError(
                "soundfile is required for file playback. "
                "Install with: pip install soundfile"
            )

        try:
            data, file_sample_rate = sf.read(file_path, dtype='float32')

            # Convert mono to stereo if needed
            if len(data.shape) == 1 and self.channels == 2:
                data = np.column_stack((data, data))

            # Convert stereo to mono if needed
            elif len(data.shape) == 2 and data.shape[1] == 2 and self.channels == 1:
                data = np.mean(data, axis=1)

            # Resample if needed
            if file_sample_rate != self.sample_rate:
                try:
                    from scipy import signal
                    # Calculate resampling ratio
                    ratio = self.sample_rate / file_sample_rate

                    # Determine output length
                    output_len = int(len(data) * ratio)

                    # Resample each channel
                    if len(data.shape) == 1:
                        # Mono
                        data = signal.resample(data, output_len)
                    else:
                        # Stereo or multi-channel
                        resampled = np.zeros((output_len, data.shape[1]), dtype=np.float32)
                        for i in range(data.shape[1]):
                            resampled[:, i] = signal.resample(data[:, i], output_len)
                        data = resampled
                except ImportError:
                    # Simple resampling by interpolation if scipy not available
                    if file_sample_rate > self.sample_rate:
                        # Downsampling
                        step = file_sample_rate / self.sample_rate
                        indices = np.arange(0, len(data), step)
                        if len(data.shape) == 1:
                            data = np.interp(indices, np.arange(len(data)), data)
                        else:
                            resampled = np.zeros((len(indices), data.shape[1]), dtype=np.float32)
                            for i in range(data.shape[1]):
                                resampled[:, i] = np.interp(indices, np.arange(len(data)), data[:, i])
                            data = resampled
                    else:
                        # Upsampling - simple repeat
                        ratio = self.sample_rate / file_sample_rate
                        data = np.repeat(data, int(ratio), axis=0)

            # Flatten for audio buffer if needed
            if len(data.shape) > 1:
                # Interleave channels
                data = data.flatten('F')

            self._audio_data = data
            self._total_frames = len(data) // max(1, self.channels)

        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")

    def _load_audio_object(self, audio: Audio) -> None:
        """
        Load audio data from an Audio object.

        Args:
            audio: Audio object to load
        """
        data = audio.data

        # Resample if needed
        if audio.sample_rate != self.sample_rate:
            try:
                from scipy import signal
                ratio = self.sample_rate / audio.sample_rate
                output_len = int(len(data) * ratio)
                data = signal.resample(data, output_len)
            except ImportError:
                # Simple resampling if scipy not available
                if audio.sample_rate > self.sample_rate:
                    # Downsampling
                    step = audio.sample_rate / self.sample_rate
                    indices = np.arange(0, len(data), step)
                    data = np.interp(indices, np.arange(len(data)), data)
                else:
                    # Upsampling - simple repeat
                    ratio = self.sample_rate / audio.sample_rate
                    data = np.repeat(data, int(ratio))

        # Convert mono to stereo if needed
        if audio.channels == 1 and self.channels == 2:
            data = np.repeat(data.reshape(-1, 1), 2, axis=1).flatten()

        # Convert stereo to mono if needed
        elif audio.channels == 2 and self.channels == 1:
            # Reshape to [frames, channels]
            stereo = data.reshape(-1, 2)
            # Mix down to mono
            data = np.mean(stereo, axis=1)

        self._audio_data = data
        self._total_frames = len(data) // max(1, self.channels)

    def _start_playback(self) -> None:
        """Start audio playback."""
        if not self._stream:
            self.open()

        self._is_playing = True
        self._stop_event.clear()

        # Start the stream
        self._stream.start_stream()

    def stop(self) -> None:
        """Stop audio playback."""
        if self._stream and self._stream.is_active():
            self._stream.stop_stream()

        self._is_playing = False
        self._stop_event.set()

    def pause(self) -> None:
        """Pause audio playback."""
        if self._stream and self._stream.is_active():
            self._stream.stop_stream()
            self._is_playing = False

    def resume(self) -> None:
        """Resume audio playback."""
        if self._stream and not self._stream.is_active() and self._audio_data is not None:
            self._stream.start_stream()
            self._is_playing = True

    def seek(self, position_seconds: float) -> None:
        """
        Seek to a specific position in the audio.

        Args:
            position_seconds: Position in seconds to seek to
        """
        if self._audio_data is None:
            return

        # Calculate position in frames
        position_frames = int(position_seconds * self.sample_rate)

        # Clamp to valid range
        position_frames = max(0, min(position_frames, self._total_frames))

        # Update position
        self._audio_position = position_frames

    def get_position(self) -> float:
        """
        Get current playback position in seconds.

        Returns:
            Current position in seconds
        """
        if self._audio_data is None:
            return 0.0

        return self._audio_position / self.sample_rate

    def get_duration(self) -> float:
        """
        Get total duration of the loaded audio in seconds.

        Returns:
            Total duration in seconds
        """
        if self._audio_data is None:
            return 0.0

        return self._total_frames / self.sample_rate

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if audio is playing, False otherwise
        """
        return self._is_playing and self._stream and self._stream.is_active()

    @staticmethod
    def list_devices() -> List[Dict[str, Any]]:
        """
        List available audio output devices.

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

                # Only include output devices
                if device_info.get('maxOutputChannels', 0) > 0:
                    devices.append({
                        'index': device_info.get('index', i),
                        'name': device_info.get('name', f"Device {i}"),
                        'channels': device_info.get('maxOutputChannels', 0),
                        'sample_rates': [
                            int(r) for r in device_info.get('supportedSampleRates', [44100, 48000])
                        ],
                        'default': device_info.get('isDefaultOutputDevice', False)
                    })
        finally:
            p.terminate()

        return devices

    @staticmethod
    def get_default_device() -> Optional[Dict[str, Any]]:
        """
        Get the default audio output device.

        Returns:
            Default device information or None if not found
        """
        devices = AudioPlayer.list_devices()

        # Find default device
        for device in devices:
            if device.get('default', False):
                return device

        # If no default device is marked, return the first one
        if devices:
            return devices[0]

        return None


# Convenient alias
Player = AudioPlayer
