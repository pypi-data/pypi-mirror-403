"""Tests for frame extraction functionality."""

import pytest

from video_to_claude.core.frames import (
    get_video_info,
    extract_frames,
    extract_frames_at_times,
)


class TestGetVideoInfo:
    """Tests for get_video_info function."""

    def test_get_video_info_returns_metadata(self, test_video):
        """Test that video info contains expected fields."""
        info = get_video_info(test_video)

        assert "duration" in info
        assert "width" in info
        assert "height" in info
        assert "fps" in info
        assert "codec" in info
        assert "has_audio" in info

    def test_get_video_info_correct_values(self, test_video):
        """Test that video info values are reasonable."""
        info = get_video_info(test_video)

        assert info["duration"] > 0
        assert info["width"] == 320
        assert info["height"] == 240
        assert info["fps"] > 0
        assert info["has_audio"] is True

    def test_get_video_info_no_audio(self, test_video_no_audio):
        """Test video info for video without audio."""
        info = get_video_info(test_video_no_audio)

        assert info["has_audio"] is False
        assert info["audio_codec"] is None

    def test_get_video_info_nonexistent_file(self, temp_dir):
        """Test that nonexistent file raises error."""
        with pytest.raises(RuntimeError):
            get_video_info(temp_dir / "nonexistent.mp4")


class TestExtractFrames:
    """Tests for extract_frames function."""

    def test_extract_frames_returns_list(self, test_video, output_dir):
        """Test that extract_frames returns a list of paths."""
        frames = extract_frames(test_video, output_dir, num_frames=5)

        assert isinstance(frames, list)
        assert len(frames) > 0

    def test_extract_frames_creates_files(self, test_video, output_dir):
        """Test that frame files are actually created."""
        frames = extract_frames(test_video, output_dir, num_frames=5)

        for frame in frames:
            assert frame.exists()
            assert frame.suffix == ".jpg"

    def test_extract_frames_correct_count(self, test_video, output_dir):
        """Test that requested number of frames are extracted."""
        frames = extract_frames(test_video, output_dir, num_frames=3)

        # May get fewer frames than requested for short videos
        assert len(frames) <= 3
        assert len(frames) > 0

    def test_extract_frames_naming(self, test_video, output_dir):
        """Test that frames are named correctly."""
        frames = extract_frames(test_video, output_dir, num_frames=5)

        for i, frame in enumerate(frames, 1):
            assert f"frame_{i:03d}.jpg" == frame.name

    def test_extract_frames_creates_output_dir(self, test_video, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        output = temp_dir / "new_output_dir"
        assert not output.exists()

        extract_frames(test_video, output, num_frames=3)

        assert output.exists()
        assert output.is_dir()


class TestExtractFramesAtTimes:
    """Tests for extract_frames_at_times function."""

    def test_extract_at_specific_times(self, test_video, output_dir):
        """Test extracting frames at specific timestamps."""
        times = [0.0, 1.0, 2.0]
        frames = extract_frames_at_times(test_video, output_dir, times)

        assert len(frames) == 3

        for frame in frames:
            assert frame.exists()
            assert frame.suffix == ".jpg"

    def test_extract_at_times_naming(self, test_video, output_dir):
        """Test that frames are named sequentially."""
        times = [0.5, 1.5]
        frames = extract_frames_at_times(test_video, output_dir, times)

        assert frames[0].name == "frame_001.jpg"
        assert frames[1].name == "frame_002.jpg"
