"""
Voice transformation functionality for fmus-vox.

This module provides voice transformation capabilities including pitch shifting,
time stretching, formant shifting, and voice conversion.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
from scipy import signal
from scipy.interpolate import interp1d

from fmus_vox.core.audio import Audio
from fmus_vox.core.utils import get_logger


class VoiceTransformer:
    """
    Voice transformation class for modifying voice characteristics.

    This class provides various voice transformation techniques including
    pitch shifting, time stretching, formant modification, and more.

    Args:
        **kwargs: Additional transformation parameters
    """

    def __init__(self, **kwargs):
        """
        Initialize the voice transformer.

        Args:
            **kwargs: Additional transformation parameters
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def shift_pitch(
        self,
        audio: Audio,
        semitones: float = 0.0,
        method: str = "librosa"
    ) -> Audio:
        """
        Shift the pitch of audio.

        Args:
            audio: Input audio
            semitones: Number of semitones to shift (positive=higher, negative=lower)
            method: Method to use (librosa, resample)

        Returns:
            Pitch-shifted audio
        """
        if method == "librosa":
            return self._pitch_shift_librosa(audio, semitones)
        else:
            return self._pitch_shift_resample(audio, semitones)

    def _pitch_shift_librosa(self, audio: Audio, semitones: float) -> Audio:
        """Pitch shift using librosa."""
        try:
            import librosa
            import pyrubberband as pyrb

            audio_data = audio.data
            if audio_data.ndim > 1:
                # Process each channel
                channels = []
                for i in range(audio_data.shape[1]):
                    channel = self._pitch_shift_librosa_single(
                        audio_data[:, i],
                        audio.sample_rate,
                        semitones
                    )
                    channels.append(channel)
                result = np.column_stack(channels)
            else:
                result = self._pitch_shift_librosa_single(
                    audio_data,
                    audio.sample_rate,
                    semitones
                )

            return Audio(result, audio.sample_rate)

        except ImportError:
            self.logger.warning("librosa/pyrubberband not available, using resample method")
            return self._pitch_shift_resample(audio, semitones)

    def _pitch_shift_librosa_single(
        self,
        data: np.ndarray,
        sample_rate: int,
        semitones: float
    ) -> np.ndarray:
        """Pitch shift single channel using rubberband."""
        try:
            import pyrubberband as pyrb

            # Rubberband uses steps parameter where 1.0 = no change
            # semitones to ratio: 2^(semitones/12)
            n_steps = 2 ** (semitones / 12.0)

            result = pyrb.pitch_shift(data, sample_rate, n_steps)

            # Handle length changes
            if len(result) > len(data):
                result = result[:len(data)]
            elif len(result) < len(data):
                result = np.pad(result, (0, len(data) - len(result)))

            return result

        except Exception as e:
            self.logger.warning(f"Rubberband pitch shift failed: {e}")
            return self._pitch_shift_resample_single(data, sample_rate, semitones)

    def _pitch_shift_resample(self, audio: Audio, semitones: float) -> Audio:
        """Pitch shift using resampling (simpler, lower quality)."""
        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = self._pitch_shift_resample_single(
                    audio_data[:, i],
                    audio.sample_rate,
                    semitones
                )
                channels.append(channel)
            result = np.column_stack(channels)
        else:
            result = self._pitch_shift_resample_single(
                audio_data,
                audio.sample_rate,
                semitones
            )

        return Audio(result, audio.sample_rate)

    def _pitch_shift_resample_single(
        self,
        data: np.ndarray,
        sample_rate: int,
        semitones: float
    ) -> np.ndarray:
        """Pitch shift single channel using resampling."""
        # Calculate resampling ratio
        ratio = 2 ** (semitones / 12.0)

        # Resample
        from scipy import signal as scipy_signal

        original_length = len(data)
        resampled = scipy_signal.resample(data, int(original_length * ratio))

        # Time stretch back to original length
        # Simple linear interpolation
        indices = np.linspace(0, len(resampled) - 1, original_length)
        result = np.interp(
            np.arange(original_length),
            np.arange(len(resampled)),
            resampled
        )

        return result

    def stretch_time(
        self,
        audio: Audio,
        factor: float = 1.0,
        method: str = "librosa"
    ) -> Audio:
        """
        Stretch or compress audio in time without changing pitch.

        Args:
            audio: Input audio
            factor: Time stretch factor (>1=slower, <1=faster)
            method: Method to use (librosa, phase_vocoder)

        Returns:
            Time-stretched audio
        """
        if factor == 1.0:
            return audio

        if method == "librosa":
            return self._time_stretch_librosa(audio, factor)
        else:
            return self._time_stretch_phase(audio, factor)

    def _time_stretch_librosa(self, audio: Audio, factor: float) -> Audio:
        """Time stretch using librosa."""
        try:
            import librosa
            import pyrubberband as pyrb

            audio_data = audio.data
            if audio_data.ndim > 1:
                channels = []
                for i in range(audio_data.shape[1]):
                    channel = pyrb.time_stretch(
                        audio_data[:, i],
                        audio.sample_rate,
                        factor
                    )
                    channels.append(channel)
                result = np.column_stack(channels)
            else:
                result = pyrb.time_stretch(
                    audio_data,
                    audio.sample_rate,
                    factor
                )

            return Audio(result, audio.sample_rate)

        except ImportError:
            self.logger.warning("pyrubberband not available, using phase vocoder")
            return self._time_stretch_phase(audio, factor)

    def _time_stretch_phase(self, audio: Audio, factor: float) -> Audio:
        """Time stretch using phase vocoder."""
        try:
            import librosa

            audio_data = audio.data
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Use librosa's phase vocoder
            result = librosa.effects.time_stretch(audio_data, rate=factor)

            return Audio(result, audio.sample_rate)

        except Exception as e:
            self.logger.warning(f"Phase vocoder failed: {e}, using simple resample")
            # Fallback to simple resampling
            audio_data = audio.data
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            new_length = int(len(audio_data) * factor)
            from scipy import signal as scipy_signal
            result = scipy_signal.resample(audio_data, new_length)

            return Audio(result, audio.sample_rate)

    def shift_formants(
        self,
        audio: Audio,
        shift_factor: float = 1.0,
        **kwargs
    ) -> Audio:
        """
        Shift formants to change vocal tract length perception.

        Args:
            audio: Input audio
            shift_factor: Formant shift factor (>1=longer tract, <1=shorter)
            **kwargs: Additional parameters

        Returns:
            Formant-shifted audio
        """
        try:
            import librosa

            audio_data = audio.data.copy()
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Compute STFT
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            phase = np.angle(stft)

            # Shift frequency bins
            num_bins = magnitude.shape[0]
            shifted_magnitude = np.zeros_like(magnitude)

            for i in range(magnitude.shape[1]):
                # Interpolate to shift formants
                original_indices = np.arange(num_bins)
                shifted_indices = original_indices * shift_factor
                shifted_indices = np.clip(shifted_indices, 0, num_bins - 1)

                interpolator = interp1d(
                    original_indices,
                    magnitude[:, i],
                    kind='linear',
                    bounds_error=False,
                    fill_value=0
                )
                shifted_magnitude[:, i] = interpolator(shifted_indices)

            # Reconstruct
            shifted_stft = shifted_magnitude * np.exp(1j * phase)
            result = librosa.istft(shifted_stft)

            return Audio(result, audio.sample_rate)

        except ImportError:
            self.logger.warning("librosa not available for formant shifting")
            return audio

    def add_reverb(
        self,
        audio: Audio,
        room_size: float = 0.5,
        damping: float = 0.5,
        wet_level: float = 0.3,
        dry_level: float = 0.7,
        **kwargs
    ) -> Audio:
        """
        Add reverb effect to audio.

        Args:
            audio: Input audio
            room_size: Room size (0-1)
            damping: Damping factor (0-1)
            wet_level: Wet signal level (0-1)
            dry_level: Dry signal level (0-1)
            **kwargs: Additional parameters

        Returns:
            Audio with reverb
        """
        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Simple delay-based reverb
        delay_samples = int(room_size * audio.sample_rate * 0.5)
        decay = damping * 0.5

        # Create reverb tail
        reverb_tail = np.zeros_like(audio_data)

        for i in range(4):  # Multiple echoes
            delay = delay_samples * (i + 1)
            gain = decay ** (i + 1)

            if delay < len(audio_data):
                reverb_tail[delay:] += audio_data[:-delay] * gain

        # Mix wet and dry signals
        result = audio_data * dry_level + reverb_tail * wet_level

        # Normalize
        result = result / np.max(np.abs(result))

        return Audio(result, audio.sample_rate)

    def apply_robot_effect(self, audio: Audio, modulation_rate: float = 10.0) -> Audio:
        """
        Apply a robotic voice effect.

        Args:
            audio: Input audio
            modulation_rate: Modulation rate in Hz

        Returns:
            Robot-processed audio
        """
        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Create amplitude modulation
        t = np.linspace(0, len(audio_data) / audio.sample_rate, len(audio_data))
        modulator = 0.5 + 0.5 * np.sin(2 * np.pi * modulation_rate * t)

        # Apply modulation
        result = audio_data * modulator

        return Audio(result, audio.sample_rate)

    def apply_telephone_effect(self, audio: Audio) -> Audio:
        """
        Apply a telephone-like bandpass filter effect.

        Args:
            audio: Input audio

        Returns:
            Telephone-processed audio
        """
        from scipy import signal as scipy_signal

        audio_data = audio.data.copy()

        # Telephone frequency range: 300Hz - 3400Hz
        lowcut = 300.0
        highcut = 3400.0
        nyquist = audio.sample_rate / 2

        low = lowcut / nyquist
        high = highcut / nyquist

        # Design bandpass filter
        b, a = scipy_signal.butter(4, [low, high], btype='band')

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = scipy_signal.filtfilt(b, a, audio_data[:, i])
                channels.append(channel)
            result = np.column_stack(channels)
        else:
            result = scipy_signal.filtfilt(b, a, audio_data)

        # Add some distortion
        result = np.tanh(result * 2.0) / 2.0

        return Audio(result, audio.sample_rate)


def transform_voice(audio: Audio, transformation: str, **kwargs) -> Audio:
    """
    Convenience function for voice transformation.

    Args:
        audio: Input audio
        transformation: Type of transformation (pitch_shift, time_stretch, etc.)
        **kwargs: Transformation parameters

    Returns:
        Transformed audio
    """
    transformer = VoiceTransformer()

    if transformation == "pitch_shift":
        semitones = kwargs.get("semitones", 0.0)
        return transformer.shift_pitch(audio, semitones)
    elif transformation == "time_stretch":
        factor = kwargs.get("factor", 1.0)
        return transformer.stretch_time(audio, factor)
    elif transformation == "formant_shift":
        shift_factor = kwargs.get("shift_factor", 1.0)
        return transformer.shift_formants(audio, shift_factor)
    elif transformation == "reverb":
        return transformer.add_reverb(audio, **kwargs)
    elif transformation == "robot":
        return transformer.apply_robot_effect(audio, **kwargs)
    elif transformation == "telephone":
        return transformer.apply_telephone_effect(audio)
    else:
        raise ValueError(f"Unknown transformation: {transformation}")


def shift_pitch(audio: Audio, semitones: float = 0.0) -> Audio:
    """Convenience function for pitch shifting."""
    return transform_voice(audio, "pitch_shift", semitones=semitones)


def stretch_time(audio: Audio, factor: float = 1.0) -> Audio:
    """Convenience function for time stretching."""
    return transform_voice(audio, "time_stretch", factor=factor)
