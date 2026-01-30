"""
Audio enhancement functionality for fmus-vox.

This module provides audio enhancement capabilities including noise reduction,
audio cleanup, and quality improvement.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple

from fmus_vox.core.audio import Audio
from fmus_vox.core.utils import get_logger


class AudioEnhancer:
    """
    Audio enhancement class for improving audio quality.

    This class provides various audio enhancement techniques including
    noise reduction, normalization, and audio cleanup.

    Args:
        **kwargs: Additional enhancement parameters
    """

    def __init__(self, **kwargs):
        """
        Initialize the audio enhancer.

        Args:
            **kwargs: Additional enhancement parameters
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def denoise(
        self,
        audio: Audio,
        method: str = "spectral",
        **kwargs
    ) -> Audio:
        """
        Remove noise from audio.

        Args:
            audio: Input audio
            method: Noise reduction method (spectral, moving_average, median)
            **kwargs: Method-specific parameters

        Returns:
            Denoised audio
        """
        if method == "spectral":
            return self._spectral_denoise(audio, **kwargs)
        elif method == "moving_average":
            return self._moving_average_denoise(audio, **kwargs)
        elif method == "median":
            return self._median_filter_denoise(audio, **kwargs)
        else:
            raise ValueError(f"Unknown denoising method: {method}")

    def _spectral_denoise(
        self,
        audio: Audio,
        noise_floor: float = 0.02,
        reduction_strength: float = 0.8,
        **kwargs
    ) -> Audio:
        """
        Spectral subtraction noise reduction.

        Args:
            audio: Input audio
            noise_floor: Noise floor threshold (0-1)
            reduction_strength: Strength of reduction (0-1)

        Returns:
            Denoised audio
        """
        try:
            import librosa
        except ImportError:
            self.logger.warning("librosa not available, using simple denoise")
            return self._simple_denoise(audio, noise_floor, reduction_strength)

        # Get audio data
        audio_data = audio.data.copy()

        # Handle multi-channel
        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = self._spectral_denoise_single(
                    audio_data[:, i],
                    audio.sample_rate,
                    noise_floor,
                    reduction_strength
                )
                channels.append(channel)
            result = np.column_stack(channels)
        else:
            result = self._spectral_denoise_single(
                audio_data,
                audio.sample_rate,
                noise_floor,
                reduction_strength
            )

        return Audio(result, audio.sample_rate)

    def _spectral_denoise_single(
        self,
        data: np.ndarray,
        sample_rate: int,
        noise_floor: float,
        strength: float
    ) -> np.ndarray:
        """Apply spectral denoising to single channel."""
        try:
            import librosa

            # Compute STFT
            stft = librosa.stft(data)
            magnitude = np.abs(stft)
            phase = np.angle(stft)

            # Estimate noise from quiet portions
            noise_profile = np.percentile(magnitude, 10, axis=1, keepdims=True)

            # Create mask
            mask = (magnitude - noise_profile * noise_floor) / (magnitude + 1e-10)
            mask = np.clip(mask, 0, 1)

            # Apply strength
            mask = mask ** (1 - strength)

            # Apply mask
            enhanced_magnitude = magnitude * mask

            # Reconstruct
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            result = librosa.istft(enhanced_stft)

            # Handle length mismatch
            if len(result) > len(data):
                result = result[:len(data)]
            elif len(result) < len(data):
                result = np.pad(result, (0, len(data) - len(result)))

            return result

        except Exception as e:
            self.logger.warning(f"Spectral denoise failed: {e}, using simple method")
            return self._simple_denoise_single(data, noise_floor, strength)

    def _simple_denoise_single(
        self,
        data: np.ndarray,
        noise_floor: float,
        strength: float
    ) -> np.ndarray:
        """Simple threshold-based noise reduction."""
        # Calculate magnitude
        magnitude = np.abs(data)

        # Create mask
        mask = (magnitude > noise_floor).astype(float)

        # Smooth the mask
        kernel_size = max(1, int(0.01 * len(data)))  # 10ms window
        if kernel_size > 1:
            kernel = np.ones(kernel_size) / kernel_size
            mask = np.convolve(mask, kernel, mode='same')

        # Apply mask with strength
        mask = mask * strength + (1 - strength) * np.ones_like(mask)

        return data * mask

    def _simple_denoise(
        self,
        audio: Audio,
        noise_floor: float,
        strength: float
    ) -> Audio:
        """Simple threshold-based denoising for all channels."""
        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = self._simple_denoise_single(
                    audio_data[:, i],
                    noise_floor,
                    strength
                )
                channels.append(channel)
            result = np.column_stack(channels)
        else:
            result = self._simple_denoise_single(
                audio_data,
                noise_floor,
                strength
            )

        return Audio(result, audio.sample_rate)

    def _moving_average_denoise(
        self,
        audio: Audio,
        window_size: int = 5,
        **kwargs
    ) -> Audio:
        """
        Moving average noise reduction.

        Args:
            audio: Input audio
            window_size: Size of the moving average window

        Returns:
            Denoised audio
        """
        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = audio_data[:, i]
                smoothed = np.convolve(
                    channel,
                    np.ones(window_size) / window_size,
                    mode='same'
                )
                channels.append(smoothed)
            result = np.column_stack(channels)
        else:
            result = np.convolve(
                audio_data,
                np.ones(window_size) / window_size,
                mode='same'
            )

        return Audio(result, audio.sample_rate)

    def _median_filter_denoise(
        self,
        audio: Audio,
        kernel_size: int = 5,
        **kwargs
    ) -> Audio:
        """
        Median filter noise reduction.

        Args:
            audio: Input audio
            kernel_size: Size of the median filter kernel

        Returns:
            Denoised audio
        """
        from scipy import signal

        audio_data = audio.data.copy()

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = audio_data[:, i]
                smoothed = signal.medfilt(channel, kernel_size=kernel_size)
                channels.append(smoothed)
            result = np.column_stack(channels)
        else:
            result = signal.medfilt(audio_data, kernel_size=kernel_size)

        return Audio(result, audio.sample_rate)

    def enhance(
        self,
        audio: Audio,
        normalize: bool = True,
        denoise: bool = True,
        trim_silence: bool = False,
        **kwargs
    ) -> Audio:
        """
        Apply comprehensive audio enhancement.

        Args:
            audio: Input audio
            normalize: Whether to normalize audio
            denoise: Whether to denoise audio
            trim_silence: Whether to trim silence from ends
            **kwargs: Additional parameters

        Returns:
            Enhanced audio
        """
        result = audio

        # Apply denoising
        if denoise:
            result = self.denoise(result, **kwargs)

        # Normalize
        if normalize:
            result = result.normalize()

        # Trim silence
        if trim_silence:
            result = result.trim_silence()

        return result

    def reduce_echo(
        self,
        audio: Audio,
        delay: float = 0.1,
        decay: float = 0.5,
        **kwargs
    ) -> Audio:
        """
        Simple echo reduction using spectral subtraction.

        Args:
            audio: Input audio
            delay: Echo delay in seconds
            decay: Echo decay factor

        Returns:
            Echo-reduced audio
        """
        # Simple approach: apply a high-pass filter to reduce echo
        from scipy import signal

        audio_data = audio.data.copy()

        # Design high-pass filter
        nyquist = audio.sample_rate / 2
        cutoff = 100 / nyquist  # 100 Hz cutoff
        b, a = signal.butter(4, cutoff, btype='high')

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = signal.filtfilt(b, a, audio_data[:, i])
                channels.append(channel)
            result = np.column_stack(channels)
        else:
            result = signal.filtfilt(b, a, audio_data)

        return Audio(result, audio.sample_rate)

    def improve_clarity(
        self,
        audio: Audio,
        boost_high: float = 2.0,
        boost_mid: float = 1.2,
        **kwargs
    ) -> Audio:
        """
        Improve speech clarity using EQ.

        Args:
            audio: Input audio
            boost_high: High frequency boost (dB)
            boost_mid: Mid frequency boost (dB)

        Returns:
            Enhanced audio
        """
        from scipy import signal

        audio_data = audio.data.copy()

        # Convert dB to linear
        high_gain = 10 ** (boost_high / 20)
        mid_gain = 10 ** (boost_mid / 20)

        # Design filters
        nyquist = audio.sample_rate / 2

        # High shelf (2-8 kHz)
        high_cutoff = 5000 / nyquist
        b_high, a_high = signal.butter(2, high_cutoff, btype='high')

        # Mid band (500 Hz - 2 kHz)
        low_cutoff = 500 / nyquist
        b_mid_low, a_mid_low = signal.butter(2, low_cutoff, btype='high')
        high_cutoff_mid = 2000 / nyquist
        b_mid_high, a_mid_high = signal.butter(2, high_cutoff_mid, btype='low')

        if audio_data.ndim > 1:
            channels = []
            for i in range(audio_data.shape[1]):
                channel = audio_data[:, i].copy()

                # Extract frequency bands
                high_freq = signal.filtfilt(b_high, a_high, channel)
                mid_freq = signal.filtfilt(b_mid_low, a_mid_low, channel)
                mid_freq = signal.filtfilt(b_mid_high, a_mid_high, mid_freq)

                # Apply gains and mix
                enhanced = channel * 0.3 + mid_freq * (mid_gain - 0.3) + high_freq * (high_gain - 0.3)
                channels.append(enhanced)

            result = np.column_stack(channels)
        else:
            channel = audio_data.copy()
            high_freq = signal.filtfilt(b_high, a_high, channel)
            mid_freq = signal.filtfilt(b_mid_low, a_mid_low, channel)
            mid_freq = signal.filtfilt(b_mid_high, a_mid_high, mid_freq)
            result = channel * 0.3 + mid_freq * (mid_gain - 0.3) + high_freq * (high_gain - 0.3)

        return Audio(result, audio.sample_rate)


def enhance_audio(audio: Audio, **kwargs) -> Audio:
    """
    Convenience function for audio enhancement.

    Args:
        audio: Input audio
        **kwargs: Enhancement parameters

    Returns:
        Enhanced audio
    """
    enhancer = AudioEnhancer()
    return enhancer.enhance(audio, **kwargs)


def denoise_audio(audio: Audio, method: str = "spectral", **kwargs) -> Audio:
    """
    Convenience function for noise reduction.

    Args:
        audio: Input audio
        method: Noise reduction method
        **kwargs: Method-specific parameters

    Returns:
        Denoised audio
    """
    enhancer = AudioEnhancer()
    return enhancer.denoise(audio, method=method, **kwargs)
