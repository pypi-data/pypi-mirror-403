"""Tests for local MCP server functionality."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMCPServerTools:
    """Tests for MCP server tool implementations."""

    def test_convert_video_tool(self, test_video, output_dir):
        """Test convert_video tool function."""
        from video_to_claude.mcp_server import _convert_video

        result = _convert_video(
            path=str(test_video),
            frames=5,
            include_audio=True,
            output_dir=str(output_dir),
        )

        assert isinstance(result, dict)
        assert "error" not in result
        assert "version" in result
        assert "video" in result
        assert "frames" in result

        # Check processing info
        assert "_processing" in result
        assert result["_processing"]["frame_count"] > 0

    def test_convert_video_nonexistent(self, temp_dir):
        """Test convert_video with nonexistent file."""
        from video_to_claude.mcp_server import _convert_video

        result = _convert_video(
            path=str(temp_dir / "nonexistent.mp4"),
            frames=5,
        )

        assert "error" in result

    def test_get_video_info_tool(self, test_video):
        """Test get_video_info_tool function."""
        from video_to_claude.mcp_server import _get_video_info

        result = _get_video_info(str(test_video))

        assert isinstance(result, dict)
        assert "error" not in result
        assert "duration" in result
        assert "width" in result
        assert "height" in result

    def test_get_video_info_nonexistent(self, temp_dir):
        """Test get_video_info_tool with nonexistent file."""
        from video_to_claude.mcp_server import _get_video_info

        result = _get_video_info(str(temp_dir / "nonexistent.mp4"))

        assert "error" in result

    def test_view_frame(self, test_video, output_dir):
        """Test view_frame tool function."""
        from video_to_claude.mcp_server import _convert_video, _view_frame

        # First process the video
        _convert_video(
            path=str(test_video),
            frames=5,
            include_audio=False,
            output_dir=str(output_dir),
        )

        # Then view a frame
        result = _view_frame(str(output_dir), 1)

        # Should return an Image object
        from fastmcp.utilities.types import Image
        assert isinstance(result, Image)

    def test_view_frame_invalid(self, test_video, output_dir):
        """Test view_frame with invalid frame number."""
        from video_to_claude.mcp_server import _convert_video, _view_frame

        # First process the video
        _convert_video(
            path=str(test_video),
            frames=3,
            include_audio=False,
            output_dir=str(output_dir),
        )

        # Try to view non-existent frame
        with pytest.raises(ValueError) as exc:
            _view_frame(str(output_dir), 999)

        assert "not found" in str(exc.value).lower()

    def test_get_manifest_tool(self, test_video, output_dir):
        """Test get_manifest tool function."""
        from video_to_claude.mcp_server import _convert_video, _get_manifest

        # First process the video
        _convert_video(
            path=str(test_video),
            frames=5,
            include_audio=False,
            output_dir=str(output_dir),
        )

        result = _get_manifest(str(output_dir))

        assert isinstance(result, dict)
        assert "version" in result
        assert "video" in result

    def test_get_audio_analysis_tool(self, test_video, output_dir):
        """Test get_audio_analysis tool function."""
        from video_to_claude.mcp_server import _convert_video, _get_audio_analysis

        # Process with audio
        _convert_video(
            path=str(test_video),
            frames=3,
            include_audio=True,
            output_dir=str(output_dir),
        )

        result = _get_audio_analysis(str(output_dir))

        assert isinstance(result, dict)
        assert "metadata" in result
        assert "overall_characteristics" in result

    def test_view_spectrogram(self, test_video, output_dir):
        """Test view_spectrogram tool function."""
        from video_to_claude.mcp_server import _convert_video, _view_spectrogram

        # Process with audio
        _convert_video(
            path=str(test_video),
            frames=3,
            include_audio=True,
            output_dir=str(output_dir),
        )

        result = _view_spectrogram(str(output_dir))

        from fastmcp.utilities.types import Image
        assert isinstance(result, Image)

    def test_view_waveform(self, test_video, output_dir):
        """Test view_waveform tool function."""
        from video_to_claude.mcp_server import _convert_video, _view_waveform

        # Process with audio
        _convert_video(
            path=str(test_video),
            frames=3,
            include_audio=True,
            output_dir=str(output_dir),
        )

        result = _view_waveform(str(output_dir))

        from fastmcp.utilities.types import Image
        assert isinstance(result, Image)

    def test_view_all_frames(self, test_video, output_dir):
        """Test view_all_frames tool function."""
        from video_to_claude.mcp_server import _convert_video, _view_all_frames

        # Process video
        _convert_video(
            path=str(test_video),
            frames=5,
            include_audio=False,
            output_dir=str(output_dir),
        )

        result = _view_all_frames(str(output_dir), max_frames=3)

        assert isinstance(result, list)
        assert len(result) <= 3

        from fastmcp.utilities.types import Image
        for item in result:
            assert isinstance(item, Image)


class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    def test_mcp_server_creation(self):
        """Test that MCP server can be created."""
        from video_to_claude.mcp_server import mcp

        assert mcp is not None
        assert mcp.name == "video-to-claude"

    def test_tools_registered(self):
        """Test that tools are registered with the server."""
        from video_to_claude.mcp_server import mcp

        # The server should have tools available
        # This tests that the decorators worked
        assert hasattr(mcp, '_tool_manager') or hasattr(mcp, 'tools')
