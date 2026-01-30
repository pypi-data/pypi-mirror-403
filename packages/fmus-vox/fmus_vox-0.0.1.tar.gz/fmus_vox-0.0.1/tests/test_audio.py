"""
Tests for the core Audio class.

This module contains tests for the Audio class functionality including
loading, processing, and manipulating audio data.
"""

import os
import tempfile
import numpy as np
import pytest
from pathlib import Path

from fmus_vox.core.audio import Audio
from fmus_vox.core.errors import AudioError

# Komentar: Fixture untuk membuat file audio sampel untuk pengujian
@pytest.fixture
def sample_audio_path():
    """Create a sample audio file for testing."""
    # Create a temporary audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    # Generate a simple sine wave
    sample_rate = 16000
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave at half amplitude

    # Create an Audio object and save it
    audio = Audio(data, sample_rate)
    audio.save(tmp_path)

    yield tmp_path

    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

# Komentar: Pengujian loading audio dari file
def test_load_from_file(sample_audio_path):
    """Test loading audio from a file."""
    audio = Audio.load(sample_audio_path)

    assert isinstance(audio, Audio)
    assert audio.sample_rate == 16000
    assert len(audio.data) == 16000
    assert isinstance(audio.data, np.ndarray)

# Komentar: Pengujian loading audio dari numpy array
def test_load_from_array():
    """Test loading audio from a numpy array."""
    data = np.zeros(16000)
    sample_rate = 16000

    audio = Audio.load(data, sample_rate=sample_rate)

    assert isinstance(audio, Audio)
    assert audio.sample_rate == sample_rate
    assert len(audio.data) == len(data)
    assert np.array_equal(audio.data, data)

# Komentar: Pengujian error loading audio dari array tanpa sample rate
def test_load_from_array_without_sample_rate():
    """Test loading audio from array without sample rate raises error."""
    data = np.zeros(16000)

    with pytest.raises(AudioError):
        Audio.load(data)

# Komentar: Pengujian saving audio ke file
def test_save(sample_audio_path):
    """Test saving audio to a file."""
    audio = Audio.load(sample_audio_path)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        output_path = tmp.name

    try:
        saved_path = audio.save(output_path)

        assert os.path.exists(saved_path)
        assert saved_path == output_path

        # Load the saved file and check if it's the same
        saved_audio = Audio.load(saved_path)
        assert saved_audio.sample_rate == audio.sample_rate
        assert len(saved_audio.data) == len(audio.data)
        # Audio data should be approximately equal (not exactly due to encoding/decoding)
        assert np.allclose(saved_audio.data, audio.data, atol=1e-4)

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

# Komentar: Pengujian properti audio
def test_audio_properties():
    """Test audio properties."""
    data = np.zeros(16000)
    sample_rate = 16000
    audio = Audio(data, sample_rate)

    assert audio.duration == 1.0  # 16000 samples at 16000 Hz = 1 second
    assert audio.sample_rate == sample_rate
    assert len(audio) == len(data)
    assert np.array_equal(audio.data, data)

# Komentar: Pengujian metode trim
def test_trim():
    """Test trimming audio."""
    sample_rate = 16000
    duration = 2.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    audio = Audio(data, sample_rate)

    # Trim to middle 1 second
    trimmed = audio.trim(start=0.5, end=1.5)

    assert isinstance(trimmed, Audio)
    assert trimmed.sample_rate == sample_rate
    assert trimmed.duration == 1.0
    assert len(trimmed.data) == 16000  # 1 second at 16000 Hz

    # Verify we got the right part
    start_sample = int(0.5 * sample_rate)
    end_sample = int(1.5 * sample_rate)
    assert np.array_equal(trimmed.data, data[start_sample:end_sample])

# Komentar: Pengujian method chaining
def test_method_chaining():
    """Test method chaining."""
    sample_rate = 16000
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    audio = Audio(data, sample_rate)

    # Chain multiple methods
    result = audio.normalize().resample(target_sr=8000).change_speed(speed_factor=1.5)

    assert isinstance(result, Audio)
    assert result.sample_rate == 8000
    # Speed 1.5x means the duration is 2/3 of the original after resampling to 8000 Hz
    assert np.isclose(result.duration, (1.0 / 1.5), rtol=1e-2)

# Komentar: Pengujian normalisasi audio
def test_normalize():
    """Test audio normalization."""
    # Create audio with different amplitude
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = 0.1 * np.sin(2 * np.pi * 440 * t)  # Low amplitude sine wave

    audio = Audio(data, sample_rate)
    normalized = audio.normalize(target_db=-3)

    # Check that the peak amplitude is now at the target level
    target_peak = 10 ** (-3/20)  # -3 dB as amplitude ratio
    actual_peak = np.max(np.abs(normalized.data))
    assert np.isclose(actual_peak, target_peak, rtol=1e-5)

# Komentar: Pengujian resampling audio
def test_resample():
    """Test audio resampling."""
    # Create audio
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    audio = Audio(data, sample_rate)

    # Resample to 8000 Hz
    resampled = audio.resample(target_sr=8000)

    assert resampled.sample_rate == 8000
    assert len(resampled.data) == 8000  # 1 second at 8000 Hz
    assert resampled.duration == audio.duration  # Duration should be preserved

# Komentar: Pengujian fungsi VAD
def test_detect_vad():
    """Test voice activity detection."""
    # Create audio with silence and voice
    sample_rate = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # First second is silence, middle second is voice, last second is silence
    data = np.zeros_like(t)
    middle_start = int(sample_rate * 1.0)
    middle_end = int(sample_rate * 2.0)
    data[middle_start:middle_end] = 0.5 * np.sin(2 * np.pi * 440 * t[middle_start:middle_end])

    audio = Audio(data, sample_rate)

    # Detect voice activity
    segments = audio.detect_vad(threshold=0.1)

    assert len(segments) == 1
    # Should detect voice in the middle section
    assert segments[0][0] >= 0.9 and segments[0][0] <= 1.1  # Start around 1.0s
    assert segments[0][1] >= 1.9 and segments[0][1] <= 2.1  # End around 2.0s

# Komentar: Pengujian split audio pada silence
def test_split_on_silence():
    """Test splitting audio on silence."""
    # Create audio with 3 voiced segments separated by silence
    sample_rate = 16000
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    data = np.zeros_like(t)
    # 0.5-1.0s: voice
    segment1 = slice(int(0.5 * sample_rate), int(1.0 * sample_rate))
    # 2.0-2.5s: voice
    segment2 = slice(int(2.0 * sample_rate), int(2.5 * sample_rate))
    # 3.5-4.0s: voice
    segment3 = slice(int(3.5 * sample_rate), int(4.0 * sample_rate))

    data[segment1] = 0.5 * np.sin(2 * np.pi * 440 * t[segment1])
    data[segment2] = 0.5 * np.sin(2 * np.pi * 440 * t[segment2])
    data[segment3] = 0.5 * np.sin(2 * np.pi * 440 * t[segment3])

    audio = Audio(data, sample_rate)

    # Split on silence
    segments = audio.split_on_silence(min_silence_len=500, silence_thresh=-40)

    assert len(segments) == 3
    # Check each segment duration is approximately 0.5 seconds
    for segment in segments:
        assert np.isclose(segment.duration, 0.5, atol=0.1)

# Komentar: Pengujian perubahan kecepatan audio
def test_change_speed():
    """Test changing audio speed."""
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    audio = Audio(data, sample_rate)

    # Speed up by 2x
    faster = audio.change_speed(speed_factor=2.0)

    assert faster.sample_rate == audio.sample_rate
    assert np.isclose(faster.duration, 0.5, atol=0.05)  # Duration should be halved

    # Slow down by 0.5x
    slower = audio.change_speed(speed_factor=0.5)

    assert slower.sample_rate == audio.sample_rate
    assert np.isclose(slower.duration, 2.0, atol=0.05)  # Duration should be doubled

# Komentar: Pengujian perubahan pitch audio
def test_change_pitch():
    """Test changing audio pitch."""
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    audio = Audio(data, sample_rate)

    # Shift pitch up by 2 semitones
    higher = audio.change_pitch(semitones=2.0)

    assert higher.sample_rate == audio.sample_rate
    assert higher.duration == audio.duration  # Duration should be preserved

    # Pitch shifted audio should have different waveform
    assert not np.array_equal(higher.data, audio.data)

    # Shift pitch down by 2 semitones
    lower = audio.change_pitch(semitones=-2.0)

    assert lower.sample_rate == audio.sample_rate
    assert lower.duration == audio.duration  # Duration should be preserved

    # Pitch shifted audio should have different waveform
    assert not np.array_equal(lower.data, audio.data)
