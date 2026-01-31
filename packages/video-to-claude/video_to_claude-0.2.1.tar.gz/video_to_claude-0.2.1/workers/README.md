# video-to-claude Remote MCP Server

Cloudflare Workers-based MCP server for serving pre-processed video content with GitHub OAuth authentication.

**Production Deployment:** https://api.ai-media-tools.dev

## Features

- Secure upload endpoint with GitHub OAuth authentication
- MCP server for accessing uploaded videos (requires auth)
- Custom domain support
- R2 storage for video frames and audio analysis
- RESTful API for video management

## Prerequisites

- Node.js 18+
- Cloudflare account with Workers enabled
- R2 bucket for storage
- GitHub OAuth App for authentication
- (Optional) Custom domain configured in Cloudflare

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
   - Homepage URL: `https://your-domain.com` (or `https://your-worker.workers.dev`)
   - Callback URL: `https://your-domain.com/callback` (or `https://your-worker.workers.dev/callback`)
4. Note the Client ID and generate a Client Secret

**Note:** If using a custom domain, use that domain in the URLs. You can update these later after deploying.

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

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/` | GET | No | Health check and server info |
| `/mcp` | POST | **Yes** | MCP JSON-RPC endpoint (streamable HTTP) |
| `/sse` | GET | **Yes** | SSE endpoint (legacy transport) |
| `/upload` | POST | **Yes** | Upload processed video files |
| `/authorize` | GET | No | OAuth authorization start |
| `/callback` | GET | No | OAuth callback handler |

**Authentication:** Endpoints marked with "Yes" require a Bearer token in the `Authorization` header:

```bash
Authorization: Bearer YOUR_GITHUB_TOKEN
```

Tokens are obtained through the GitHub OAuth flow (`/authorize` -> `/callback`).

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

Add to your Claude Desktop config with authentication:

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
        "MCP_AUTH_TOKEN": "your-github-oauth-token"
      }
    }
  }
}
```

**Getting your token:**

Run the upload command to authenticate and get your token:

```bash
video-to-claude upload --get-token
```

Or set the `VIDEO_TO_CLAUDE_TOKEN` environment variable if you already have a token.

## Custom Domain Setup

To use a custom domain like `api.ai-media-tools.dev`:

1. **Add domain to Cloudflare** (if not already added)
2. **Deploy your worker**: `npm run deploy`
3. **Add custom domain in Cloudflare dashboard**:
   - Go to Workers & Pages
   - Select your worker
   - Go to Settings > Domains & Routes
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `api.ai-media-tools.dev`)
4. **Update GitHub OAuth App**:
   - Go to your OAuth App settings
   - Update Homepage URL and Callback URL to use custom domain
5. **Update client code** (if self-hosting):
   - Update `DEFAULT_SERVER_URL` in `src/video_to_claude/upload.py`

Custom domains provide:
- Professional appearance
- Cleaner URLs
- Better branding
- SSL/TLS certificates (automatic via Cloudflare)
