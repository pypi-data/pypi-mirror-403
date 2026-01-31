/**
 * video-to-claude Remote MCP Server
 *
 * A Cloudflare Workers-based MCP server that serves pre-processed video content
 * from R2 storage with GitHub OAuth authentication.
 */

import { Hono } from "hono";
import { cors } from "hono/cors";
import { z } from "zod";
import type { Env, AuthProps } from "./types.js";
import {
  handleListVideos,
  handleGetManifest,
  handleGetFrame,
  handleGetFrames,
  handleGetSpectrogram,
  handleGetWaveform,
  handleGetAudioAnalysis,
  ListVideosSchema,
  GetManifestSchema,
  GetFrameSchema,
  GetFramesSchema,
  GetSpectrogramSchema,
  GetWaveformSchema,
  GetAudioAnalysisSchema,
} from "./tools.js";
import { GitHubHandler } from "./github-handler.js";
import { OAuthMetadataHandler, getWWWAuthenticateHeader } from "./oauth-metadata.js";
import { createVideoId, uploadVideo } from "./r2.js";

// MCP Protocol types
interface MCPRequest {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: Record<string, unknown>;
}

interface MCPResponse {
  jsonrpc: "2.0";
  id: string | number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
  };
}

// MCP tool definitions
const TOOLS = [
  {
    name: "list_videos",
    description: "List all videos available in storage. Returns video IDs and names.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "get_manifest",
    description:
      "Get the complete manifest for a video, including metadata, frame list, and audio information.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID (from list_videos output)",
        },
      },
      required: ["video_id"],
    },
  },
  {
    name: "get_frame",
    description: "Get a single frame image from a video.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID",
        },
        frame_number: {
          type: "integer",
          minimum: 1,
          description: "Frame number (1-indexed)",
        },
      },
      required: ["video_id", "frame_number"],
    },
  },
  {
    name: "get_frames",
    description:
      "Get multiple frames from a video. Returns evenly distributed frames within the specified range.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID",
        },
        start: {
          type: "integer",
          minimum: 1,
          description: "Start frame number (default: 1)",
        },
        end: {
          type: "integer",
          minimum: 1,
          description: "End frame number (default: last frame)",
        },
        max_frames: {
          type: "integer",
          minimum: 1,
          maximum: 10,
          description: "Maximum frames to return (default: 5, max: 10)",
        },
      },
      required: ["video_id"],
    },
  },
  {
    name: "get_spectrogram",
    description:
      "Get the audio spectrogram image showing frequency content over time.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID",
        },
      },
      required: ["video_id"],
    },
  },
  {
    name: "get_waveform",
    description: "Get the audio waveform image showing amplitude over time.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID",
        },
      },
      required: ["video_id"],
    },
  },
  {
    name: "get_audio_analysis",
    description:
      "Get detailed audio analysis including frequency bands, energy levels, and notable events.",
    inputSchema: {
      type: "object",
      properties: {
        video_id: {
          type: "string",
          description: "The video ID",
        },
      },
      required: ["video_id"],
    },
  },
];

// Server info
const SERVER_INFO = {
  name: "video-to-claude-remote",
  version: "0.2.0",
  protocolVersion: "2025-06-18",
};

// Create Hono app
const app = new Hono<{ Bindings: Env }>();

// CORS middleware
app.use(
  "*",
  cors({
    origin: "*",
    allowMethods: ["GET", "POST", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
  })
);

// Health check
app.get("/", (c) => {
  return c.json({
    name: SERVER_INFO.name,
    version: SERVER_INFO.version,
    protocolVersion: SERVER_INFO.protocolVersion,
    status: "healthy",
    endpoints: {
      mcp: "/mcp",
      sse: "/sse",
      upload: "/upload",
      oauth: {
        protected_resource_metadata: "/.well-known/oauth-protected-resource",
        authorization_server_metadata: "/.well-known/oauth-authorization-server",
        register: "/register",
        authorize: "/authorize",
        callback: "/callback",
        token: "/token",
      },
    },
  });
});

// Mount OAuth metadata endpoints (RFC 9728 & RFC 8414)
app.route("/", OAuthMetadataHandler);

// Mount GitHub OAuth handler
app.route("/", GitHubHandler);

// Upload endpoint - allows authenticated users to upload processed videos
app.post("/upload", async (c) => {
  const authHeader = c.req.header("Authorization");
  const user = await authenticate(c.env, authHeader);

  // Require authentication for uploads
  if (!user) {
    const baseUrl = new URL(c.req.url).origin;
    return c.json(
      { error: "Unauthorized. Please authenticate first." },
      401,
      { "WWW-Authenticate": getWWWAuthenticateHeader(baseUrl) }
    );
  }

  try {
    const formData = await c.req.formData();
    const name = formData.get("name");

    if (!name || typeof name !== "string") {
      return c.json({ error: "Missing 'name' field" }, 400);
    }

    // Check for manifest (required)
    const manifest = formData.get("manifest.json");
    if (!manifest || typeof manifest === "string") {
      return c.json({ error: "Missing manifest.json file" }, 400);
    }

    // Create video ID
    const videoId = createVideoId(name);

    // Collect all files
    const files = new Map<string, { data: ArrayBuffer; contentType: string }>();

    for (const [key, value] of formData.entries()) {
      if (key === "name") continue;
      if (typeof value === "string") continue;

      const file = value as globalThis.File;
      const data = await file.arrayBuffer();
      const contentType = file.type || getContentType(key);
      files.set(key, { data, contentType });
    }

    // Upload to R2 with owner
    await uploadVideo(c.env.R2, videoId, name, files, user.login);

    return c.json({
      success: true,
      video_id: videoId,
      name,
      files: Array.from(files.keys()),
      uploaded_by: user.login,
    });
  } catch (error) {
    console.error("Upload error:", error);
    return c.json(
      { error: error instanceof Error ? error.message : "Upload failed" },
      500
    );
  }
});

/**
 * Get content type from filename.
 */
function getContentType(filename: string): string {
  if (filename.endsWith(".json")) return "application/json";
  if (filename.endsWith(".jpg") || filename.endsWith(".jpeg")) return "image/jpeg";
  if (filename.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}

/**
 * Authenticate request and get user props.
 */
async function authenticate(
  env: Env,
  authHeader: string | undefined
): Promise<AuthProps | null> {
  if (!authHeader?.startsWith("Bearer ")) {
    return null;
  }

  const token = authHeader.slice(7);
  const tokenKey = `token:${token}`;
  const tokenData = await env.OAUTH_KV.get(tokenKey);

  if (!tokenData) {
    return null;
  }

  return JSON.parse(tokenData) as AuthProps;
}

/**
 * Handle MCP tool call.
 */
async function handleToolCall(
  env: Env,
  name: string,
  args: Record<string, unknown>,
  userLogin?: string
): Promise<unknown> {
  switch (name) {
    case "list_videos":
      return handleListVideos(env.R2, userLogin);

    case "get_manifest":
      return handleGetManifest(env.R2, GetManifestSchema.parse(args), userLogin);

    case "get_frame":
      return handleGetFrame(env.R2, GetFrameSchema.parse(args), userLogin);

    case "get_frames":
      return handleGetFrames(env.R2, GetFramesSchema.parse(args), userLogin);

    case "get_spectrogram":
      return handleGetSpectrogram(env.R2, GetSpectrogramSchema.parse(args), userLogin);

    case "get_waveform":
      return handleGetWaveform(env.R2, GetWaveformSchema.parse(args), userLogin);

    case "get_audio_analysis":
      return handleGetAudioAnalysis(env.R2, GetAudioAnalysisSchema.parse(args), userLogin);

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

/**
 * Handle MCP JSON-RPC request.
 */
async function handleMCPRequest(
  env: Env,
  request: MCPRequest,
  user: AuthProps | null
): Promise<MCPResponse> {
  const { id, method, params } = request;

  try {
    switch (method) {
      case "initialize":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion: SERVER_INFO.protocolVersion,
            capabilities: {
              tools: {},
            },
            serverInfo: {
              name: SERVER_INFO.name,
              version: SERVER_INFO.version,
            },
          },
        };

      case "initialized":
        return {
          jsonrpc: "2.0",
          id,
          result: {},
        };

      case "tools/list":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            tools: TOOLS,
          },
        };

      case "tools/call": {
        const toolParams = params as { name: string; arguments?: Record<string, unknown> };
        const result = await handleToolCall(
          env,
          toolParams.name,
          toolParams.arguments || {},
          user?.login
        );
        return {
          jsonrpc: "2.0",
          id,
          result,
        };
      }

      case "ping":
        return {
          jsonrpc: "2.0",
          id,
          result: {},
        };

      default:
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`,
          },
        };
    }
  } catch (error) {
    console.error("MCP request error:", error);
    return {
      jsonrpc: "2.0",
      id,
      error: {
        code: -32603,
        message: error instanceof Error ? error.message : "Internal error",
      },
    };
  }
}

// MCP endpoint (streamable HTTP transport)
app.post("/mcp", async (c) => {
  const authHeader = c.req.header("Authorization");
  const user = await authenticate(c.env, authHeader);

  // Require authentication - return proper WWW-Authenticate header per RFC 9728
  if (!user) {
    const baseUrl = new URL(c.req.url).origin;
    return c.json(
      {
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32001,
          message: "Unauthorized",
        },
      },
      401,
      { "WWW-Authenticate": getWWWAuthenticateHeader(baseUrl) }
    );
  }

  try {
    const body = await c.req.json();

    // Handle batch requests
    if (Array.isArray(body)) {
      const responses = await Promise.all(
        body.map((req: MCPRequest) => handleMCPRequest(c.env, req, user))
      );
      return c.json(responses);
    }

    // Handle single request
    const response = await handleMCPRequest(c.env, body as MCPRequest, user);
    return c.json(response);
  } catch (error) {
    console.error("MCP endpoint error:", error);
    return c.json(
      {
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: "Parse error",
        },
      },
      400
    );
  }
});

// SSE endpoint (legacy transport)
app.get("/sse", async (c) => {
  const authHeader = c.req.header("Authorization");
  const user = await authenticate(c.env, authHeader);

  // Set up SSE
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const encoder = new TextEncoder();

  // Send initial connection event
  const sendEvent = async (event: string, data: unknown) => {
    await writer.write(encoder.encode(`event: ${event}\n`));
    await writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
  };

  // Send endpoint info
  await sendEvent("endpoint", { url: new URL("/mcp", c.req.url).href });

  // Keep connection alive
  const keepAlive = setInterval(async () => {
    try {
      await writer.write(encoder.encode(": keepalive\n\n"));
    } catch {
      clearInterval(keepAlive);
    }
  }, 30000);

  // Handle connection close
  c.req.raw.signal.addEventListener("abort", () => {
    clearInterval(keepAlive);
    writer.close();
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
});

export default app;
