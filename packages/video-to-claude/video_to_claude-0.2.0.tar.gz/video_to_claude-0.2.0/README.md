# video-to-claude

Translate video files into a format Claude can experience.

Claude can't watch videos, but it can view images and read data. This tool extracts sequential frames, generates spectrograms, and produces audio analysis - everything Claude needs to "experience" your video.

## Installation

```bash
# Requires ffmpeg
brew install ffmpeg  # macOS
apt install ffmpeg   # Ubuntu/Debian

# Install the tool
pip install video-to-claude[mcp]
```

## MCP Server Setup (Claude Code)

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "video-to-claude": {
      "command": "video-to-claude-mcp"
    }
  }
}
```

Then ask Claude:
- "Convert the video at ~/Videos/wilson.mov"
- "Show me frame 10"
- "What does the audio look like?"

### Available Tools

| Tool | Description |
|------|-------------|
| `convert_video` | Process a video into frames + audio analysis |
| `get_video_info` | Get video metadata without processing |
| `view_frame` | View a specific frame |
| `view_all_frames` | View multiple frames at once |
| `view_spectrogram` | View audio frequency visualization |
| `view_waveform` | View audio amplitude visualization |
| `get_audio_analysis` | Get detailed audio metrics |
| `get_manifest` | Get the full manifest |

## CLI Usage

```bash
# Convert a video (20 frames + audio analysis)
video-to-claude convert ~/Videos/my_video.mp4

# Custom frame count
video-to-claude convert ~/Videos/my_video.mp4 --frames 30

# Skip audio analysis
video-to-claude convert ~/Videos/my_video.mp4 --no-audio

# Get video info
video-to-claude info ~/Videos/my_video.mp4
```

## Output

```
my_video_for_claude/
├── manifest.json          # Metadata and viewing instructions
├── frame_001.jpg          # Sequential frames
├── frame_002.jpg
├── ...
├── spectrogram.png        # Audio frequency visualization
├── waveform.png           # Audio amplitude visualization
└── audio_analysis.json    # Detailed audio metrics
```

## Why?

Videos contain moments worth sharing - a pet's greeting, a child's first steps, a sunset. Claude can understand these moments through sequential frames and audio analysis, experiencing the motion and sound in its own way.

This tool is a codec for Claude.

## License

MIT
