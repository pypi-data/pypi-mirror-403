"""Core video processing functionality."""

from .processor import VideoProcessor
from .frames import get_video_info, extract_frames, extract_frames_at_times
from .audio import extract_audio, generate_spectrogram, generate_waveform, analyze_audio
from .manifest import generate_manifest, build_manifest

__all__ = [
    "VideoProcessor",
    "get_video_info",
    "extract_frames",
    "extract_frames_at_times",
    "extract_audio",
    "generate_spectrogram",
    "generate_waveform",
    "analyze_audio",
    "generate_manifest",
    "build_manifest",
]
