# video-to-claude Remote MCP Server

Cloudflare Workers-based MCP server for serving pre-processed video content with GitHub OAuth authentication.

## Prerequisites

- Node.js 18+
- Cloudflare account with Workers enabled
- R2 bucket for storage
- GitHub OAuth App for authentication

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Create R2 Bucket

```bash
wrangler r2 bucket create video-to-claude-storage
```

### 3. Create KV Namespace

```bash
wrangler kv:namespace create OAUTH_KV
```

Update `wrangler.toml` with the returned namespace ID.

### 4. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Set:
   - Application name: `video-to-claude`
   - Homepage URL: `https://your-worker.workers.dev`
   - Callback URL: `https://your-worker.workers.dev/callback`
4. Note the Client ID and generate a Client Secret

### 5. Set Secrets

```bash
wrangler secret put GITHUB_CLIENT_ID
wrangler secret put GITHUB_CLIENT_SECRET
wrangler secret put COOKIE_ENCRYPTION_KEY
```

For `COOKIE_ENCRYPTION_KEY`, generate a random 32-character string:
```bash
openssl rand -hex 16
```

### 6. Deploy

```bash
npm run deploy
```

## Development

```bash
npm run dev
```

This starts a local development server at http://localhost:8787.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and server info |
| `/mcp` | POST | MCP JSON-RPC endpoint (streamable HTTP) |
| `/sse` | GET | SSE endpoint (legacy transport) |
| `/authorize` | GET | OAuth authorization start |
| `/callback` | GET | OAuth callback handler |
| `/token` | POST | Token exchange endpoint |

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_videos` | List all videos in R2 storage |
| `get_manifest` | Get video manifest with metadata |
| `get_frame` | Get a single frame image |
| `get_frames` | Get multiple frames |
| `get_spectrogram` | Get audio spectrogram |
| `get_waveform` | Get audio waveform |
| `get_audio_analysis` | Get detailed audio analysis |

## Testing with MCP Inspector

```bash
npx @anthropic/mcp-inspector http://localhost:8787/mcp
```

## R2 Storage Structure

Videos are stored with this structure:

```
video-to-claude-storage/
└── {video-id}/
    ├── _index.json          # Video index for listing
    ├── manifest.json        # Full manifest
    ├── frame_001.jpg        # Frames
    ├── frame_002.jpg
    ├── ...
    ├── spectrogram.png      # Audio visualization
    ├── waveform.png
    └── audio_analysis.json  # Audio data
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret |
| `COOKIE_ENCRYPTION_KEY` | Key for encrypting OAuth state cookies |
| `ENVIRONMENT` | `production` or `development` |

## Connecting from Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "video-to-claude-remote": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://your-worker.workers.dev/mcp"
      ]
    }
  }
}
```
