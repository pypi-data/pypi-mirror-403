/**
 * GitHub OAuth handler for video-to-claude remote MCP server.
 *
 * Supports:
 * - Standard OAuth 2.1 flow with PKCE
 * - Dynamic Client Registration (RFC 7591)
 * - CLI mode for video-to-claude CLI uploads
 */

import { Hono } from "hono";
import { Octokit } from "@octokit/rest";
import type { Env, AuthProps, RegisteredClient } from "./types.js";
import { getRegisteredClient } from "./oauth-metadata.js";

// OAuth state stored in KV
interface OAuthState {
  clientId: string;
  redirectUri: string;
  state: string;
  codeChallenge?: string;
  codeChallengeMethod?: string;
  scope?: string;
  resource?: string;
}

const app = new Hono<{ Bindings: Env }>();

/**
 * Validate a redirect URI against a registered client.
 */
function validateRedirectUri(
  client: RegisteredClient | null,
  redirectUri: string,
  isCLIMode: boolean
): boolean {
  // CLI mode allows localhost
  if (isCLIMode) {
    try {
      const parsed = new URL(redirectUri);
      return (
        parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1"
      );
    } catch {
      return false;
    }
  }

  // For registered clients, check against registered URIs
  if (client) {
    return client.redirect_uris.includes(redirectUri);
  }

  return false;
}

/**
 * Verify PKCE code challenge.
 */
async function verifyCodeChallenge(
  codeVerifier: string,
  codeChallenge: string,
  method: string = "S256"
): Promise<boolean> {
  if (method !== "S256") {
    return false;
  }

  // Generate S256 challenge from verifier
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = new Uint8Array(hashBuffer);

  // Base64url encode
  const base64 = btoa(String.fromCharCode(...hashArray))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  return base64 === codeChallenge;
}

/**
 * Authorization endpoint - redirects to GitHub OAuth.
 *
 * Supports:
 * 1. Full OAuth 2.1 flow with PKCE (for MCP clients like Claude)
 * 2. CLI mode: just redirect_uri (for video-to-claude CLI uploads)
 */
app.get("/authorize", async (c) => {
  const url = new URL(c.req.url);
  const clientId = url.searchParams.get("client_id");
  const redirectUri = url.searchParams.get("redirect_uri");
  const state = url.searchParams.get("state") || crypto.randomUUID();
  const scope = url.searchParams.get("scope");
  const codeChallenge = url.searchParams.get("code_challenge");
  const codeChallengeMethod =
    url.searchParams.get("code_challenge_method") || "S256";
  const resource = url.searchParams.get("resource");

  // CLI mode: only redirect_uri is required (no client_id)
  const isCLIMode = !clientId && redirectUri;

  // Standard mode requires client_id, redirect_uri, state
  if (!isCLIMode && (!clientId || !redirectUri || !state)) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Missing required OAuth parameters",
      },
      400
    );
  }

  if (!redirectUri) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Missing redirect_uri parameter",
      },
      400
    );
  }

  // For registered clients, validate the client and redirect_uri
  let registeredClient: RegisteredClient | null = null;
  if (clientId && clientId !== "cli") {
    registeredClient = await getRegisteredClient(c.env.OAUTH_KV, clientId);
    if (!registeredClient) {
      return c.json(
        {
          error: "invalid_client",
          error_description: "Unknown client_id",
        },
        400
      );
    }
  }

  // Validate redirect URI
  if (!validateRedirectUri(registeredClient, redirectUri, !!isCLIMode)) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Invalid redirect_uri",
      },
      400
    );
  }

  // Store OAuth state for callback
  const oauthState: OAuthState = {
    clientId: clientId || "cli",
    redirectUri,
    state,
    codeChallenge: codeChallenge || undefined,
    codeChallengeMethod: codeChallenge ? codeChallengeMethod : undefined,
    scope: scope || undefined,
    resource: resource || undefined,
  };

  // Store in KV
  const stateKey = `oauth_state:${state}`;
  await c.env.OAUTH_KV.put(stateKey, JSON.stringify(oauthState), {
    expirationTtl: 600, // 10 minutes
  });

  // Redirect to GitHub OAuth
  const githubAuthUrl = new URL("https://github.com/login/oauth/authorize");
  githubAuthUrl.searchParams.set("client_id", c.env.GITHUB_CLIENT_ID);
  githubAuthUrl.searchParams.set(
    "redirect_uri",
    new URL("/callback", url.origin).href
  );
  githubAuthUrl.searchParams.set("state", state);
  githubAuthUrl.searchParams.set("scope", "read:user user:email");

  return c.redirect(githubAuthUrl.href);
});

/**
 * Callback endpoint - handles GitHub OAuth callback.
 */
app.get("/callback", async (c) => {
  const url = new URL(c.req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");

  if (error) {
    return c.json({ error: "oauth_error", error_description: error }, 400);
  }

  if (!code || !state) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Missing code or state parameter",
      },
      400
    );
  }

  // Retrieve OAuth state from KV
  const stateKey = `oauth_state:${state}`;
  const storedState = await c.env.OAUTH_KV.get(stateKey);

  if (!storedState) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Invalid or expired state",
      },
      400
    );
  }

  const oauthState: OAuthState = JSON.parse(storedState);

  // Exchange code for access token with GitHub
  const tokenResponse = await fetch(
    "https://github.com/login/oauth/access_token",
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_id: c.env.GITHUB_CLIENT_ID,
        client_secret: c.env.GITHUB_CLIENT_SECRET,
        code,
        redirect_uri: new URL("/callback", url.origin).href,
      }),
    }
  );

  const tokenData = (await tokenResponse.json()) as {
    access_token?: string;
    error?: string;
    error_description?: string;
  };

  if (tokenData.error || !tokenData.access_token) {
    return c.json(
      {
        error: "token_exchange_failed",
        error_description:
          tokenData.error_description ||
          tokenData.error ||
          JSON.stringify(tokenData),
      },
      400
    );
  }

  const githubAccessToken = tokenData.access_token;

  // Get user info from GitHub
  const octokit = new Octokit({ auth: githubAccessToken });
  const { data: user } = await octokit.rest.users.getAuthenticated();

  // Get user's email (may be private)
  let email = user.email;
  if (!email) {
    try {
      const { data: emails } =
        await octokit.rest.users.listEmailsForAuthenticatedUser();
      const primaryEmail = emails.find((e) => e.primary);
      email = primaryEmail?.email || emails[0]?.email || "";
    } catch {
      email = "";
    }
  }

  // Create auth props
  const authProps: AuthProps = {
    login: user.login,
    name: user.name || user.login,
    email: email || "",
    accessToken: githubAccessToken,
  };

  // Clean up OAuth state
  await c.env.OAUTH_KV.delete(stateKey);

  // CLI mode: return token directly (localhost callbacks)
  if (
    oauthState.clientId === "cli" ||
    oauthState.redirectUri.includes("localhost") ||
    oauthState.redirectUri.includes("127.0.0.1")
  ) {
    // Generate MCP token directly for CLI
    const mcpToken = crypto.randomUUID();
    const tokenKey = `token:${mcpToken}`;
    await c.env.OAUTH_KV.put(tokenKey, JSON.stringify(authProps), {
      expirationTtl: 604800, // 7 days for CLI tokens
    });

    const redirectUrl = new URL(oauthState.redirectUri);
    redirectUrl.searchParams.set("token", mcpToken);
    return c.redirect(redirectUrl.href);
  }

  // Standard OAuth flow: return authorization code
  // Generate authorization code (this will be exchanged for access token)
  const authCode = crypto.randomUUID();
  const authCodeKey = `auth_code:${authCode}`;

  // Store auth code data (includes PKCE info for validation at token endpoint)
  await c.env.OAUTH_KV.put(
    authCodeKey,
    JSON.stringify({
      authProps,
      clientId: oauthState.clientId,
      redirectUri: oauthState.redirectUri,
      codeChallenge: oauthState.codeChallenge,
      codeChallengeMethod: oauthState.codeChallengeMethod,
      resource: oauthState.resource,
    }),
    {
      expirationTtl: 600, // 10 minutes
    }
  );

  const redirectUrl = new URL(oauthState.redirectUri);
  redirectUrl.searchParams.set("code", authCode);
  redirectUrl.searchParams.set("state", oauthState.state);

  return c.redirect(redirectUrl.href);
});

/**
 * Token endpoint - exchanges authorization code for access token.
 */
app.post("/token", async (c) => {
  const contentType = c.req.header("Content-Type");

  let code: string | null = null;
  let grantType: string | null = null;
  let clientId: string | null = null;
  let clientSecret: string | null = null;
  let codeVerifier: string | null = null;
  let redirectUri: string | null = null;

  // Parse request body
  if (contentType?.includes("application/x-www-form-urlencoded")) {
    const body = await c.req.text();
    const params = new URLSearchParams(body);
    code = params.get("code");
    grantType = params.get("grant_type");
    clientId = params.get("client_id");
    clientSecret = params.get("client_secret");
    codeVerifier = params.get("code_verifier");
    redirectUri = params.get("redirect_uri");
  } else if (contentType?.includes("application/json")) {
    const body = (await c.req.json()) as Record<string, string>;
    code = body.code || null;
    grantType = body.grant_type || null;
    clientId = body.client_id || null;
    clientSecret = body.client_secret || null;
    codeVerifier = body.code_verifier || null;
    redirectUri = body.redirect_uri || null;
  }

  // Check for client credentials in Authorization header (Basic auth)
  const authHeader = c.req.header("Authorization");
  if (authHeader?.startsWith("Basic ")) {
    const decoded = atob(authHeader.slice(6));
    const [headerClientId, headerClientSecret] = decoded.split(":");
    clientId = clientId || headerClientId;
    clientSecret = clientSecret || headerClientSecret;
  }

  // Validate grant type
  if (grantType !== "authorization_code") {
    return c.json(
      {
        error: "unsupported_grant_type",
        error_description: "Only authorization_code grant is supported",
      },
      400
    );
  }

  if (!code) {
    return c.json(
      {
        error: "invalid_request",
        error_description: "Missing authorization code",
      },
      400
    );
  }

  // Look up authorization code
  const authCodeKey = `auth_code:${code}`;
  const authCodeData = await c.env.OAUTH_KV.get(authCodeKey);

  if (!authCodeData) {
    return c.json(
      {
        error: "invalid_grant",
        error_description: "Invalid or expired authorization code",
      },
      400
    );
  }

  const codeData = JSON.parse(authCodeData) as {
    authProps: AuthProps;
    clientId: string;
    redirectUri: string;
    codeChallenge?: string;
    codeChallengeMethod?: string;
    resource?: string;
  };

  // Validate client_id matches
  if (clientId && clientId !== codeData.clientId) {
    return c.json(
      {
        error: "invalid_grant",
        error_description: "client_id mismatch",
      },
      400
    );
  }

  // Validate redirect_uri matches (if provided)
  if (redirectUri && redirectUri !== codeData.redirectUri) {
    return c.json(
      {
        error: "invalid_grant",
        error_description: "redirect_uri mismatch",
      },
      400
    );
  }

  // Validate PKCE if code_challenge was provided during authorization
  if (codeData.codeChallenge) {
    if (!codeVerifier) {
      return c.json(
        {
          error: "invalid_request",
          error_description: "code_verifier required for PKCE",
        },
        400
      );
    }

    const isValid = await verifyCodeChallenge(
      codeVerifier,
      codeData.codeChallenge,
      codeData.codeChallengeMethod
    );

    if (!isValid) {
      return c.json(
        {
          error: "invalid_grant",
          error_description: "Invalid code_verifier",
        },
        400
      );
    }
  }

  // If client has a secret, validate it
  if (codeData.clientId !== "cli") {
    const registeredClient = await getRegisteredClient(
      c.env.OAUTH_KV,
      codeData.clientId
    );
    if (
      registeredClient?.client_secret &&
      registeredClient.token_endpoint_auth_method !== "none"
    ) {
      if (clientSecret !== registeredClient.client_secret) {
        return c.json(
          {
            error: "invalid_client",
            error_description: "Invalid client credentials",
          },
          401
        );
      }
    }
  }

  // Delete the authorization code (single use)
  await c.env.OAUTH_KV.delete(authCodeKey);

  // Generate access token
  const mcpToken = crypto.randomUUID();
  const tokenKey = `token:${mcpToken}`;

  // Store token in KV
  await c.env.OAUTH_KV.put(tokenKey, JSON.stringify(codeData.authProps), {
    expirationTtl: 86400, // 24 hours
  });

  return c.json({
    access_token: mcpToken,
    token_type: "Bearer",
    expires_in: 86400,
  });
});

export { app as GitHubHandler };
export default app;
