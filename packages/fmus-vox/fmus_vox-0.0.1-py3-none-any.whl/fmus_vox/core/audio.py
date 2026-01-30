"""
Core audio processing functionality.

This module provides the Audio class which is the main entry point for all audio operations
in the fmus-vox library.
"""

from typing import Optional, Union, List, Tuple, BinaryIO, Any
import numpy as np
import os
import tempfile
from pathlib import Path
import soundfile as sf
import librosa
import pyrubberband as pyrb

from fmus_vox.core.errors import AudioError

class Audio:
    """
    Main class for audio operations in fmus-vox.

    The Audio class provides an intuitive interface for loading, processing,
    and manipulating audio data. It supports method chaining for clean,
    readable code.

    Examples:
        >>> # Load and process audio
        >>> audio = Audio.load("recording.wav")
        >>> processed = audio.normalize().denoise().resample(target_sr=16000)
        >>> processed.save("processed.wav")
        >>>
        >>> # Record and save audio
        >>> audio = Audio.record(seconds=5)
        >>> audio.save("recording.wav")
    """

    def __init__(self, data: np.ndarray, sample_rate: int):
        """
        Initialize an Audio object.

        Args:
            data: Audio data as a numpy array
            sample_rate: Sample rate of the audio in Hz
        """
        self._data = data
        self._sample_rate = sample_rate

    @classmethod
    def load(cls, source: Union[str, Path, BinaryIO, np.ndarray],
             sample_rate: Optional[int] = None) -> "Audio":
        """
        Load audio from file, bytes, or numpy array.

        Args:
            source: Audio source (file path, file-like object, or numpy array)
            sample_rate: Target sample rate for loading. If None, use the source's rate.
                         If source is a numpy array, this must be provided.

        Returns:
            Audio object

        Raises:
            AudioError: If the audio cannot be loaded
        """
        try:
            if isinstance(source, np.ndarray):
                if sample_rate is None:
                    raise AudioError("Sample rate must be provided when loading from numpy array")
                return cls(source, sample_rate)

            if isinstance(source, (str, Path)):
                data, sr = librosa.load(source, sr=sample_rate, mono=True)
                return cls(data, sr)

            # Handle file-like objects
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(source.read())
                tmp_name = tmp.name

            try:
                data, sr = librosa.load(tmp_name, sr=sample_rate, mono=True)
                return cls(data, sr)
            finally:
                os.unlink(tmp_name)

        except Exception as e:
            raise AudioError(f"Failed to load audio: {str(e)}")

    @classmethod
    def record(cls, seconds: Optional[float] = None,
               sample_rate: int = 44100, **kwargs) -> "Audio":
        """
        Record audio from microphone.

        Args:
            seconds: Duration in seconds to record. If None, records until stopped.
            sample_rate: Sample rate to record at
            **kwargs: Additional arguments for recording

        Returns:
            Audio object containing the recorded audio

        Raises:
            AudioError: If recording fails
        """
        try:
            import sounddevice as sd

            if seconds is None:
                # Interactive recording
                print("Recording... Press Ctrl+C to stop.")
                try:
                    data = sd.rec(int(sample_rate * 3600), samplerate=sample_rate,
                                 channels=1, blocking=True)
                except KeyboardInterrupt:
                    sd.stop()
            else:
                # Fixed duration recording
                data = sd.rec(int(sample_rate * seconds), samplerate=sample_rate,
                             channels=1, blocking=True)

            return cls(data.flatten(), sample_rate)

        except Exception as e:
            raise AudioError(f"Failed to record audio: {str(e)}")

    def save(self, path: Union[str, Path], format: Optional[str] = None, **kwargs) -> str:
        """
        Save audio to file.

        Args:
            path: Path to save the audio file
            format: Audio format (inferred from path if None)
            **kwargs: Additional arguments for saving

        Returns:
            Path to the saved file

        Raises:
            AudioError: If saving fails
        """
        try:
            sf.write(path, self._data, self._sample_rate, format=format, **kwargs)
            return str(path)
        except Exception as e:
            raise AudioError(f"Failed to save audio: {str(e)}")

    def play(self) -> None:
        """
        Play audio through speakers.

        Raises:
            AudioError: If playback fails
        """
        try:
            import sounddevice as sd
            sd.play(self._data, self._sample_rate)
            sd.wait()
        except Exception as e:
            raise AudioError(f"Failed to play audio: {str(e)}")

    def trim(self, start: float = 0, end: Optional[float] = None) -> "Audio":
        """
        Trim audio to specified time range.

        Args:
            start: Start time in seconds
            end: End time in seconds. If None, trim to the end of the audio.

        Returns:
            New Audio object with trimmed audio
        """
        start_sample = int(start * self._sample_rate)
        if end is None:
            end_sample = len(self._data)
        else:
            end_sample = min(int(end * self._sample_rate), len(self._data))

        return Audio(self._data[start_sample:end_sample], self._sample_rate)

    def denoise(self, strength: float = 0.5) -> "Audio":
        """
        Remove noise from audio.

        Args:
            strength: Denoising strength (0.0 to 1.0)

        Returns:
            New Audio object with denoised audio
        """
        try:
            import noisereduce as nr
            denoised = nr.reduce_noise(
                y=self._data,
                sr=self._sample_rate,
                prop_decrease=strength
            )
            return Audio(denoised, self._sample_rate)
        except ImportError:
            # Fall back to simple high-pass filter if noisereduce not available
            from scipy import signal
            b, a = signal.butter(5, 100 / (self._sample_rate / 2), 'highpass')
            denoised = signal.filtfilt(b, a, self._data)
            return Audio(denoised, self._sample_rate)

    def normalize(self, target_db: float = -3) -> "Audio":
        """
        Normalize audio volume.

        Args:
            target_db: Target peak dB level

        Returns:
            New Audio object with normalized audio
        """
        peak = np.max(np.abs(self._data))
        if peak > 0:
            target_peak = 10 ** (target_db / 20)
            normalized = self._data * (target_peak / peak)
            return Audio(normalized, self._sample_rate)
        return self

    def resample(self, target_sr: int = 16000) -> "Audio":
        """
        Resample audio to target sample rate.

        Args:
            target_sr: Target sample rate in Hz

        Returns:
            New Audio object with resampled audio
        """
        if self._sample_rate == target_sr:
            return self

        resampled = librosa.resample(
            y=self._data,
            orig_sr=self._sample_rate,
            target_sr=target_sr
        )
        return Audio(resampled, target_sr)

    def detect_vad(self, threshold: float = 0.5) -> List[Tuple[float, float]]:
        """
        Detect voice activity segments.

        Args:
            threshold: Energy threshold for voice detection (0.0 to 1.0)

        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        # Simple energy-based VAD
        energy = librosa.feature.rms(y=self._data)[0]
        energy_norm = energy / np.max(energy) if np.max(energy) > 0 else energy

        # Find segments above threshold
        is_speech = energy_norm > threshold

        # Convert to time ranges
        frame_length = 2048
        hop_length = 512
        segments = []
        in_segment = False
        start_frame = 0

        for i, speech in enumerate(is_speech):
            if speech and not in_segment:
                in_segment = True
                start_frame = i
            elif not speech and in_segment:
                in_segment = False
                # Convert frames to time
                start_time = librosa.frames_to_time(start_frame,
                                                   sr=self._sample_rate,
                                                   hop_length=hop_length)
                end_time = librosa.frames_to_time(i,
                                                 sr=self._sample_rate,
                                                 hop_length=hop_length)
                segments.append((start_time, end_time))

        # Handle case where audio ends during speech
        if in_segment:
            start_time = librosa.frames_to_time(start_frame,
                                               sr=self._sample_rate,
                                               hop_length=hop_length)
            end_time = librosa.frames_to_time(len(is_speech),
                                             sr=self._sample_rate,
                                             hop_length=hop_length)
            segments.append((start_time, end_time))

        return segments

    def split_on_silence(self, min_silence_len: int = 500,
                         silence_thresh: float = -40) -> List["Audio"]:
        """
        Split audio on silence into segments.

        Args:
            min_silence_len: Minimum silence length in milliseconds
            silence_thresh: Silence threshold in dB

        Returns:
            List of Audio objects, one for each non-silent segment
        """
        # Convert min_silence_len from ms to samples
        min_silence_samples = int(min_silence_len * self._sample_rate / 1000)

        # Convert silence_thresh from dB to amplitude ratio
        silence_thresh_amp = 10 ** (silence_thresh / 20)

        # Find silent points
        is_silent = np.abs(self._data) < silence_thresh_amp

        # Group silent points into ranges
        silent_ranges = []
        start = None

        for i, silent in enumerate(is_silent):
            if silent and start is None:
                start = i
            elif not silent and start is not None:
                if i - start >= min_silence_samples:
                    silent_ranges.append((start, i))
                start = None

        # Handle case where audio ends in silence
        if start is not None and len(is_silent) - start >= min_silence_samples:
            silent_ranges.append((start, len(is_silent)))

        # Create segments based on silent ranges
        segments = []

        if not silent_ranges:
            segments.append(self)
            return segments

        # Add segment from start to first silence
        if silent_ranges[0][0] > 0:
            segments.append(
                Audio(self._data[:silent_ranges[0][0]], self._sample_rate)
            )

        # Add segments between silences
        for i in range(len(silent_ranges) - 1):
            start = silent_ranges[i][1]
            end = silent_ranges[i + 1][0]
            if end > start:
                segments.append(
                    Audio(self._data[start:end], self._sample_rate)
                )

        # Add segment from last silence to end
        if silent_ranges[-1][1] < len(self._data):
            segments.append(
                Audio(self._data[silent_ranges[-1][1]:], self._sample_rate)
            )

        return segments

    def change_speed(self, speed_factor: float = 1.0) -> "Audio":
        """
        Change the playback speed of the audio.

        Args:
            speed_factor: Speed factor (1.0 = original speed)

        Returns:
            New Audio object with changed speed
        """
        if speed_factor == 1.0:
            return self

        y_stretched = pyrb.time_stretch(self._data, self._sample_rate, speed_factor)
        return Audio(y_stretched, self._sample_rate)

    def change_pitch(self, semitones: float = 0.0) -> "Audio":
        """
        Change the pitch of the audio.

        Args:
            semitones: Number of semitones to shift (-12 to +12)

        Returns:
            New Audio object with changed pitch
        """
        if semitones == 0:
            return self

        y_shifted = pyrb.pitch_shift(self._data, self._sample_rate, semitones)
        return Audio(y_shifted, self._sample_rate)

    @property
    def duration(self) -> float:
        """Get audio duration in seconds."""
        return len(self._data) / self._sample_rate

    @property
    def sample_rate(self) -> int:
        """Get audio sample rate."""
        return self._sample_rate

    @property
    def data(self) -> np.ndarray:
        """Get audio data as numpy array."""
        return self._data

    def __len__(self) -> int:
        """Get length of audio in samples."""
        return len(self._data)
