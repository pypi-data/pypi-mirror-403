"""Tests for VideoProcessor class."""

import json

import pytest

from video_to_claude.core import VideoProcessor


class TestVideoProcessor:
    """Tests for VideoProcessor class."""

    def test_processor_initialization(self):
        """Test processor can be initialized with defaults."""
        processor = VideoProcessor()

        assert processor.num_frames == 20
        assert processor.include_audio is True
        assert processor.write_files is True

    def test_processor_custom_settings(self):
        """Test processor can be initialized with custom settings."""
        processor = VideoProcessor(
            num_frames=10,
            include_audio=False,
            write_files=False,
        )

        assert processor.num_frames == 10
        assert processor.include_audio is False
        assert processor.write_files is False

    def test_get_info(self, test_video):
        """Test getting video info without processing."""
        processor = VideoProcessor()
        info = processor.get_info(test_video)

        assert "duration" in info
        assert "width" in info
        assert "height" in info

    def test_process_returns_result(self, test_video, output_dir):
        """Test that process returns a ProcessingResult."""
        processor = VideoProcessor(num_frames=5)
        result = processor.process(test_video, output_dir=output_dir)

        assert result is not None
        # Use resolve() for both paths to handle macOS /var -> /private/var symlink
        assert result.output_dir.resolve() == output_dir.resolve()
        assert result.manifest is not None
        assert len(result.frames) > 0

    def test_process_creates_frames(self, test_video, output_dir):
        """Test that process creates frame files."""
        processor = VideoProcessor(num_frames=5)
        result = processor.process(test_video, output_dir=output_dir)

        for frame in result.frames:
            assert frame.exists()
            assert frame.suffix == ".jpg"

    def test_process_creates_manifest(self, test_video, output_dir):
        """Test that process creates manifest file."""
        processor = VideoProcessor(num_frames=3)
        result = processor.process(test_video, output_dir=output_dir)

        assert result.manifest_path is not None
        assert result.manifest_path.exists()

        with open(result.manifest_path) as f:
            data = json.load(f)

        assert data["version"] == "1.0"

    def test_process_with_audio(self, test_video, output_dir):
        """Test processing with audio analysis."""
        processor = VideoProcessor(num_frames=3, include_audio=True)
        result = processor.process(test_video, output_dir=output_dir)

        assert result.spectrogram is not None
        assert result.spectrogram.exists()

        assert result.waveform is not None
        assert result.waveform.exists()

        assert result.audio_analysis is not None
        assert "metadata" in result.audio_analysis

    def test_process_without_audio(self, test_video, output_dir):
        """Test processing without audio analysis."""
        processor = VideoProcessor(num_frames=3, include_audio=False)
        result = processor.process(test_video, output_dir=output_dir)

        assert result.spectrogram is None
        assert result.waveform is None
        assert result.audio_analysis is None

    def test_process_override_settings(self, test_video, output_dir):
        """Test that process arguments override instance settings."""
        processor = VideoProcessor(num_frames=20, include_audio=True)
        result = processor.process(
            test_video,
            output_dir=output_dir,
            num_frames=3,
            include_audio=False,
        )

        # Should have used the overridden values
        assert len(result.frames) <= 3
        assert result.audio_analysis is None

    def test_process_auto_output_dir(self, test_video, temp_dir):
        """Test that output directory is auto-generated."""
        import os
        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)
            processor = VideoProcessor(num_frames=3)
            result = processor.process(test_video)

            expected_name = f"{test_video.stem}_for_claude"
            assert result.output_dir.name == expected_name
            assert result.output_dir.exists()
        finally:
            os.chdir(original_cwd)

    def test_process_to_memory(self, test_video):
        """Test processing to temporary directory."""
        processor = VideoProcessor(num_frames=3, include_audio=False)
        result = processor.process_to_memory(test_video)

        assert result.output_dir.exists()
        assert len(result.frames) > 0

        # Should be in a temp directory
        assert "video_to_claude" in str(result.output_dir)

    def test_manifest_structure(self, test_video, output_dir):
        """Test that manifest has expected structure."""
        processor = VideoProcessor(num_frames=5)
        result = processor.process(test_video, output_dir=output_dir)

        manifest = result.manifest

        # Check required sections
        assert "source" in manifest
        assert "video" in manifest
        assert "frames" in manifest
        assert "files" in manifest

        # Check video info
        assert "duration_seconds" in manifest["video"]
        assert "resolution" in manifest["video"]

        # Check frames info
        assert "count" in manifest["frames"]
        assert "files" in manifest["frames"]
        assert len(manifest["frames"]["files"]) == manifest["frames"]["count"]

    def test_nonexistent_video(self, temp_dir):
        """Test processing nonexistent video raises error."""
        processor = VideoProcessor()

        with pytest.raises(RuntimeError):
            processor.process(temp_dir / "nonexistent.mp4")
