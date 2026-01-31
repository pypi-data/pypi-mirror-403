# Claude Code Setup

Integrate video-to-claude directly into Claude Code so you can process and view videos without leaving the conversation.

---

## Overview

When configured, Claude Code gains these capabilities:

| Tool | Description |
|------|-------------|
| `convert_video` | Process a video file or URL into Claude-ready format |
| `get_video_info` | Get video metadata without processing |
| `view_frame` | View a specific frame from processed video |
| `view_all_frames` | View multiple frames at once |
| `view_spectrogram` | View audio frequency visualization |
| `view_waveform` | View audio amplitude visualization |
| `get_audio_analysis` | Get detailed audio analysis data |
| `get_manifest` | Get the full video manifest |

---

## Quick Setup

### Step 1: Install the Package

```bash
pip install video-to-claude
```

### Step 2: Add MCP Server to Claude Code

```bash
claude mcp add video-to-claude video-to-claude-mcp
```

### Step 3: Restart Claude Code

Close and reopen Claude Code (or start a new session) to load the MCP server.

### Step 4: Test It

Ask Claude:

> "Convert this video: /path/to/my-video.mp4"

or

> "Convert this YouTube video: https://www.youtube.com/shorts/VIDEO_ID"

---

## Detailed Setup

### Using a Virtual Environment

If you installed video-to-claude in a virtual environment:

```bash
# Find your venv's path to the MCP server
which video-to-claude-mcp
# Example output: /Users/you/myenv/bin/video-to-claude-mcp

# Add with full path
claude mcp add video-to-claude /Users/you/myenv/bin/video-to-claude-mcp
```

### Manual Configuration

You can also edit the Claude Code config directly. The config file is typically at:
- macOS: `~/.claude.json`
- Linux: `~/.claude.json`
- Windows: `%USERPROFILE%\.claude.json`

Add this to your config:

```json
{
  "mcpServers": {
    "video-to-claude": {
      "command": "video-to-claude-mcp"
    }
  }
}
```

Or with a full path:

```json
{
  "mcpServers": {
    "video-to-claude": {
      "command": "/full/path/to/video-to-claude-mcp"
    }
  }
}
```

### Verifying Setup

After restarting Claude Code, you can verify the MCP server is loaded:

```bash
claude mcp list
```

You should see `video-to-claude` in the list.

---

## Usage Examples

### Converting a Local Video

**You:** Convert this video: ~/Downloads/my-cat.mp4

**Claude:** *Uses `convert_video` tool, processes the video, returns manifest with output location*

### Converting a YouTube Video

**You:** Process this YouTube short: https://www.youtube.com/shorts/abc123

**Claude:** *Downloads via yt-dlp, processes, returns manifest*

### Viewing Frames

**You:** Show me frame 5 from /Users/me/my-cat_for_claude/

**Claude:** *Uses `view_frame` tool, displays the image*

**You:** Show me all the frames

**Claude:** *Uses `view_all_frames` tool, displays up to 10 frames*

### Viewing Audio Visualizations

**You:** Show me the spectrogram

**Claude:** *Uses `view_spectrogram` tool, displays audio frequency visualization*

**You:** What does the audio analysis show?

**Claude:** *Uses `get_audio_analysis` tool, describes frequency bands, energy levels, notable events*

### Quick Info Check

**You:** What's the duration and resolution of ~/Videos/raw-footage.mov?

**Claude:** *Uses `get_video_info` tool, returns metadata without full processing*

---

## Tool Reference

### convert_video

Process a video file or URL.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | string | *required* | File path or URL |
| `frames` | int | 20 | Number of frames to extract |
| `include_audio` | bool | true | Whether to analyze audio |
| `output_dir` | string | auto | Custom output directory |

**Returns:** Manifest dictionary with processing results

### get_video_info

Get metadata about a video without processing.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | File path or URL |

**Returns:** Dictionary with duration, resolution, FPS, codec, audio info

### view_frame

View a single frame from processed video.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | string | Path to processed video directory |
| `frame_number` | int | Frame number (1-indexed) |

**Returns:** Frame image

### view_all_frames

View multiple frames at once.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | string | *required* | Path to processed video directory |
| `max_frames` | int | 10 | Maximum frames to return (max: 20) |

**Returns:** List of frame images

### view_spectrogram

View audio spectrogram visualization.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | string | Path to processed video directory |

**Returns:** Spectrogram image

### view_waveform

View audio waveform visualization.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | string | Path to processed video directory |

**Returns:** Waveform image

### get_audio_analysis

Get detailed audio analysis data.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | string | Path to processed video directory |

**Returns:** Dictionary with frequency analysis, energy levels, notable events

### get_manifest

Get the full manifest from processed video.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | string | Path to processed video directory |

**Returns:** Full manifest dictionary

---

## Troubleshooting

### "video-to-claude-mcp: command not found"

The MCP server isn't in your PATH. Use the full path:

```bash
# Find where it's installed
pip show video-to-claude | grep Location
# Then add with full path
claude mcp add video-to-claude /path/to/bin/video-to-claude-mcp
```

### "ffmpeg not found"

Install ffmpeg:
```bash
brew install ffmpeg  # macOS
apt install ffmpeg   # Ubuntu/Debian
```

### "yt-dlp not found" (for YouTube URLs)

Install yt-dlp:
```bash
pip install yt-dlp
# or
brew install yt-dlp
```

### Tools not appearing after setup

1. Make sure you restarted Claude Code
2. Check the MCP server is registered: `claude mcp list`
3. Check for errors in Claude Code logs

### "Video file not found"

Use absolute paths (starting with `/` or `~/`) instead of relative paths.

---

## Next Steps

- **[YouTube & URLs](YouTube-and-URLs)** - More on processing online videos
- **[Uploading Videos](Uploading-Videos)** - Share to the cloud for access anywhere
- **[Claude.ai Setup](Claude-AI-Setup)** - Access videos from claude.ai
