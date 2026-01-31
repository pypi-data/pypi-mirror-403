# Getting Started

This guide will get you from zero to processing your first video in under 5 minutes.

---

## Prerequisites

You'll need:

- **Python 3.10+** - Check with `python3 --version`
- **ffmpeg** - For video/audio processing
- **pip** - Python package manager

### Installing ffmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**Verify installation:**
```bash
ffmpeg -version
```

---

## Step 1: Install video-to-claude

```bash
pip install video-to-claude
```

This installs:
- The `video-to-claude` CLI command
- The `video-to-claude-mcp` MCP server
- All Python dependencies (scipy, numpy, matplotlib, etc.)

**Verify installation:**
```bash
video-to-claude --help
```

You should see:
```
Usage: video-to-claude [OPTIONS] COMMAND [ARGS]...

  Convert video files into a format Claude can experience.

Commands:
  convert  Convert a video file or URL into a format Claude can experience.
  info     Show video metadata without processing.
  upload   Upload processed video output to the cloud.
```

---

## Step 2: Convert Your First Video

Pick any video file on your computer:

```bash
video-to-claude convert ~/Videos/my-video.mp4
```

You'll see progress output:
```
Processing: my-video.mp4
Output: /Users/you/Videos/my-video_for_claude/

Analyzing video... done (30.5s, 1920x1080)
Extracting 20 frames... done (20 frames)
Extracting audio... done
Generating spectrogram... done
Generating waveform... done
Analyzing audio... done
Writing manifest... done

Success!

To experience this video, ask Claude to read:
  /Users/you/Videos/my-video_for_claude/manifest.json

Or view all files in:
  /Users/you/Videos/my-video_for_claude/
```

---

## Step 3: Share with Claude

### Option A: Claude Code (Recommended)

If you're using Claude Code, just tell Claude the path:

> "Read the manifest at /Users/you/Videos/my-video_for_claude/manifest.json and describe the video"

Claude will read the manifest and can then view frames:

> "Show me frame 10"

### Option B: Manual Upload

You can also manually share files with Claude:
1. Open the manifest.json in a text editor
2. Copy the content to Claude
3. Upload individual frames as images

### Option C: Remote MCP (claude.ai)

For access from anywhere, upload to the cloud:

```bash
video-to-claude upload ./my-video_for_claude/ --name "My Video"
```

Then connect to the remote MCP server on claude.ai. See [Claude.ai Setup](Claude-AI-Setup) for details.

---

## Step 4: Try a YouTube Video

video-to-claude can download and process YouTube videos:

```bash
video-to-claude convert "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This requires `yt-dlp`. Install it with:
```bash
pip install yt-dlp
# or
brew install yt-dlp
```

---

## Common Options

### Fewer/More Frames

```bash
# Extract only 10 frames (faster, smaller output)
video-to-claude convert video.mp4 --frames 10

# Extract 50 frames (more detail)
video-to-claude convert video.mp4 --frames 50
```

### Custom Output Directory

```bash
video-to-claude convert video.mp4 --output ./my-custom-folder/
```

### Skip Audio Processing

```bash
video-to-claude convert video.mp4 --no-audio
```

### Just Get Video Info

```bash
video-to-claude info video.mp4
```

Output:
```
File: video.mp4
Duration: 30.52s
Resolution: 1920x1080
FPS: 30.00
Codec: h264
Has Audio: True
Audio Codec: aac
Audio Sample Rate: 48000 Hz
```

---

## Next Steps

- **[CLI Reference](CLI-Reference)** - All commands and options
- **[Claude Code Setup](Claude-Code-Setup)** - Integrate with Claude Code
- **[Claude.ai Setup](Claude-AI-Setup)** - Use from claude.ai
- **[YouTube & URLs](YouTube-and-URLs)** - Process online videos
