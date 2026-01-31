# Uploading Videos

Share your processed videos to the cloud for access from anywhere.

---

## Overview

After processing a video locally, you can upload it to the cloud. This lets you:

- Access videos from claude.ai (via remote MCP)
- Share videos across devices
- Keep your videos backed up

---

## Quick Upload

### Step 1: Process a Video

```bash
video-to-claude convert ~/Videos/my-video.mp4
```

This creates `my-video_for_claude/` with all the outputs.

### Step 2: Upload

```bash
video-to-claude upload ./my-video_for_claude/ --name "My Awesome Video"
```

### Step 3: Authenticate (First Time)

On your first upload, you'll be prompted to authenticate:

1. Your browser opens to GitHub
2. Click **Authorize** to grant access
3. Browser shows "Authentication successful!"
4. Return to terminal - upload continues

### Step 4: Done!

You'll see:
```
Success!
Video ID: my-awesome-video-abc123
Files uploaded: 24

Your video is now accessible via the remote MCP server.
Server: https://api.ai-media-tools.dev
```

---

## Authentication

### How It Works

video-to-claude uses GitHub OAuth for authentication:

1. First upload opens browser → GitHub authorization
2. You approve the OAuth request
3. A token is returned to the CLI
4. Token is used for the upload

### Saving Your Token

To avoid re-authenticating every time, save the token:

```bash
# After first auth, the token is shown
# Save it as an environment variable
export VIDEO_TO_CLAUDE_TOKEN=your-token-here
```

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence:

```bash
echo 'export VIDEO_TO_CLAUDE_TOKEN=your-token-here' >> ~/.zshrc
```

### Using a Saved Token

With the environment variable set:

```bash
video-to-claude upload ./video_for_claude/ --name "My Video"
# No browser popup - uses saved token
```

Or pass directly:

```bash
video-to-claude upload ./video_for_claude/ --name "My Video" --token your-token
```

---

## Naming Videos

The `--name` option sets the display name for your video:

```bash
video-to-claude upload ./output/ --name "Wilson the Dog Greeting"
```

**Tips:**
- Use descriptive names you'll recognize later
- Names can include spaces and special characters
- The video ID is generated from the name (slugified + hash)

---

## What Gets Uploaded

The upload includes all files in the processed output:

| File | Description |
|------|-------------|
| `manifest.json` | Video metadata and viewing instructions |
| `frame_001.jpg` ... `frame_N.jpg` | Extracted frames |
| `spectrogram.png` | Audio frequency visualization |
| `waveform.png` | Audio amplitude visualization |
| `audio_analysis.json` | Detailed audio data |

Typically 2-10 MB total for a 30-second video with 20 frames.

---

## Accessing Uploaded Videos

### From claude.ai

1. Add the MCP connector (see [Claude.ai Setup](Claude-AI-Setup))
2. Ask Claude: "List my videos"
3. Claude shows your uploaded videos
4. Ask: "Show me [video name]"

### Video IDs

Each upload gets a unique video ID:
```
wilson-the-dog-abc123
my-awesome-video-xyz789
```

You can use either the name or ID when asking Claude about videos.

---

## Direct R2 Upload (Advanced)

For users with Cloudflare R2 credentials, you can upload directly without going through the worker API:

### Setup Credentials

```bash
export CLOUDFLARE_ACCOUNT_ID=your-account-id
export CLOUDFLARE_R2_ACCESS_KEY_ID=your-access-key
export CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret-key
```

### Upload with --direct

```bash
video-to-claude upload ./video_for_claude/ --name "My Video" --direct
```

### Custom Bucket

```bash
video-to-claude upload ./output/ --name "Video" --direct --bucket my-custom-bucket
```

**Note:** Direct upload requires the `upload` extra:
```bash
pip install video-to-claude[upload]
```

---

## Storage & Limits

### Current Limits

- No hard file size limits
- Reasonable use expected (personal videos, not bulk storage)
- Videos are private to your GitHub account

### Storage Location

Videos are stored in Cloudflare R2:
- Encrypted at rest
- Globally distributed (fast access worldwide)
- Managed by the video-to-claude infrastructure

---

## Managing Uploaded Videos

### Listing Videos

From claude.ai:
> "List my videos"

Or using the MCP tools directly.

### Deleting Videos

Currently, video deletion is not available through the CLI. Contact support or manage directly if you have R2 access.

*Note: Deletion via CLI is planned for a future release.*

---

## Troubleshooting

### "No manifest.json found"

Make sure you're pointing to the processed output directory, not the original video:

```bash
# Wrong
video-to-claude upload ~/Videos/my-video.mp4 --name "Video"

# Correct
video-to-claude upload ~/Videos/my-video_for_claude/ --name "Video"
```

### "Authentication failed"

1. Make sure you have internet access
2. Try clearing saved token and re-authenticating
3. Check that you're approving the correct GitHub OAuth request

### "error code: 1010"

This is a Cloudflare protection error. The CLI automatically handles this with proper headers, but if you see it:

1. Make sure you're using the latest version: `pip install -U video-to-claude`
2. Try again in a few seconds

### "Upload failed: timeout"

Large uploads may timeout. Try:
1. Check your internet connection
2. Process with fewer frames: `video-to-claude convert video.mp4 --frames 10`
3. Try again

### Token Not Working

Tokens can expire or be revoked. Get a new one:

```bash
# Clear saved token
unset VIDEO_TO_CLAUDE_TOKEN

# Upload will prompt for new auth
video-to-claude upload ./output/ --name "Video"
```

---

## Complete Example

```bash
# 1. Process a YouTube video
video-to-claude convert "https://www.youtube.com/shorts/abc123" -o ./cool-short/

# 2. Upload it
video-to-claude upload ./cool-short/ --name "Cool YouTube Short"

# 3. Access from claude.ai
# Connect MCP server, then ask:
# "Show me the Cool YouTube Short video"
```

---

## Next Steps

- **[Claude.ai Setup](Claude-AI-Setup)** - Access uploaded videos
- **[YouTube & URLs](YouTube-and-URLs)** - Process online videos
- **[Troubleshooting](Troubleshooting)** - More help
