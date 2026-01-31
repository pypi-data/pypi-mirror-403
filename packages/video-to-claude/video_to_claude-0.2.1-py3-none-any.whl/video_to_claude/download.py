"""Download videos from URLs (direct links and YouTube via yt-dlp)."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube video URL."""
    youtube_patterns = [
        r'(youtube\.com/watch\?v=)',
        r'(youtu\.be/)',
        r'(youtube\.com/embed/)',
        r'(youtube\.com/v/)',
        r'(youtube\.com/shorts/)',
    ]
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def download_video(url: str, output_dir: Path | str | None = None) -> Path:
    """
    Download a video from a URL.

    Supports:
    - Direct video URLs (.mp4, .mov, .avi, .mkv, .webm, etc.)
    - YouTube URLs (requires yt-dlp)

    Args:
        url: URL of the video to download
        output_dir: Directory to save the video. If None, uses a temp directory.

    Returns:
        Path to the downloaded video file.

    Raises:
        RuntimeError: If download fails
        ImportError: If yt-dlp is needed but not installed
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="video_to_claude_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if is_youtube_url(url):
        return _download_youtube(url, output_dir)
    else:
        return _download_direct(url, output_dir)


def _download_youtube(url: str, output_dir: Path) -> Path:
    """Download video from YouTube using yt-dlp."""
    # Check if yt-dlp is available
    if shutil.which("yt-dlp") is None:
        raise ImportError(
            "yt-dlp is required for YouTube downloads. "
            "Install with: pip install yt-dlp"
        )

    # Generate output filename based on URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    output_template = str(output_dir / f"video_{url_hash}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--output", output_template,
        "--no-playlist",  # Don't download playlists
        "--quiet",
        "--no-warnings",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    # Find the downloaded file
    downloaded = list(output_dir.glob(f"video_{url_hash}.*"))
    if not downloaded:
        raise RuntimeError("Download completed but no file found")

    return downloaded[0]


def _download_direct(url: str, output_dir: Path) -> Path:
    """Download video from a direct URL."""
    parsed = urlparse(url)

    # Get filename from URL or generate one
    path_parts = parsed.path.split("/")
    filename = path_parts[-1] if path_parts else None

    # Check if filename has a video extension
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}

    if filename:
        ext = Path(filename).suffix.lower()
        if ext not in video_extensions:
            filename = None

    if not filename:
        # Generate filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"video_{url_hash}.mp4"

    output_path = output_dir / filename

    try:
        # Download with progress
        urllib.request.urlretrieve(url, output_path)
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Download completed but file is empty")

    return output_path


def get_video_id_from_youtube_url(url: str) -> str | None:
    """Extract video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[?&]|$)',
        r'(?:youtu\.be/)([0-9A-Za-z_-]{11})',
        r'(?:embed/)([0-9A-Za-z_-]{11})',
        r'(?:shorts/)([0-9A-Za-z_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None
