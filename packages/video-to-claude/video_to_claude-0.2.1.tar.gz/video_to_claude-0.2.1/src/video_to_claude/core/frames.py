"""Frame extraction from video files using ffmpeg."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def get_video_info(video_path: Path | str) -> dict:
    """
    Get video metadata using ffprobe.

    Args:
        video_path: Path to the input video

    Returns:
        Dictionary with video metadata including:
        - duration: Video duration in seconds
        - width: Video width in pixels
        - height: Video height in pixels
        - fps: Frames per second
        - codec: Video codec name
        - has_audio: Whether video has an audio track
        - audio_codec: Audio codec name (if has_audio)
        - audio_sample_rate: Audio sample rate (if has_audio)
    """
    video_path = Path(video_path)

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Find video stream
    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    if video_stream is None:
        raise RuntimeError("No video stream found")

    duration = float(data.get("format", {}).get("duration", 0))

    # Parse frame rate safely (avoid eval)
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, denom = fps_str.split("/")
        fps = float(num) / float(denom)
    else:
        fps = float(fps_str)

    return {
        "duration": duration,
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "fps": fps,
        "codec": video_stream.get("codec_name"),
        "has_audio": audio_stream is not None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
    }


def extract_frames(
    video_path: Path | str,
    output_dir: Path | str,
    num_frames: int = 20
) -> list[Path]:
    """
    Extract evenly-spaced frames from a video.

    Args:
        video_path: Path to the input video
        output_dir: Directory to save frames
        num_frames: Number of frames to extract

    Returns:
        List of paths to extracted frame images
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get video info to calculate frame interval
    info = get_video_info(video_path)
    total_frames = int(info["duration"] * info["fps"])

    # Calculate which frames to extract (evenly spaced)
    frame_interval = max(1, total_frames // num_frames)

    # Use ffmpeg select filter to extract specific frames
    output_pattern = output_dir / "frame_%03d.jpg"

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"select='not(mod(n\\,{frame_interval}))'",
        "-vsync", "vfr",
        "-frames:v", str(num_frames),
        "-q:v", "2",  # High quality JPEG
        str(output_pattern),
        "-y"  # Overwrite
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed: {result.stderr}")

    # Return list of created frame paths
    frames = sorted(output_dir.glob("frame_*.jpg"))
    return frames


def extract_frames_at_times(
    video_path: Path | str,
    output_dir: Path | str,
    times: list[float]
) -> list[Path]:
    """
    Extract frames at specific timestamps.

    Args:
        video_path: Path to the input video
        output_dir: Directory to save frames
        times: List of timestamps in seconds

    Returns:
        List of paths to extracted frame images
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = []

    for i, t in enumerate(times, 1):
        output_path = output_dir / f"frame_{i:03d}.jpg"
        cmd = [
            "ffmpeg",
            "-ss", str(t),
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",
            str(output_path),
            "-y"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed at time {t}: {result.stderr}")

        frames.append(output_path)

    return frames
