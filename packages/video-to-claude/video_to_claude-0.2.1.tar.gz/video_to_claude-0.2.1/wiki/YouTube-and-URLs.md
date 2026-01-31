# YouTube & URLs

Process videos directly from YouTube and other online sources.

---

## Overview

video-to-claude can download and process videos from:

- **YouTube** - Regular videos, Shorts, playlists (first video)
- **Direct URLs** - Any URL ending in a video file extension
- **Other platforms** - Anything yt-dlp supports (Vimeo, Twitter, etc.)

---

## Prerequisites

For YouTube and most online platforms, you need **yt-dlp**:

```bash
# Install via pip
pip install yt-dlp

# Or via Homebrew (macOS)
brew install yt-dlp

# Or via apt (Ubuntu/Debian)
sudo apt install yt-dlp
```

**Verify installation:**
```bash
yt-dlp --version
```

---

## YouTube Videos

### Regular Videos

```bash
video-to-claude convert "https://www.youtube.com/watch?v=VIDEO_ID"
```

### YouTube Shorts

```bash
video-to-claude convert "https://www.youtube.com/shorts/VIDEO_ID"
```

### With Custom Options

```bash
# More frames for longer video
video-to-claude convert "https://www.youtube.com/watch?v=VIDEO_ID" --frames 30

# Custom output location
video-to-claude convert "https://www.youtube.com/watch?v=VIDEO_ID" -o ~/Videos/yt-video/
```

---

## Direct Video URLs

For direct links to video files:

```bash
video-to-claude convert "https://example.com/path/to/video.mp4"
```

Supported formats: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, and any other format ffmpeg supports.

---

## Other Platforms

yt-dlp supports hundreds of platforms. Some examples:

### Vimeo
```bash
video-to-claude convert "https://vimeo.com/VIDEO_ID"
```

### Twitter/X
```bash
video-to-claude convert "https://twitter.com/user/status/TWEET_ID"
```

### TikTok
```bash
video-to-claude convert "https://www.tiktok.com/@user/video/VIDEO_ID"
```

### Reddit
```bash
video-to-claude convert "https://www.reddit.com/r/subreddit/comments/POST_ID/"
```

For the full list of supported sites, see: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

## Using with Claude Code

If you have the MCP server configured in Claude Code, just ask:

> "Convert this YouTube video: https://www.youtube.com/shorts/abc123"

Claude will use the `convert_video` tool to download and process it automatically.

---

## How It Works

1. **URL Detection** - video-to-claude checks if the input starts with `http://` or `https://`
2. **Platform Detection** - For YouTube URLs, uses yt-dlp with optimal settings
3. **Download** - Video is downloaded to a temporary location
4. **Process** - Standard frame extraction and audio analysis
5. **Cleanup** - Temporary download is removed after processing

The downloaded video is stored temporarily and deleted after processing. Only the extracted frames and analysis remain.

---

## Quality Settings

By default, yt-dlp downloads the best available quality. The video is then processed at its downloaded resolution.

For very high-resolution videos (4K+), you might want to consider:
- The output frame JPEGs will be large
- Processing may take longer
- Consider using fewer frames (`--frames 10`)

---

## Age-Restricted Content

For age-restricted YouTube videos, you may need to authenticate yt-dlp:

```bash
# Login to YouTube (stores cookies)
yt-dlp --cookies-from-browser chrome "https://www.youtube.com/watch?v=VIDEO_ID"
```

Or provide cookies manually:
```bash
yt-dlp --cookies cookies.txt "https://www.youtube.com/watch?v=VIDEO_ID"
```

Note: video-to-claude uses yt-dlp's default settings. For advanced authentication, download the video manually first, then process the local file.

---

## Troubleshooting

### "yt-dlp not found"

Install yt-dlp:
```bash
pip install yt-dlp
```

### "Unable to download video"

Common causes:
1. **Private video** - Must be public or unlisted
2. **Region-restricted** - Video not available in your region
3. **Age-restricted** - Requires authentication (see above)
4. **Invalid URL** - Double-check the URL format

Try downloading manually to see the error:
```bash
yt-dlp "https://youtube.com/watch?v=VIDEO_ID"
```

### "Video too long"

yt-dlp will download the entire video. For very long videos:
- This may take a while
- Use fewer frames (`--frames 10`)
- Consider downloading and trimming manually first

### SSL Certificate Errors

Try updating yt-dlp:
```bash
pip install -U yt-dlp
```

### Rate Limiting

If you're processing many videos, YouTube may rate limit you. Wait a few minutes between downloads.

---

## Examples

### Quick YouTube Short

```bash
video-to-claude convert "https://www.youtube.com/shorts/abc123"
```

### Music Video with Extra Frames

```bash
video-to-claude convert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --frames 40
```

### Tutorial Video (No Audio Needed)

```bash
video-to-claude convert "https://www.youtube.com/watch?v=TUTORIAL_ID" --no-audio
```

### Process and Upload to Cloud

```bash
# Process
video-to-claude convert "https://www.youtube.com/shorts/abc123" -o ./yt-short/

# Upload
video-to-claude upload ./yt-short/ --name "Cool YouTube Short"
```

---

## Next Steps

- **[CLI Reference](CLI-Reference)** - All command options
- **[Uploading Videos](Uploading-Videos)** - Share to the cloud
- **[Claude Code Setup](Claude-Code-Setup)** - Process URLs directly in Claude
