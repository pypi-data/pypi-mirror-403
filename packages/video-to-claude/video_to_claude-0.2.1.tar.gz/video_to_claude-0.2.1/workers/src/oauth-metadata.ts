/**
 * OAuth 2.0 Metadata Endpoints for MCP Authorization
 *
 * Implements:
 * - RFC 9728: OAuth 2.0 Protected Resource Metadata
 * - RFC 8414: OAuth 2.0 Authorization Server Metadata
 * - RFC 7591: OAuth 2.0 Dynamic Client Registration
 */

import { Hono } from "hono";
import type {
  Env,
  ProtectedResourceMetadata,
  AuthorizationServerMetadata,
  ClientRegistrationRequest,
  ClientRegistrationResponse,
  RegisteredClient,
} from "./types.js";

const app = new Hono<{ Bindings: Env }>();

/**
 * Get the base URL from the request.
 */
function getBaseUrl(url: string): string {
  const parsed = new URL(url);
  return `${parsed.protocol}//${parsed.host}`;
}

/**
 * RFC 9728 - Protected Resource Metadata
 *
 * Tells clients where to find the authorization server for this resource.
 */
app.get("/.well-known/oauth-protected-resource", (c) => {
  const baseUrl = getBaseUrl(c.req.url);

  const metadata: ProtectedResourceMetadata = {
    resource: baseUrl,
    authorization_servers: [baseUrl],
    bearer_methods_supported: ["header"],
    resource_documentation: "https://github.com/ai-media-tools/video-to-claude",
  };

  return c.json(metadata, 200, {
    "Cache-Control": "max-age=3600",
  });
});

/**
 * RFC 8414 - Authorization Server Metadata
 *
 * Tells clients about OAuth endpoints and capabilities.
 */
app.get("/.well-known/oauth-authorization-server", (c) => {
  const baseUrl = getBaseUrl(c.req.url);

  const metadata: AuthorizationServerMetadata = {
    issuer: baseUrl,
    authorization_endpoint: `${baseUrl}/authorize`,
    token_endpoint: `${baseUrl}/token`,
    registration_endpoint: `${baseUrl}/register`,
    scopes_supported: ["read:user", "user:email"],
    response_types_supported: ["code"],
    response_modes_supported: ["query"],
    grant_types_supported: ["authorization_code", "refresh_token"],
    token_endpoint_auth_methods_supported: [
      "client_secret_post",
      "client_secret_basic",
      "none",
    ],
    code_challenge_methods_supported: ["S256"],
    service_documentation: "https://github.com/ai-media-tools/video-to-claude",
  };

  return c.json(metadata, 200, {
    "Cache-Control": "max-age=3600",
  });
});

/**
 * RFC 7591 - Dynamic Client Registration
 *
 * Allows MCP clients to register themselves automatically.
 */
app.post("/register", async (c) => {
  try {
    const body = (await c.req.json()) as ClientRegistrationRequest;

    // Validate required fields
    if (!body.redirect_uris || body.redirect_uris.length === 0) {
      return c.json(
        {
          error: "invalid_client_metadata",
          error_description: "redirect_uris is required",
        },
        400
      );
    }

    // Validate redirect URIs
    for (const uri of body.redirect_uris) {
      try {
        const parsed = new URL(uri);
        // Allow localhost for development, require HTTPS otherwise
        if (
          parsed.hostname !== "localhost" &&
          parsed.hostname !== "127.0.0.1" &&
          parsed.protocol !== "https:"
        ) {
          return c.json(
            {
              error: "invalid_redirect_uri",
              error_description:
                "redirect_uris must use HTTPS (except localhost)",
            },
            400
          );
        }
      } catch {
        return c.json(
          {
            error: "invalid_redirect_uri",
            error_description: `Invalid redirect URI: ${uri}`,
          },
          400
        );
      }
    }

    // Generate client credentials
    const clientId = `mcp_${crypto.randomUUID().replace(/-/g, "")}`;
    const clientSecret = crypto.randomUUID();

    // Determine auth method
    const tokenEndpointAuthMethod =
      body.token_endpoint_auth_method || "client_secret_post";

    // Build registered client
    const registeredClient: RegisteredClient = {
      client_id: clientId,
      client_secret:
        tokenEndpointAuthMethod !== "none" ? clientSecret : undefined,
      redirect_uris: body.redirect_uris,
      client_name: body.client_name,
      grant_types: body.grant_types || ["authorization_code"],
      response_types: body.response_types || ["code"],
      token_endpoint_auth_method: tokenEndpointAuthMethod,
      created_at: Date.now(),
    };

    // Store in KV
    await c.env.OAUTH_KV.put(
      `client:${clientId}`,
      JSON.stringify(registeredClient),
      {
        expirationTtl: 86400 * 365, // 1 year
      }
    );

    // Build response
    const response: ClientRegistrationResponse = {
      client_id: clientId,
      client_secret: registeredClient.client_secret,
      client_id_issued_at: Math.floor(Date.now() / 1000),
      client_secret_expires_at: 0, // Never expires
      redirect_uris: registeredClient.redirect_uris,
      token_endpoint_auth_method: registeredClient.token_endpoint_auth_method,
      grant_types: registeredClient.grant_types,
      response_types: registeredClient.response_types,
      client_name: registeredClient.client_name,
    };

    return c.json(response, 201);
  } catch (error) {
    console.error("Client registration error:", error);
    return c.json(
      {
        error: "invalid_client_metadata",
        error_description: "Failed to parse registration request",
      },
      400
    );
  }
});

/**
 * Get a registered client by ID.
 */
export async function getRegisteredClient(
  kv: import("@cloudflare/workers-types").KVNamespace,
  clientId: string
): Promise<RegisteredClient | null> {
  const data = await kv.get(`client:${clientId}`);
  if (!data) return null;
  return JSON.parse(data) as RegisteredClient;
}

/**
 * Generate WWW-Authenticate header for 401 responses.
 */
export function getWWWAuthenticateHeader(baseUrl: string): string {
  const resourceMetadataUrl = `${baseUrl}/.well-known/oauth-protected-resource`;
  return `Bearer resource_metadata="${resourceMetadataUrl}"`;
}

export { app as OAuthMetadataHandler };
export default app;
