# Troubleshooting

Solutions to common issues with video-to-claude.

---

## Installation Issues

### "pip: command not found"

Python's package manager isn't in your PATH. Try:

```bash
# Use python's module directly
python3 -m pip install video-to-claude
```

### "video-to-claude: command not found"

The CLI isn't in your PATH after installation. Solutions:

1. **Restart your terminal** - PATH updates on new sessions

2. **Check installation location:**
   ```bash
   pip show video-to-claude | grep Location
   ```

3. **Use full path:**
   ```bash
   python3 -m video_to_claude.cli convert video.mp4
   ```

4. **Install with --user flag:**
   ```bash
   pip install --user video-to-claude
   # Add ~/.local/bin to PATH
   ```

### "ffmpeg not found"

Install ffmpeg for your system:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Windows (manual)
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

### "No module named 'scipy'"

Dependencies didn't install correctly. Reinstall:

```bash
pip uninstall video-to-claude
pip install video-to-claude
```

---

## Video Processing Issues

### "Video file not found"

- Use absolute paths: `/Users/you/Videos/video.mp4`
- Expand home directory: `~/Videos/video.mp4`
- Check the file exists: `ls -la /path/to/video.mp4`

### "Could not read video"

The video format may not be supported. Try:

1. **Check ffmpeg can read it:**
   ```bash
   ffmpeg -i video.mp4
   ```

2. **Convert to a standard format first:**
   ```bash
   ffmpeg -i input.weird -c:v libx264 -c:a aac output.mp4
   video-to-claude convert output.mp4
   ```

### "Frame extraction failed"

- Video may be corrupted - try playing it in a media player
- Try with fewer frames: `--frames 5`
- Check ffmpeg is working: `ffmpeg -version`

### "Audio extraction failed"

- Video may not have an audio track
- Use `--no-audio` flag to skip audio processing
- Check video has audio: `video-to-claude info video.mp4`

### Processing takes forever

- Long videos take longer - try `--frames 10` for faster processing
- High-resolution videos are slower - output frames are at original resolution
- Audio analysis is CPU-intensive for long videos

---

## YouTube & URL Issues

### "yt-dlp not found"

Install yt-dlp:

```bash
pip install yt-dlp
# or
brew install yt-dlp
```

### "Unable to download video"

| Issue | Solution |
|-------|----------|
| Private video | Video must be public or unlisted |
| Age-restricted | Requires authentication (see below) |
| Region-blocked | Use VPN or try different video |
| Invalid URL | Check URL format is correct |

**Test download manually:**
```bash
yt-dlp "https://youtube.com/watch?v=VIDEO_ID"
```

### Age-restricted videos

Authenticate yt-dlp with your browser cookies:

```bash
# Using Chrome cookies
yt-dlp --cookies-from-browser chrome "URL"

# Using Firefox cookies
yt-dlp --cookies-from-browser firefox "URL"
```

### "SSL certificate error"

Update yt-dlp:
```bash
pip install -U yt-dlp
```

### Rate limiting

YouTube limits requests. Wait a few minutes between downloads.

---

## Upload Issues

### "No manifest.json found"

You're pointing to the wrong directory:

```bash
# Wrong - pointing to video file
video-to-claude upload ~/Videos/my-video.mp4 --name "Video"

# Correct - pointing to processed output directory
video-to-claude upload ~/Videos/my-video_for_claude/ --name "Video"
```

### Authentication popup doesn't appear

1. Check your default browser is set
2. Try manually opening: `https://api.ai-media-tools.dev/authorize`
3. Use `--token` flag if you have a saved token

### "Authentication failed"

1. Clear saved token: `unset VIDEO_TO_CLAUDE_TOKEN`
2. Try upload again (will re-authenticate)
3. Make sure you're clicking "Authorize" on GitHub

### "error code: 1010"

Cloudflare protection triggered. The CLI handles this, but if you see it:

1. Update to latest version: `pip install -U video-to-claude`
2. Wait a few seconds and try again

### Upload timeout

For large uploads:
1. Check internet connection
2. Try with fewer frames: `--frames 10`
3. Try again later

### Token stopped working

Tokens can expire. Get a new one:

```bash
unset VIDEO_TO_CLAUDE_TOKEN
video-to-claude upload ./output/ --name "Video"
# Will prompt for new authentication
```

---

## Claude Code MCP Issues

### "video-to-claude-mcp: command not found"

The MCP server isn't in your PATH. Use full path:

```bash
# Find installation location
which video-to-claude-mcp
# or
pip show video-to-claude | grep Location

# Add with full path
claude mcp add video-to-claude /full/path/to/video-to-claude-mcp
```

### Tools not appearing in Claude Code

1. **Restart Claude Code** after adding MCP server
2. **Check MCP is registered:**
   ```bash
   claude mcp list
   ```
3. **Check for errors** in Claude Code logs

### "Video file not found" in Claude Code

Use absolute paths when asking Claude to process videos:
- Good: `/Users/you/Videos/video.mp4`
- Good: `~/Videos/video.mp4`
- Bad: `./video.mp4` (relative paths can fail)

### MCP server crashes

Check dependencies are installed:
```bash
pip install video-to-claude[dev]  # Installs all dependencies
```

---

## Claude.ai MCP Issues

### Can't find "Add Custom Connector"

1. Go to claude.ai → Settings (profile icon)
2. Look for "Integrations" or "MCP Connectors"
3. Feature may be rolling out - check back later

### "Connection failed"

1. Check internet connection
2. Server URL should be: `https://api.ai-media-tools.dev`
3. Try disconnecting and reconnecting

### "No videos found"

You haven't uploaded any videos yet:

```bash
video-to-claude convert ~/Videos/video.mp4
video-to-claude upload ./video_for_claude/ --name "My Video"
```

### "Access denied: you don't own this video"

Each user can only access their own videos. Make sure:
1. You're logged into the correct GitHub account
2. You uploaded the video yourself
3. The video ID is correct

### Tools not working

1. Disconnect the MCP connector
2. Reconnect and re-authenticate
3. Try a simple command: "List my videos"

---

## Platform-Specific Issues

### macOS

**"Operation not permitted" errors:**
- Grant terminal full disk access in System Preferences → Security & Privacy

**ffmpeg from Homebrew not found:**
```bash
# Ensure Homebrew is in PATH
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Windows

**ffmpeg not in PATH:**
1. Download ffmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH

**Permission errors:**
- Run terminal as Administrator
- Or use `--user` flag: `pip install --user video-to-claude`

### Linux

**Missing system dependencies:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg python3-pip python3-venv

# Fedora
sudo dnf install ffmpeg python3-pip
```

---

## Getting Help

### Check Version

```bash
video-to-claude --version
pip show video-to-claude
```

### Debug Output

For CLI issues, check what's happening:
```bash
# Verbose ffmpeg output
ffmpeg -i video.mp4 2>&1 | head -50

# Check video info
video-to-claude info video.mp4 --json
```

### Report Issues

If you're stuck:

1. **Search existing issues:** https://github.com/anthropics/video-to-claude/issues
2. **Create new issue** with:
   - Your OS and Python version
   - video-to-claude version
   - Complete error message
   - Steps to reproduce

---

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Command not found | `pip install video-to-claude` and restart terminal |
| ffmpeg not found | `brew install ffmpeg` / `apt install ffmpeg` |
| yt-dlp not found | `pip install yt-dlp` |
| Video not found | Use absolute path: `/full/path/to/video.mp4` |
| Upload auth fails | `unset VIDEO_TO_CLAUDE_TOKEN` and retry |
| MCP tools missing | Restart Claude Code after `claude mcp add` |
| No videos on claude.ai | Upload first: `video-to-claude upload ./output/ -n "Name"` |
