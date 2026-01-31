"""Tests for audio extraction and analysis functionality."""

import json

import pytest

from video_to_claude.core.audio import (
    extract_audio,
    generate_spectrogram,
    generate_waveform,
    analyze_audio,
)


class TestExtractAudio:
    """Tests for extract_audio function."""

    def test_extract_audio_creates_wav(self, test_video, output_dir):
        """Test that audio extraction creates a WAV file."""
        audio_path = output_dir / "audio.wav"
        result = extract_audio(test_video, audio_path)

        assert result == audio_path
        assert audio_path.exists()
        assert audio_path.suffix == ".wav"

    def test_extract_audio_nonzero_size(self, test_video, output_dir):
        """Test that extracted audio file is not empty."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        assert audio_path.stat().st_size > 0

    def test_extract_audio_no_audio_track(self, test_video_no_audio, output_dir):
        """Test extraction from video without audio."""
        audio_path = output_dir / "audio.wav"

        # ffmpeg should still create a file but may fail
        # This behavior depends on ffmpeg version
        with pytest.raises(RuntimeError):
            extract_audio(test_video_no_audio, audio_path)


class TestGenerateSpectrogram:
    """Tests for generate_spectrogram function."""

    def test_generate_spectrogram_creates_png(self, test_video, output_dir):
        """Test that spectrogram generation creates a PNG file."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        spectrogram_path = output_dir / "spectrogram.png"
        result = generate_spectrogram(audio_path, spectrogram_path)

        assert result == spectrogram_path
        assert spectrogram_path.exists()
        assert spectrogram_path.suffix == ".png"

    def test_generate_spectrogram_nonzero_size(self, test_video, output_dir):
        """Test that spectrogram image has content."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        spectrogram_path = output_dir / "spectrogram.png"
        generate_spectrogram(audio_path, spectrogram_path)

        # PNG files should be reasonably sized
        assert spectrogram_path.stat().st_size > 1000


class TestGenerateWaveform:
    """Tests for generate_waveform function."""

    def test_generate_waveform_creates_png(self, test_video, output_dir):
        """Test that waveform generation creates a PNG file."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        waveform_path = output_dir / "waveform.png"
        result = generate_waveform(audio_path, waveform_path)

        assert result == waveform_path
        assert waveform_path.exists()
        assert waveform_path.suffix == ".png"

    def test_generate_waveform_nonzero_size(self, test_video, output_dir):
        """Test that waveform image has content."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        waveform_path = output_dir / "waveform.png"
        generate_waveform(audio_path, waveform_path)

        assert waveform_path.stat().st_size > 1000


class TestAnalyzeAudio:
    """Tests for analyze_audio function."""

    def test_analyze_audio_returns_dict(self, test_video, output_dir):
        """Test that audio analysis returns a dictionary."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)

        assert isinstance(analysis, dict)

    def test_analyze_audio_has_required_keys(self, test_video, output_dir):
        """Test that analysis contains expected keys."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)

        assert "metadata" in analysis
        assert "overall_characteristics" in analysis
        assert "frequency_analysis" in analysis
        assert "temporal_analysis" in analysis
        assert "notable_events" in analysis
        assert "text_description" in analysis

    def test_analyze_audio_metadata(self, test_video, output_dir):
        """Test that metadata contains expected fields."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)
        metadata = analysis["metadata"]

        assert "sample_rate" in metadata
        assert "duration_seconds" in metadata
        assert "total_samples" in metadata
        assert metadata["sample_rate"] == 44100  # We extract at 44100 Hz

    def test_analyze_audio_characteristics(self, test_video, output_dir):
        """Test overall characteristics values."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)
        chars = analysis["overall_characteristics"]

        assert "rms_energy" in chars
        assert "peak_amplitude" in chars
        assert "dynamic_range_db" in chars
        assert "zero_crossing_rate" in chars

        # Values should be in expected ranges
        assert 0 <= chars["rms_energy"] <= 1
        assert 0 <= chars["peak_amplitude"] <= 1

    def test_analyze_audio_frequency_bands(self, test_video, output_dir):
        """Test frequency band analysis."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)
        freq = analysis["frequency_analysis"]

        assert "frequency_band_energy_percent" in freq
        assert "spectral_centroid_hz" in freq

        bands = freq["frequency_band_energy_percent"]
        # Should have all standard bands
        assert "sub_bass_20_60hz" in bands
        assert "bass_60_250hz" in bands
        assert "mid_500_2000hz" in bands

        # Total should be approximately 100%
        total = sum(bands.values())
        assert 99 <= total <= 101

    def test_analyze_audio_text_description(self, test_video, output_dir):
        """Test that text description is generated."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)

        assert isinstance(analysis["text_description"], str)
        assert len(analysis["text_description"]) > 0

    def test_analyze_audio_json_serializable(self, test_video, output_dir):
        """Test that analysis can be serialized to JSON."""
        audio_path = output_dir / "audio.wav"
        extract_audio(test_video, audio_path)

        analysis = analyze_audio(audio_path)

        # Should not raise
        json_str = json.dumps(analysis)
        assert len(json_str) > 0
