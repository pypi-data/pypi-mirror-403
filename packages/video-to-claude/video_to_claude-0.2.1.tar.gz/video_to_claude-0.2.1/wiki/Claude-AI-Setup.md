# Claude.ai Setup

Access your processed videos from claude.ai using the remote MCP server.

---

## Overview

The remote MCP server lets you view videos that have been processed and uploaded to the cloud. This works from anywhere - no local installation needed.

**Important:** The remote server can only **view** pre-processed videos. It cannot process new videos (that requires ffmpeg which can't run on Cloudflare Workers). To add new videos, use the [CLI](CLI-Reference) or [Claude Code](Claude-Code-Setup) to process and upload.

---

## Quick Setup

### Step 1: Add the MCP Connector

1. Go to [claude.ai](https://claude.ai)
2. Click on your profile icon → **Settings**
3. Go to **Integrations** (or **MCP Connectors**)
4. Click **Add Custom Connector**
5. Enter the server URL:
   ```
   https://api.ai-media-tools.dev
   ```
6. Click **Connect**

### Step 2: Authenticate

1. You'll be redirected to GitHub to authorize
2. Click **Authorize** to grant access
3. You'll be redirected back to claude.ai

### Step 3: Use It

In any Claude conversation, you can now:

> "List my videos"

> "Show me the manifest for [video-name]"

> "Show me frame 10 of [video-name]"

---

## Available Tools

Once connected, Claude has access to these tools:

| Tool | Description |
|------|-------------|
| `list_videos` | List all your uploaded videos |
| `get_manifest` | Get video metadata and viewing instructions |
| `get_frame` | Get a single frame image |
| `get_frames` | Get multiple frames at once |
| `get_spectrogram` | Get audio frequency visualization |
| `get_waveform` | Get audio amplitude visualization |
| `get_audio_analysis` | Get detailed audio data |

---

## Usage Examples

### List Your Videos

**You:** What videos do I have?

**Claude:** *Uses `list_videos`, shows your uploaded videos with names and durations*

### View a Video

**You:** Show me the Wilson video

**Claude:** *Gets manifest, describes the video, then shows frames*

### View Specific Frames

**You:** Show me frames 5 through 10 of the Wilson video

**Claude:** *Uses `get_frames` to retrieve and display those frames*

### Understand the Audio

**You:** What does the audio sound like in the YouTube short?

**Claude:** *Gets spectrogram and audio analysis, describes the sound*

---

## Adding Videos

To add videos to your library, you need to:

1. **Process locally** using CLI or Claude Code
2. **Upload** to the cloud

### From CLI

```bash
# Process the video
video-to-claude convert ~/Videos/my-video.mp4

# Upload to cloud
video-to-claude upload ./my-video_for_claude/ --name "My Video"
```

### From Claude Code

If you have the local MCP configured, just ask Claude:

> "Convert ~/Videos/my-video.mp4 and upload it as 'My Video'"

---

## User Isolation

Your videos are private to you:

- Each video is tagged with your GitHub username
- You can only see videos you uploaded
- Other users cannot access your videos

The authentication flow uses GitHub OAuth to verify your identity.

---

## Tool Reference

### list_videos

List all videos in your library.

**Parameters:** None

**Returns:** List of videos with:
- `video_id` - Unique identifier
- `name` - Display name
- `duration` - Video length
- `uploaded_at` - Upload timestamp

### get_manifest

Get full manifest for a video.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | string | Video identifier |

**Returns:** Complete manifest with video info, frame list, audio summary

### get_frame

Get a single frame image.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | string | Video identifier |
| `frame_number` | int | Frame number (1-indexed) |

**Returns:** Frame image (base64 encoded)

### get_frames

Get multiple frames at once.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | string | *required* | Video identifier |
| `start` | int | 1 | Starting frame number |
| `end` | int | last | Ending frame number |
| `max_frames` | int | 10 | Maximum frames to return |

**Returns:** List of frame images

### get_spectrogram

Get audio spectrogram visualization.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | string | Video identifier |

**Returns:** Spectrogram image (base64 encoded)

### get_waveform

Get audio waveform visualization.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | string | Video identifier |

**Returns:** Waveform image (base64 encoded)

### get_audio_analysis

Get detailed audio analysis.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | string | Video identifier |

**Returns:** Audio analysis data with frequency bands, energy, events

---

## Troubleshooting

### "No videos found"

You haven't uploaded any videos yet. Use the CLI to process and upload:

```bash
video-to-claude convert ~/Videos/video.mp4
video-to-claude upload ./video_for_claude/ --name "My Video"
```

### "Access denied: you don't own this video"

You're trying to access a video uploaded by another user. Each user can only see their own videos.

### "Authentication failed"

1. Try disconnecting and reconnecting the MCP connector
2. Make sure you authorized the GitHub OAuth request
3. Check that you're signed into the correct GitHub account

### Connection timeout

The server might be experiencing issues. Try:
1. Refresh the page
2. Disconnect and reconnect the MCP connector
3. Try again in a few minutes

---

## Privacy & Security

- **Authentication:** GitHub OAuth verifies your identity
- **Authorization:** Each video is tagged with owner's GitHub username
- **Isolation:** Users can only access their own videos
- **Storage:** Videos stored in Cloudflare R2 (encrypted at rest)
- **Transport:** All connections over HTTPS

---

## Next Steps

- **[Uploading Videos](Uploading-Videos)** - Detailed upload guide
- **[YouTube & URLs](YouTube-and-URLs)** - Process online videos
- **[Troubleshooting](Troubleshooting)** - More help with common issues
