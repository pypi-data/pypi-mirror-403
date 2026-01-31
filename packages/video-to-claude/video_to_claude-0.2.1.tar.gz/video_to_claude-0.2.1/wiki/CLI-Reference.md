# CLI Reference

Complete reference for all video-to-claude commands.

---

## Commands Overview

| Command | Description |
|---------|-------------|
| `convert` | Process a video file or URL |
| `info` | Show video metadata without processing |
| `upload` | Upload processed output to the cloud |

---

## convert

Process a video file or URL into a format Claude can experience.

### Usage

```bash
video-to-claude convert VIDEO [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `VIDEO` | Path to video file, YouTube URL, or direct video URL |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--frames` | `-f` | 20 | Number of frames to extract |
| `--output` | `-o` | `<video>_for_claude/` | Output directory |
| `--no-audio` | | False | Skip audio extraction and analysis |

### Examples

**Basic conversion:**
```bash
video-to-claude convert ~/Videos/my-video.mp4
```

**YouTube video:**
```bash
video-to-claude convert "https://www.youtube.com/watch?v=VIDEO_ID"
```

**YouTube Short:**
```bash
video-to-claude convert "https://www.youtube.com/shorts/VIDEO_ID"
```

**Custom frame count:**
```bash
# Fewer frames (faster, smaller)
video-to-claude convert video.mp4 -f 10

# More frames (more detail)
video-to-claude convert video.mp4 -f 50
```

**Custom output location:**
```bash
video-to-claude convert video.mp4 -o ~/claude-videos/my-video/
```

**Skip audio (video-only):**
```bash
video-to-claude convert video.mp4 --no-audio
```

### Output Structure

```
video_for_claude/
├── manifest.json          # Main metadata file
├── frame_001.jpg          # First frame (timestamp: 0:00)
├── frame_002.jpg          # Second frame
├── ...
├── frame_020.jpg          # Last frame
├── spectrogram.png        # Audio frequency visualization
├── waveform.png           # Audio amplitude visualization
└── audio_analysis.json    # Detailed audio data
```

---

## info

Show video metadata without processing the video.

### Usage

```bash
video-to-claude info VIDEO [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `VIDEO` | Path to video file |

### Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON instead of human-readable format |

### Examples

**Human-readable output:**
```bash
video-to-claude info ~/Videos/my-video.mp4
```

Output:
```
File: my-video.mp4
Duration: 30.52s
Resolution: 1920x1080
FPS: 30.00
Codec: h264
Has Audio: True
Audio Codec: aac
Audio Sample Rate: 48000 Hz
```

**JSON output:**
```bash
video-to-claude info ~/Videos/my-video.mp4 --json
```

Output:
```json
{
  "duration": 30.52,
  "width": 1920,
  "height": 1080,
  "fps": 30.0,
  "codec": "h264",
  "has_audio": true,
  "audio_codec": "aac",
  "audio_sample_rate": 48000
}
```

---

## upload

Upload processed video output to the cloud for access from anywhere.

### Usage

```bash
video-to-claude upload OUTPUT_DIR --name NAME [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `OUTPUT_DIR` | Directory containing processed video (must have manifest.json) |

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | **Required.** Name for the video in cloud storage |
| `--token` | `-t` | OAuth token (or set `VIDEO_TO_CLAUDE_TOKEN` env var) |
| `--direct` | | Upload directly to R2 (requires credentials) |
| `--bucket` | `-b` | R2 bucket name (for `--direct` mode) |

### Examples

**Standard upload (recommended):**
```bash
video-to-claude upload ./my-video_for_claude/ --name "My Awesome Video"
```

This will:
1. Open your browser for GitHub authentication (first time only)
2. Upload all files to the cloud
3. Return a video ID you can use in claude.ai

**With saved token:**
```bash
# Save token to avoid re-authenticating
export VIDEO_TO_CLAUDE_TOKEN=your-token-here

video-to-claude upload ./my-video_for_claude/ --name "My Video"
```

**Direct R2 upload (advanced):**
```bash
# Requires R2 credentials
export CLOUDFLARE_ACCOUNT_ID=your-account-id
export CLOUDFLARE_R2_ACCESS_KEY_ID=your-key
export CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret

video-to-claude upload ./my-video_for_claude/ --name "My Video" --direct
```

### Authentication

The default upload flow uses GitHub OAuth:

1. First upload opens your browser to authenticate
2. You authorize with GitHub
3. Token is returned and can be saved for future uploads

Set `VIDEO_TO_CLAUDE_TOKEN` environment variable to skip authentication on subsequent uploads.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VIDEO_TO_CLAUDE_TOKEN` | OAuth token for uploads (avoids re-authenticating) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID (for `--direct` uploads) |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` | R2 access key (for `--direct` uploads) |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | R2 secret key (for `--direct` uploads) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, processing failed, etc.) |

---

## Tips

### Processing Speed

- Frame extraction is usually fast
- Audio analysis can take time for long videos
- Use `--no-audio` if you only need visual content
- Use fewer frames (`-f 10`) for quick previews

### Video Formats

video-to-claude supports any format ffmpeg can read:
- MP4, MOV, AVI, MKV, WebM
- Most codecs (H.264, H.265, VP9, AV1, etc.)

### File Sizes

Output size depends on:
- Number of frames
- Video resolution (frames are JPEGs at original resolution)
- Audio length (affects spectrogram/waveform size)

Typical output: 2-10 MB for a 30-second video with 20 frames.
