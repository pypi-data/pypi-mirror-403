"""VideoProcessor - main orchestrator for video-to-claude conversion."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .frames import get_video_info, extract_frames
from .audio import extract_audio, generate_spectrogram, generate_waveform, analyze_audio
from .manifest import build_manifest, generate_manifest


@dataclass
class ProcessingResult:
    """Result of video processing operation."""

    manifest: dict
    """The manifest dictionary describing the processed video."""

    output_dir: Path
    """Directory containing all output files."""

    frames: list[Path]
    """List of paths to extracted frame images."""

    spectrogram: Path | None = None
    """Path to spectrogram image, if generated."""

    waveform: Path | None = None
    """Path to waveform image, if generated."""

    audio_analysis: dict | None = None
    """Audio analysis dictionary, if generated."""

    manifest_path: Path | None = None
    """Path to manifest.json file, if written to disk."""


@dataclass
class VideoProcessor:
    """
    Processes videos into Claude-friendly formats.

    This class orchestrates the extraction of frames, audio analysis,
    and manifest generation from video files.

    Example:
        processor = VideoProcessor(num_frames=20, include_audio=True)
        result = processor.process("/path/to/video.mp4")
        print(result.manifest)
    """

    num_frames: int = 20
    """Number of frames to extract from the video."""

    include_audio: bool = True
    """Whether to extract and analyze audio."""

    output_dir: Path | None = None
    """Output directory. If None, creates based on video name."""

    write_files: bool = True
    """Whether to write output files to disk."""

    _video_info: dict = field(default_factory=dict, init=False)
    """Cached video information."""

    def get_info(self, video_path: Path | str) -> dict:
        """
        Get video metadata without processing.

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary with video metadata
        """
        video_path = Path(video_path)
        return get_video_info(video_path)

    def process(
        self,
        video_path: Path | str,
        output_dir: Path | str | None = None,
        num_frames: int | None = None,
        include_audio: bool | None = None,
    ) -> ProcessingResult:
        """
        Process a video file into Claude-friendly formats.

        Args:
            video_path: Path to the video file
            output_dir: Override output directory (uses instance default if None)
            num_frames: Override number of frames (uses instance default if None)
            include_audio: Override audio processing (uses instance default if None)

        Returns:
            ProcessingResult containing all outputs and metadata
        """
        video_path = Path(video_path).resolve()

        # Use provided values or fall back to instance defaults
        num_frames = num_frames if num_frames is not None else self.num_frames
        include_audio = include_audio if include_audio is not None else self.include_audio

        # Determine output directory
        if output_dir is not None:
            out_dir = Path(output_dir).resolve()
        elif self.output_dir is not None:
            out_dir = self.output_dir
        else:
            out_dir = Path.cwd() / f"{video_path.stem}_for_claude"

        out_dir.mkdir(parents=True, exist_ok=True)

        # Get video info
        video_info = get_video_info(video_path)
        self._video_info = video_info

        # Extract frames
        frames = extract_frames(video_path, out_dir, num_frames)

        # Process audio if requested and available
        audio_analysis = None
        spectrogram_path = None
        waveform_path = None

        if include_audio and video_info.get("has_audio"):
            audio_path = out_dir / "audio.wav"
            extract_audio(video_path, audio_path)

            if audio_path.exists():
                # Generate visualizations
                spectrogram_path = out_dir / "spectrogram.png"
                generate_spectrogram(audio_path, spectrogram_path)

                waveform_path = out_dir / "waveform.png"
                generate_waveform(audio_path, waveform_path)

                # Analyze audio
                audio_analysis = analyze_audio(audio_path)

                # Save audio analysis
                if self.write_files:
                    with open(out_dir / "audio_analysis.json", "w") as f:
                        json.dump(audio_analysis, f, indent=2)

        # Build manifest
        manifest = build_manifest(
            video_path=video_path,
            video_info=video_info,
            frames=frames,
            audio_analysis=audio_analysis,
            has_spectrogram=spectrogram_path is not None,
            has_waveform=waveform_path is not None,
        )

        # Write manifest if requested
        manifest_path = None
        if self.write_files:
            manifest_path = out_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

        return ProcessingResult(
            manifest=manifest,
            output_dir=out_dir,
            frames=frames,
            spectrogram=spectrogram_path,
            waveform=waveform_path,
            audio_analysis=audio_analysis,
            manifest_path=manifest_path,
        )

    def process_to_memory(
        self,
        video_path: Path | str,
        num_frames: int | None = None,
        include_audio: bool | None = None,
    ) -> ProcessingResult:
        """
        Process a video file into memory (using temp directory).

        This is useful for MCP servers that need to return data directly
        without creating permanent files in a user-specified location.

        Args:
            video_path: Path to the video file
            num_frames: Override number of frames (uses instance default if None)
            include_audio: Override audio processing (uses instance default if None)

        Returns:
            ProcessingResult with files in a temporary directory
        """
        # Use a temporary directory for output
        temp_dir = tempfile.mkdtemp(prefix="video_to_claude_")

        return self.process(
            video_path=video_path,
            output_dir=temp_dir,
            num_frames=num_frames,
            include_audio=include_audio,
        )
