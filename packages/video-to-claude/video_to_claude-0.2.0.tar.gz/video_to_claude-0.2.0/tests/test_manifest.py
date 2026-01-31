"""Tests for manifest generation functionality."""

import json
from pathlib import Path

import pytest

from video_to_claude.core.manifest import (
    build_manifest,
    generate_manifest,
    _format_timestamp,
)


class TestBuildManifest:
    """Tests for build_manifest function."""

    def test_build_manifest_returns_dict(self):
        """Test that build_manifest returns a dictionary."""
        video_info = {
            "duration": 10.0,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [Path("frame_001.jpg"), Path("frame_002.jpg")]

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
        )

        assert isinstance(manifest, dict)

    def test_build_manifest_has_required_keys(self):
        """Test that manifest contains required keys."""
        video_info = {
            "duration": 10.0,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [Path("frame_001.jpg")]

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
        )

        assert "version" in manifest
        assert "generated_at" in manifest
        assert "generator" in manifest
        assert "source" in manifest
        assert "video" in manifest
        assert "frames" in manifest
        assert "audio" in manifest
        assert "files" in manifest
        assert "viewing_instructions" in manifest

    def test_build_manifest_video_info(self):
        """Test that video information is correctly included."""
        video_info = {
            "duration": 120.5,
            "width": 1920,
            "height": 1080,
            "fps": 29.97,
            "codec": "h264",
            "has_audio": True,
            "audio_codec": "aac",
            "audio_sample_rate": 48000,
        }
        frames = [Path("frame_001.jpg")]

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
        )

        assert manifest["video"]["duration_seconds"] == 120.5
        assert manifest["video"]["width"] == 1920
        assert manifest["video"]["height"] == 1080
        assert manifest["video"]["resolution"] == "1920x1080"
        assert manifest["video"]["codec"] == "h264"

    def test_build_manifest_frame_info(self):
        """Test that frame information is correctly calculated."""
        video_info = {
            "duration": 10.0,
            "width": 320,
            "height": 240,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [
            Path("frame_001.jpg"),
            Path("frame_002.jpg"),
            Path("frame_003.jpg"),
            Path("frame_004.jpg"),
            Path("frame_005.jpg"),
        ]

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
        )

        assert manifest["frames"]["count"] == 5
        assert manifest["frames"]["interval_seconds"] == 2.0

        frame_list = manifest["frames"]["files"]
        assert len(frame_list) == 5
        assert frame_list[0]["index"] == 1
        assert frame_list[0]["timestamp_seconds"] == 0.0
        assert frame_list[4]["index"] == 5
        assert frame_list[4]["timestamp_seconds"] == 8.0

    def test_build_manifest_with_audio_analysis(self):
        """Test manifest with audio analysis included."""
        video_info = {
            "duration": 10.0,
            "width": 320,
            "height": 240,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": True,
            "audio_codec": "aac",
            "audio_sample_rate": 44100,
        }
        frames = [Path("frame_001.jpg")]
        audio_analysis = {
            "overall_characteristics": {"rms_energy": 0.15},
            "frequency_analysis": {"spectral_centroid_hz": 1000},
            "text_description": "Test audio description",
        }

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
            audio_analysis=audio_analysis,
            has_spectrogram=True,
            has_waveform=True,
        )

        assert manifest["audio"]["available"] is True
        assert manifest["audio"]["codec"] == "aac"
        assert "characteristics" in manifest["audio"]
        assert "frequency_analysis" in manifest["audio"]
        assert manifest["audio"]["description"] == "Test audio description"
        assert manifest["files"]["spectrogram"] == "spectrogram.png"
        assert manifest["files"]["waveform"] == "waveform.png"

    def test_build_manifest_json_serializable(self):
        """Test that manifest can be serialized to JSON."""
        video_info = {
            "duration": 10.0,
            "width": 320,
            "height": 240,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [Path("frame_001.jpg")]

        manifest = build_manifest(
            video_path=Path("/test/video.mp4"),
            video_info=video_info,
            frames=frames,
        )

        # Should not raise
        json_str = json.dumps(manifest)
        assert len(json_str) > 0


class TestGenerateManifest:
    """Tests for generate_manifest function."""

    def test_generate_manifest_creates_file(self, temp_dir):
        """Test that generate_manifest creates a file."""
        video_info = {
            "duration": 10.0,
            "width": 320,
            "height": 240,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [Path("frame_001.jpg")]

        manifest_path = generate_manifest(
            video_path=Path("/test/video.mp4"),
            output_dir=temp_dir,
            video_info=video_info,
            frames=frames,
        )

        assert manifest_path.exists()
        assert manifest_path.name == "manifest.json"

    def test_generate_manifest_valid_json(self, temp_dir):
        """Test that generated manifest is valid JSON."""
        video_info = {
            "duration": 10.0,
            "width": 320,
            "height": 240,
            "fps": 30.0,
            "codec": "h264",
            "has_audio": False,
        }
        frames = [Path("frame_001.jpg")]

        manifest_path = generate_manifest(
            video_path=Path("/test/video.mp4"),
            output_dir=temp_dir,
            video_info=video_info,
            frames=frames,
        )

        with open(manifest_path) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert data["version"] == "1.0"


class TestFormatTimestamp:
    """Tests for _format_timestamp helper function."""

    def test_format_under_minute(self):
        """Test formatting for times under a minute."""
        assert _format_timestamp(0) == "0:00.00"
        assert _format_timestamp(30.5) == "0:30.50"
        assert _format_timestamp(59.99) == "0:59.99"

    def test_format_minutes(self):
        """Test formatting for times with minutes."""
        assert _format_timestamp(60) == "1:00.00"
        assert _format_timestamp(90.5) == "1:30.50"
        assert _format_timestamp(599) == "9:59.00"

    def test_format_hours(self):
        """Test formatting for times with hours."""
        assert _format_timestamp(3600) == "1:00:00.00"
        assert _format_timestamp(3661.5) == "1:01:01.50"
        assert _format_timestamp(7200) == "2:00:00.00"
