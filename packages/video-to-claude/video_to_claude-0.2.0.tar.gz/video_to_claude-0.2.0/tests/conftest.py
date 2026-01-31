"""Pytest fixtures for video-to-claude tests."""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_video(temp_dir):
    """Create a small test video using ffmpeg."""
    video_path = temp_dir / "test_video.mp4"

    # Create a 3-second test video with color bars and a beep
    # This uses ffmpeg's built-in test sources
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "testsrc=duration=3:size=320x240:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=3",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-b:a", "128k",
        str(video_path),
        "-y"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.skip(f"Could not create test video: {result.stderr}")

    return video_path


@pytest.fixture
def test_video_no_audio(temp_dir):
    """Create a test video without audio."""
    video_path = temp_dir / "test_video_no_audio.mp4"

    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "testsrc=duration=2:size=320x240:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        str(video_path),
        "-y"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.skip(f"Could not create test video: {result.stderr}")

    return video_path


@pytest.fixture
def output_dir(temp_dir):
    """Create an output directory for processed files."""
    output = temp_dir / "output"
    output.mkdir()
    return output
