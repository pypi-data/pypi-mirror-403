"""Manifest generation - ties all outputs together."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def build_manifest(
    video_path: Path | str,
    video_info: dict,
    frames: list[Path],
    audio_analysis: dict | None = None,
    has_spectrogram: bool = False,
    has_waveform: bool = False,
) -> dict:
    """
    Build a manifest dictionary that describes all outputs.

    This function returns the manifest as a dictionary without writing to disk,
    making it suitable for both file-based and MCP server usage.

    Args:
        video_path: Original video path
        video_info: Video metadata from frames.get_video_info()
        frames: List of extracted frame paths
        audio_analysis: Audio analysis dict (optional)
        has_spectrogram: Whether spectrogram was generated
        has_waveform: Whether waveform was generated

    Returns:
        Dictionary containing the complete manifest
    """
    video_path = Path(video_path)

    # Calculate frame timestamps
    duration = video_info["duration"]
    num_frames = len(frames)
    frame_interval = duration / num_frames if num_frames > 0 else 0

    frame_info = []
    for i, frame_path in enumerate(frames):
        timestamp = i * frame_interval
        frame_info.append({
            "filename": frame_path.name,
            "index": i + 1,
            "timestamp_seconds": round(timestamp, 2),
            "timestamp_formatted": _format_timestamp(timestamp)
        })

    manifest = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "generator": "video-to-claude",

        "source": {
            "filename": video_path.name,
            "path": str(video_path.absolute()),
        },

        "video": {
            "duration_seconds": round(duration, 2),
            "duration_formatted": _format_timestamp(duration),
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "width": video_info["width"],
            "height": video_info["height"],
            "fps": round(video_info["fps"], 2),
            "codec": video_info["codec"],
        },

        "frames": {
            "count": num_frames,
            "interval_seconds": round(frame_interval, 2),
            "files": frame_info,
        },

        "audio": {
            "available": video_info.get("has_audio", False),
        },

        "files": {
            "manifest": "manifest.json",
            "frames": [f["filename"] for f in frame_info],
        },

        "viewing_instructions": _generate_viewing_instructions(num_frames, duration, audio_analysis),
    }

    # Add audio info if available
    if audio_analysis:
        manifest["audio"]["codec"] = video_info.get("audio_codec")
        manifest["audio"]["sample_rate"] = video_info.get("audio_sample_rate")
        manifest["audio"]["characteristics"] = audio_analysis.get("overall_characteristics", {})
        manifest["audio"]["frequency_analysis"] = audio_analysis.get("frequency_analysis", {})
        manifest["audio"]["description"] = audio_analysis.get("text_description", "")
        manifest["files"]["audio_analysis"] = "audio_analysis.json"

    if has_spectrogram:
        manifest["files"]["spectrogram"] = "spectrogram.png"

    if has_waveform:
        manifest["files"]["waveform"] = "waveform.png"

    return manifest


def generate_manifest(
    video_path: Path | str,
    output_dir: Path | str,
    video_info: dict,
    frames: list[Path],
    audio_analysis: dict | None = None,
    has_spectrogram: bool = False,
    has_waveform: bool = False,
) -> Path:
    """
    Generate a manifest.json file that describes all outputs.

    Args:
        video_path: Original video path
        output_dir: Output directory
        video_info: Video metadata from frames.get_video_info()
        frames: List of extracted frame paths
        audio_analysis: Audio analysis dict (optional)
        has_spectrogram: Whether spectrogram was generated
        has_waveform: Whether waveform was generated

    Returns:
        Path to the manifest file
    """
    output_dir = Path(output_dir)

    manifest = build_manifest(
        video_path=video_path,
        video_info=video_info,
        frames=frames,
        audio_analysis=audio_analysis,
        has_spectrogram=has_spectrogram,
        has_waveform=has_waveform,
    )

    # Write manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


def _format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    else:
        return f"{minutes}:{secs:05.2f}"


def _generate_viewing_instructions(num_frames: int, duration: float, audio_analysis: dict | None) -> str:
    """Generate instructions for Claude on how to experience this video."""
    instructions = []

    instructions.append(f"This video has been converted into {num_frames} sequential frames spanning {duration:.1f} seconds.")
    instructions.append(f"To experience the video, view the frames in order (frame_001.jpg through frame_{num_frames:03d}.jpg).")
    instructions.append("Each frame represents a moment in time - together they show motion and change.")

    if audio_analysis:
        instructions.append("")
        instructions.append("Audio information is provided via spectrogram.png (visual frequency representation), ")
        instructions.append("waveform.png (amplitude over time), and audio_analysis.json (detailed data).")
        instructions.append(f"Audio summary: {audio_analysis.get('text_description', 'No description available.')}")

    return " ".join(instructions)
