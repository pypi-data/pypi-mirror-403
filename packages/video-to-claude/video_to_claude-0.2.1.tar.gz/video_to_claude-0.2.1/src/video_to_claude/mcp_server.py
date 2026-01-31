"""Local MCP server for video-to-claude (stdio transport)."""

from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from .core import VideoProcessor
from .core.frames import get_video_info
from .download import download_video, is_youtube_url


def is_url(s: str) -> bool:
    """Check if string is a URL."""
    return s.startswith(("http://", "https://"))

# Create the MCP server
mcp = FastMCP(
    name="video-to-claude",
    instructions="""
    This MCP server converts videos into a format you can experience.

    Use convert_video to process a video file or URL (including YouTube) -
    it will extract frames, analyze audio, and create a manifest.

    Use get_video_info to get metadata about a video without processing it.

    Use view_frame to see a specific frame from a processed video.

    Use view_spectrogram to see the audio spectrogram visualization.

    Both convert_video and get_video_info accept:
    - Local file paths: /path/to/video.mp4
    - YouTube URLs: https://www.youtube.com/watch?v=...
    - Direct video URLs: https://example.com/video.mp4
    """
)


# ============================================================================
# Internal implementation functions (testable directly)
# ============================================================================

def _convert_video(
    path: str,
    frames: int = 20,
    include_audio: bool = True,
    output_dir: str | None = None,
) -> dict:
    """
    Process a video file or URL into a format Claude can experience.

    This extracts frames, analyzes audio, generates visualizations,
    and creates a manifest describing everything.

    Args:
        path: Path to the video file OR a URL (YouTube, direct video links)
        frames: Number of frames to extract (default: 20)
        include_audio: Whether to extract and analyze audio (default: True)
        output_dir: Optional output directory. If not provided, creates
                    <video_name>_for_claude/ in the current directory.

    Returns:
        The manifest dictionary containing all video information and
        paths to the generated files.
    """
    # Handle URLs - download first
    if is_url(path):
        try:
            video_path = download_video(path)
        except ImportError as e:
            return {"error": f"URL download requires yt-dlp: {e}"}
        except RuntimeError as e:
            return {"error": f"Download failed: {e}"}
    else:
        video_path = Path(path).resolve()
        if not video_path.exists():
            return {"error": f"Video file not found: {video_path}"}

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir).resolve()
    else:
        out_dir = video_path.parent / f"{video_path.stem}_for_claude"

    processor = VideoProcessor(
        num_frames=frames,
        include_audio=include_audio,
        output_dir=out_dir,
        write_files=True,
    )

    try:
        result = processor.process(video_path)

        # Add file paths to the response
        manifest = result.manifest.copy()
        manifest["_processing"] = {
            "output_dir": str(result.output_dir),
            "manifest_path": str(result.manifest_path) if result.manifest_path else None,
            "frame_count": len(result.frames),
            "has_spectrogram": result.spectrogram is not None,
            "has_waveform": result.waveform is not None,
            "has_audio_analysis": result.audio_analysis is not None,
        }

        return manifest

    except Exception as e:
        return {"error": str(e)}


def _get_video_info(path: str) -> dict:
    """
    Get metadata about a video file or URL without processing it.

    Args:
        path: Path to the video file OR a URL (YouTube, direct video links)

    Returns:
        Dictionary containing video metadata:
        - duration: Duration in seconds
        - width, height: Resolution
        - fps: Frames per second
        - codec: Video codec
        - has_audio: Whether video has audio
        - audio_codec: Audio codec (if has_audio)
        - audio_sample_rate: Audio sample rate (if has_audio)
    """
    # Handle URLs - download first
    if is_url(path):
        try:
            video_path = download_video(path)
        except ImportError as e:
            return {"error": f"URL download requires yt-dlp: {e}"}
        except RuntimeError as e:
            return {"error": f"Download failed: {e}"}
    else:
        video_path = Path(path).resolve()
        if not video_path.exists():
            return {"error": f"Video file not found: {video_path}"}

    try:
        info = get_video_info(video_path)
        return info
    except Exception as e:
        return {"error": str(e)}


def _view_frame(output_dir: str, frame_number: int) -> Image:
    """
    View a specific frame from a processed video.

    Args:
        output_dir: Path to the output directory containing processed video
        frame_number: Frame number to view (1-indexed, e.g., 1 for first frame)

    Returns:
        The frame image.
    """
    out_dir = Path(output_dir).resolve()

    frame_path = out_dir / f"frame_{frame_number:03d}.jpg"

    if not frame_path.exists():
        # Try to list available frames
        available = sorted(out_dir.glob("frame_*.jpg"))
        if available:
            frame_nums = [int(f.stem.split("_")[1]) for f in available]
            raise ValueError(
                f"Frame {frame_number} not found. "
                f"Available frames: {min(frame_nums)}-{max(frame_nums)}"
            )
        else:
            raise ValueError(f"No frames found in {out_dir}")

    return Image(path=str(frame_path))


def _view_spectrogram(output_dir: str) -> Image:
    """
    View the audio spectrogram from a processed video.

    The spectrogram shows frequency content over time, with:
    - X-axis: Time (seconds)
    - Y-axis: Frequency (Hz, 0-8000 range)
    - Color: Power/intensity (dB)

    Args:
        output_dir: Path to the output directory containing processed video

    Returns:
        The spectrogram image.
    """
    out_dir = Path(output_dir).resolve()
    spectrogram_path = out_dir / "spectrogram.png"

    if not spectrogram_path.exists():
        raise ValueError(
            f"No spectrogram found in {out_dir}. "
            "Make sure audio was included when processing."
        )

    return Image(path=str(spectrogram_path))


def _view_waveform(output_dir: str) -> Image:
    """
    View the audio waveform from a processed video.

    The waveform shows amplitude over time:
    - X-axis: Time (seconds)
    - Y-axis: Amplitude (-1 to 1, normalized)

    Args:
        output_dir: Path to the output directory containing processed video

    Returns:
        The waveform image.
    """
    out_dir = Path(output_dir).resolve()
    waveform_path = out_dir / "waveform.png"

    if not waveform_path.exists():
        raise ValueError(
            f"No waveform found in {out_dir}. "
            "Make sure audio was included when processing."
        )

    return Image(path=str(waveform_path))


def _get_audio_analysis(output_dir: str) -> dict:
    """
    Get detailed audio analysis from a processed video.

    Args:
        output_dir: Path to the output directory containing processed video

    Returns:
        Dictionary containing:
        - metadata: sample_rate, duration, total_samples
        - overall_characteristics: RMS energy, peak amplitude, etc.
        - frequency_analysis: energy distribution across frequency bands
        - temporal_analysis: per-second energy breakdown
        - notable_events: detected energy changes
        - text_description: human-readable summary
    """
    out_dir = Path(output_dir).resolve()
    analysis_path = out_dir / "audio_analysis.json"

    if not analysis_path.exists():
        raise ValueError(
            f"No audio analysis found in {out_dir}. "
            "Make sure audio was included when processing."
        )

    with open(analysis_path) as f:
        return json.load(f)


def _get_manifest(output_dir: str) -> dict:
    """
    Get the manifest from a processed video.

    The manifest contains all information about the processed video:
    - Source video metadata
    - Frame list with timestamps
    - Audio analysis summary
    - File list
    - Viewing instructions

    Args:
        output_dir: Path to the output directory containing processed video

    Returns:
        The manifest dictionary.
    """
    out_dir = Path(output_dir).resolve()
    manifest_path = out_dir / "manifest.json"

    if not manifest_path.exists():
        raise ValueError(
            f"No manifest found in {out_dir}. "
            "This directory may not contain a processed video."
        )

    with open(manifest_path) as f:
        return json.load(f)


def _view_all_frames(output_dir: str, max_frames: int = 10) -> list[Image]:
    """
    View multiple frames from a processed video at once.

    This returns up to max_frames evenly distributed across the video.
    Use this to get an overview of the video content.

    Args:
        output_dir: Path to the output directory containing processed video
        max_frames: Maximum number of frames to return (default: 10, max: 20)

    Returns:
        List of frame images.
    """
    out_dir = Path(output_dir).resolve()

    # Get all available frames
    available = sorted(out_dir.glob("frame_*.jpg"))

    if not available:
        raise ValueError(f"No frames found in {out_dir}")

    # Limit max_frames to reasonable amount (Claude has 1MB limit per response)
    max_frames = min(max_frames, 20)

    # Select evenly distributed frames
    if len(available) <= max_frames:
        selected = available
    else:
        step = len(available) / max_frames
        indices = [int(i * step) for i in range(max_frames)]
        selected = [available[i] for i in indices]

    return [Image(path=str(frame)) for frame in selected]


# ============================================================================
# MCP Tool wrappers (these delegate to internal functions)
# ============================================================================

@mcp.tool
def convert_video(
    path: str,
    frames: int = 20,
    include_audio: bool = True,
    output_dir: str | None = None,
) -> dict:
    """Process a video file or URL (including YouTube) into a format Claude can experience."""
    return _convert_video(path, frames, include_audio, output_dir)


@mcp.tool
def get_video_info_tool(path: str) -> dict:
    """Get metadata about a video file or URL without processing it."""
    return _get_video_info(path)


@mcp.tool
def view_frame(output_dir: str, frame_number: int) -> Image:
    """View a specific frame from a processed video."""
    return _view_frame(output_dir, frame_number)


@mcp.tool
def view_spectrogram(output_dir: str) -> Image:
    """View the audio spectrogram from a processed video."""
    return _view_spectrogram(output_dir)


@mcp.tool
def view_waveform(output_dir: str) -> Image:
    """View the audio waveform from a processed video."""
    return _view_waveform(output_dir)


@mcp.tool
def get_audio_analysis(output_dir: str) -> dict:
    """Get detailed audio analysis from a processed video."""
    return _get_audio_analysis(output_dir)


@mcp.tool
def get_manifest(output_dir: str) -> dict:
    """Get the manifest from a processed video."""
    return _get_manifest(output_dir)


@mcp.tool
def view_all_frames(output_dir: str, max_frames: int = 10) -> list[Image]:
    """View multiple frames from a processed video at once."""
    return _view_all_frames(output_dir, max_frames)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
