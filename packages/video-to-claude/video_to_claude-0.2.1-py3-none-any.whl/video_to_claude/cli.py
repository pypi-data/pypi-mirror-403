"""Command-line interface for video-to-claude."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .core import VideoProcessor
from .core.frames import get_video_info
from .core.audio import extract_audio, generate_spectrogram, generate_waveform, analyze_audio
from .core.manifest import generate_manifest
from .download import download_video, is_youtube_url


def is_url(s: str) -> bool:
    """Check if string is a URL."""
    return s.startswith(("http://", "https://"))


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Convert video files into a format Claude can experience.

    This tool extracts frames, analyzes audio, and generates a manifest
    that helps Claude understand video content.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("convert")
@click.argument("video", type=str)
@click.option(
    "--frames", "-f",
    default=20,
    help="Number of frames to extract (default: 20)"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: <video_name>_for_claude/)"
)
@click.option(
    "--no-audio",
    is_flag=True,
    help="Skip audio extraction and analysis"
)
def convert(video: str, frames: int, output: Path | None, no_audio: bool):
    """
    Convert a video file or URL into a format Claude can experience.

    VIDEO is the path to a video file or a URL (YouTube, direct video links).
    """
    # Check if it's a URL
    if is_url(video):
        click.echo(f"Downloading: {video}")
        if is_youtube_url(video):
            click.echo("(YouTube video detected, using yt-dlp)")
        try:
            video_path = download_video(video)
            click.echo(f"Downloaded to: {video_path}")
            click.echo()
        except ImportError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except RuntimeError as e:
            click.echo(f"Download failed: {e}", err=True)
            sys.exit(1)
    else:
        video_path = Path(video)
        if not video_path.exists():
            click.echo(f"Error: File not found: {video}", err=True)
            sys.exit(1)

    video_path = video_path.resolve()

    # Determine output directory
    if output is None:
        output = Path.cwd() / f"{video_path.stem}_for_claude"
    output = output.resolve()

    click.echo(f"Processing: {video_path.name}")
    click.echo(f"Output: {output}/")
    click.echo()

    # Get video info
    click.echo("Analyzing video... ", nl=False)
    try:
        video_info = get_video_info(video_path)
        click.echo(f"done ({video_info['duration']:.1f}s, {video_info['width']}x{video_info['height']})")
    except Exception as e:
        click.echo(f"failed: {e}", err=True)
        sys.exit(1)

    # Use VideoProcessor for the rest
    processor = VideoProcessor(
        num_frames=frames,
        include_audio=not no_audio,
        output_dir=output,
    )

    try:
        result = processor.process(video_path)

        # Summary
        click.echo()
        click.echo(click.style("Success!", fg="green", bold=True))
        click.echo()
        click.echo("To experience this video, ask Claude to read:")
        click.echo(f"  {result.manifest_path}")
        click.echo()
        click.echo("Or view all files in:")
        click.echo(f"  {result.output_dir}/")

    except Exception as e:
        click.echo(f"failed: {e}", err=True)
        sys.exit(1)


@main.command("info")
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info(video: Path, as_json: bool):
    """
    Show video metadata without processing.

    VIDEO is the path to the input video file.
    """
    video = video.resolve()

    try:
        video_info = get_video_info(video)

        if as_json:
            click.echo(json.dumps(video_info, indent=2))
        else:
            click.echo(f"File: {video.name}")
            click.echo(f"Duration: {video_info['duration']:.2f}s")
            click.echo(f"Resolution: {video_info['width']}x{video_info['height']}")
            click.echo(f"FPS: {video_info['fps']:.2f}")
            click.echo(f"Codec: {video_info['codec']}")
            click.echo(f"Has Audio: {video_info['has_audio']}")
            if video_info['has_audio']:
                click.echo(f"Audio Codec: {video_info['audio_codec']}")
                click.echo(f"Audio Sample Rate: {video_info['audio_sample_rate']} Hz")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("upload")
@click.argument("output_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--name", "-n", required=True, help="Name for the video in cloud storage")
@click.option("--token", "-t", envvar="VIDEO_TO_CLAUDE_TOKEN", help="OAuth token (or set VIDEO_TO_CLAUDE_TOKEN)")
@click.option("--direct", is_flag=True, help="Upload directly to R2 (requires credentials)")
@click.option("--bucket", "-b", default="video-to-claude-storage", help="R2 bucket name (for --direct)")
def upload(output_dir: Path, name: str, token: str | None, direct: bool, bucket: str):
    """
    Upload processed video output to the cloud.

    OUTPUT_DIR is the directory containing the processed video files
    (must include manifest.json).

    By default, uploads via the hosted server with GitHub authentication.
    Use --direct to upload directly to R2 (requires credentials).
    """
    output_dir = output_dir.resolve()

    # Check for manifest
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        click.echo("Error: No manifest.json found in directory", err=True)
        click.echo("Run 'video-to-claude convert' first to process the video", err=True)
        sys.exit(1)

    if direct:
        # Direct R2 upload (requires credentials)
        try:
            from .upload import upload_to_r2
        except ImportError:
            click.echo("Error: Direct upload requires the 'upload' extra", err=True)
            click.echo("Install with: pip install video-to-claude[upload]", err=True)
            sys.exit(1)

        try:
            click.echo(f"Uploading directly to R2 bucket '{bucket}'...")
            video_id = upload_to_r2(output_dir, name, bucket)
            click.echo()
            click.echo(click.style("Success!", fg="green", bold=True))
            click.echo(f"Video ID: {video_id}")
            click.echo()
            click.echo("Your video is now accessible via the remote MCP server.")
        except Exception as e:
            click.echo(f"Upload failed: {e}", err=True)
            sys.exit(1)
    else:
        # Upload via worker API (no R2 credentials needed)
        from .upload import upload_via_worker, get_auth_token, DEFAULT_SERVER_URL

        try:
            # Get token if not provided
            if not token:
                click.echo("No token provided. Starting GitHub authentication...")
                click.echo()
                token = get_auth_token()
                click.echo()
                click.echo("Authentication successful!")
                click.echo(f"Tip: Set VIDEO_TO_CLAUDE_TOKEN={token} to skip auth next time")
                click.echo()

            click.echo(f"Uploading '{name}'...")
            result = upload_via_worker(output_dir, name, token)

            click.echo()
            click.echo(click.style("Success!", fg="green", bold=True))
            click.echo(f"Video ID: {result['video_id']}")
            click.echo(f"Files uploaded: {len(result['files'])}")
            click.echo()
            click.echo("Your video is now accessible via the remote MCP server.")
            click.echo(f"Server: {DEFAULT_SERVER_URL}")

        except Exception as e:
            click.echo(f"Upload failed: {e}", err=True)
            sys.exit(1)


# For backwards compatibility, also support direct invocation without subcommand
@click.command("video-to-claude-legacy")
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--frames", "-f",
    default=20,
    help="Number of frames to extract (default: 20)"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: <video_name>_for_claude/)"
)
@click.option(
    "--no-audio",
    is_flag=True,
    help="Skip audio extraction and analysis"
)
def legacy_main(video: Path, frames: int, output: Path | None, no_audio: bool):
    """
    Convert a video file into a format Claude can experience.

    VIDEO is the path to the input video file.

    This is the legacy command format. Consider using 'video-to-claude convert' instead.
    """
    video = video.resolve()

    # Determine output directory
    if output is None:
        output = Path.cwd() / f"{video.stem}_for_claude"
    output = output.resolve()

    click.echo(f"Processing: {video.name}")
    click.echo(f"Output: {output}/")
    click.echo()

    # Get video info
    click.echo("Analyzing video... ", nl=False)
    try:
        video_info = get_video_info(video)
        click.echo(f"done ({video_info['duration']:.1f}s, {video_info['width']}x{video_info['height']})")
    except Exception as e:
        click.echo(f"failed: {e}", err=True)
        sys.exit(1)

    # Extract frames
    from .core.frames import extract_frames
    click.echo(f"Extracting {frames} frames... ", nl=False)
    try:
        frame_paths = extract_frames(video, output, frames)
        click.echo(f"done ({len(frame_paths)} frames)")
    except Exception as e:
        click.echo(f"failed: {e}", err=True)
        sys.exit(1)

    # Audio processing
    audio_analysis = None
    has_spectrogram = False
    has_waveform = False

    if not no_audio and video_info.get("has_audio"):
        # Extract audio
        click.echo("Extracting audio... ", nl=False)
        try:
            audio_path = extract_audio(video, output / "audio.wav")
            click.echo("done")
        except Exception as e:
            click.echo(f"failed: {e}", err=True)
            audio_path = None

        if audio_path and audio_path.exists():
            # Generate spectrogram
            click.echo("Generating spectrogram... ", nl=False)
            try:
                generate_spectrogram(audio_path, output / "spectrogram.png")
                has_spectrogram = True
                click.echo("done")
            except Exception as e:
                click.echo(f"failed: {e}", err=True)

            # Generate waveform
            click.echo("Generating waveform... ", nl=False)
            try:
                generate_waveform(audio_path, output / "waveform.png")
                has_waveform = True
                click.echo("done")
            except Exception as e:
                click.echo(f"failed: {e}", err=True)

            # Analyze audio
            click.echo("Analyzing audio... ", nl=False)
            try:
                audio_analysis = analyze_audio(audio_path)
                # Save audio analysis
                with open(output / "audio_analysis.json", "w") as f:
                    json.dump(audio_analysis, f, indent=2)
                click.echo("done")
            except Exception as e:
                click.echo(f"failed: {e}", err=True)

    elif no_audio:
        click.echo("Skipping audio (--no-audio)")
    else:
        click.echo("No audio track found")

    # Generate manifest
    click.echo("Writing manifest... ", nl=False)
    try:
        manifest_path = generate_manifest(
            video_path=video,
            output_dir=output,
            video_info=video_info,
            frames=frame_paths,
            audio_analysis=audio_analysis,
            has_spectrogram=has_spectrogram,
            has_waveform=has_waveform,
        )
        click.echo("done")
    except Exception as e:
        click.echo(f"failed: {e}", err=True)
        sys.exit(1)

    # Summary
    click.echo()
    click.echo(click.style("Success!", fg="green", bold=True))
    click.echo()
    click.echo("To experience this video, ask Claude to read:")
    click.echo(f"  {manifest_path}")
    click.echo()
    click.echo("Or view all files in:")
    click.echo(f"  {output}/")


if __name__ == "__main__":
    main()
