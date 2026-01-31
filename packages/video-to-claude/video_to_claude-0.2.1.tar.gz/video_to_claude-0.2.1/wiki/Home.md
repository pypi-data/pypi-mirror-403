# video-to-claude

**Help Claude experience videos through frames, audio analysis, and spectrograms.**

Claude can't watch videos directly, but it can view images and analyze data. This tool converts videos into a format Claude can understand - extracting key frames, generating audio visualizations, and creating a manifest that ties it all together.

---

## What It Does

When you process a video, video-to-claude creates:

| Output | Description |
|--------|-------------|
| **Frames** | Sequential images extracted at regular intervals |
| **Spectrogram** | Visual representation of audio frequencies over time |
| **Waveform** | Audio amplitude visualization |
| **Audio Analysis** | JSON data with frequency bands, energy levels, notable events |
| **Manifest** | JSON file describing everything, with viewing instructions |

Claude can then "experience" the video by viewing frames in sequence and understanding the audio through visualizations and data.

---

## Quick Install

```bash
# Install from PyPI
pip install video-to-claude

# Also need ffmpeg (for video processing)
brew install ffmpeg  # macOS
# or: apt install ffmpeg  # Ubuntu/Debian
```

---

## Two Ways to Use

### 1. Command Line (CLI)

Process videos directly from your terminal:

```bash
video-to-claude convert ~/Videos/my-video.mp4
```

This creates a `my-video_for_claude/` directory with all the outputs.

### 2. Claude Integration (MCP)

Let Claude process and view videos directly:

- **Claude Code** - Local MCP server with full processing capabilities
- **Claude.ai** - Remote MCP server for viewing uploaded videos

---

## Documentation

- **[Getting Started](Getting-Started)** - Installation and your first video
- **[CLI Reference](CLI-Reference)** - All commands and options
- **[Claude Code Setup](Claude-Code-Setup)** - Local MCP integration
- **[Claude.ai Setup](Claude-AI-Setup)** - Remote MCP connector
- **[YouTube & URLs](YouTube-and-URLs)** - Processing online videos
- **[Uploading Videos](Uploading-Videos)** - Share videos to the cloud
- **[Troubleshooting](Troubleshooting)** - Common issues and fixes

---

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Video File  │────▶│ video-to-claude  │────▶│ Claude-Ready    │
│ or URL      │     │ (ffmpeg + scipy) │     │ Output          │
└─────────────┘     └──────────────────┘     └─────────────────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    │                                │                                │
                    ▼                                ▼                                ▼
             ┌─────────────┐                 ┌──────────────┐                ┌──────────────┐
             │ 20 Frames   │                 │ Spectrogram  │                │ manifest.json│
             │ (JPG)       │                 │ + Waveform   │                │ (metadata)   │
             └─────────────┘                 └──────────────┘                └──────────────┘
```

---

## Example Output

After processing a 30-second video:

```
wilson_for_claude/
├── manifest.json          # Video metadata + viewing instructions
├── frame_001.jpg          # Frames at regular intervals
├── frame_002.jpg
├── ...
├── frame_020.jpg
├── spectrogram.png        # Audio frequency visualization
├── waveform.png           # Audio amplitude visualization
└── audio_analysis.json    # Detailed audio data
```

The manifest tells Claude:
- Video duration, resolution, FPS
- What each frame represents (timestamp)
- Audio characteristics (dominant frequencies, energy levels)
- How to "view" the video (frame sequence + audio context)

---

## Links

- [PyPI Package](https://pypi.org/project/video-to-claude/)
- [GitHub Repository](https://github.com/anthropics/video-to-claude)
- [Report Issues](https://github.com/anthropics/video-to-claude/issues)
