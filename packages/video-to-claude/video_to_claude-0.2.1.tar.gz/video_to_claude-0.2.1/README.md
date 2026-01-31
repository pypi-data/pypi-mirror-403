# video-to-claude

Translate video files into a format Claude can experience.

Claude can't watch videos, but it can view images and read data. This tool extracts sequential frames, generates spectrograms, and produces audio analysis - everything Claude needs to "experience" your video.

[![PyPI](https://img.shields.io/pypi/v/video-to-claude)](https://pypi.org/project/video-to-claude/)
[![Python Version](https://img.shields.io/pypi/pyversions/video-to-claude)](https://pypi.org/project/video-to-claude/)
[![License](https://img.shields.io/pypi/l/video-to-claude)](https://github.com/lemonyte/video-to-claude/blob/main/LICENSE)

## Quick Start

```bash
# 1. Install dependencies
brew install ffmpeg  # macOS (or apt install ffmpeg on Ubuntu/Debian)
pip install video-to-claude[mcp]

# 2. Convert a video
video-to-claude convert ~/Videos/my_video.mp4

# 3. Upload to share with Claude
video-to-claude upload ~/Videos/my_video_for_claude --name "My Video"

# 4. Access via MCP server in Claude Desktop (see setup below)
```

## Installation

```bash
# Requires ffmpeg
brew install ffmpeg  # macOS
apt install ffmpeg   # Ubuntu/Debian

# Install the tool
pip install video-to-claude[mcp]
```

## MCP Server Setup

### Local MCP Server (Claude Code)

Process videos locally on your machine:

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

**Available Tools:**

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

### Remote MCP Server (Access Uploaded Videos)

Access your uploaded videos from anywhere using the remote MCP server at `https://api.ai-media-tools.dev`:

```json
{
  "mcpServers": {
    "video-to-claude-remote": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://api.ai-media-tools.dev/mcp"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your-github-token-here"
      }
    }
  }
}
```

**Authentication Required:** The remote MCP endpoint requires a Bearer token. Use the token you received during upload authentication, or get a new one:

```bash
# Get your token
video-to-claude upload --get-token
```

**Available Tools:**

| Tool | Description |
|------|-------------|
| `list_videos` | List all your uploaded videos |
| `get_manifest` | Get video manifest and metadata |
| `get_frame` | View a specific frame |
| `get_frames` | View multiple frames |
| `get_spectrogram` | View audio frequency visualization |
| `get_waveform` | View audio amplitude visualization |
| `get_audio_analysis` | Get detailed audio metrics |

## CLI Usage

### Convert Videos

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

### Upload and Share Videos

Upload processed videos to share them with Claude or access them from anywhere:

```bash
# Upload a processed video (uses GitHub OAuth)
video-to-claude upload ~/Videos/my_video_for_claude --name "My Video"
```

**Authentication Flow:**

1. First upload opens your browser for GitHub authentication
2. Authorize the app to get a token
3. Token is saved automatically for future uploads
4. Set `VIDEO_TO_CLAUDE_TOKEN` environment variable to use the same token across sessions

**Direct Upload (Advanced):**

If you have R2 credentials, you can upload directly without authentication:

```bash
# Set environment variables
export CLOUDFLARE_ACCOUNT_ID=your-account-id
export CLOUDFLARE_R2_ACCESS_KEY_ID=your-access-key
export CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret-key

# Upload with --direct flag
video-to-claude upload ~/Videos/my_video_for_claude --name "My Video" --direct
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

## Troubleshooting

### Authentication Issues

**Browser doesn't open or callback hangs:**
- Check if port 8765 is available: `lsof -i :8765`
- Try using the `--token` flag with an existing token
- Check firewall settings for localhost connections

**Already have a token?** Skip the browser flow:
```bash
video-to-claude upload ./output --name "Video" --token YOUR_TOKEN
# Or set it as an environment variable
export VIDEO_TO_CLAUDE_TOKEN="your-token"
```

### Upload Issues

**"error code: 1010" during upload:**

This typically means a required header is missing. Ensure you're using the latest version:
```bash
pip install --upgrade video-to-claude
```

### Processing Issues

**ffmpeg not found:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

## Why?

Videos contain moments worth sharing - a pet's greeting, a child's first steps, a sunset. Claude can understand these moments through sequential frames and audio analysis, experiencing the motion and sound in its own way.

This tool is a codec for Claude.

## License

MIT
