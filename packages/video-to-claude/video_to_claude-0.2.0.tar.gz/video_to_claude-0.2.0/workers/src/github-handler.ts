/**
 * GitHub OAuth handler for video-to-claude remote MCP server.
 */

import { Hono } from "hono";
import { Octokit } from "@octokit/rest";
import type { Env, AuthProps } from "./types.js";

// OAuth state stored in cookies
interface OAuthState {
  clientId: string;
  redirectUri: string;
  state: string;
  codeChallenge?: string;
  scope?: string;
}

const app = new Hono<{ Bindings: Env }>();

/**
 * Authorization endpoint - redirects to GitHub OAuth.
 */
app.get("/authorize", async (c) => {
  const url = new URL(c.req.url);
  const clientId = url.searchParams.get("client_id");
  const redirectUri = url.searchParams.get("redirect_uri");
  const state = url.searchParams.get("state");
  const scope = url.searchParams.get("scope");
  const codeChallenge = url.searchParams.get("code_challenge");

  if (!clientId || !redirectUri || !state) {
    return c.text("Missing required OAuth parameters", 400);
  }

  // Store OAuth state for callback
  const oauthState: OAuthState = {
    clientId,
    redirectUri,
    state,
    codeChallenge,
    scope,
  };

  // Encrypt and store in KV
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
    return c.text(`OAuth error: ${error}`, 400);
  }

  if (!code || !state) {
    return c.text("Missing code or state parameter", 400);
  }

  // Retrieve OAuth state from KV
  const stateKey = `oauth_state:${state}`;
  const storedState = await c.env.OAUTH_KV.get(stateKey);

  if (!storedState) {
    return c.text("Invalid or expired state", 400);
  }

  const oauthState: OAuthState = JSON.parse(storedState);

  // Exchange code for access token
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
    return c.text(
      `Token exchange failed: ${tokenData.error_description || tokenData.error}`,
      400
    );
  }

  const accessToken = tokenData.access_token;

  // Get user info from GitHub
  const octokit = new Octokit({ auth: accessToken });
  const { data: user } = await octokit.rest.users.getAuthenticated();

  // Get user's email (may be private)
  let email = user.email;
  if (!email) {
    try {
      const { data: emails } = await octokit.rest.users.listEmailsForAuthenticatedUser();
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
    accessToken,
  };

  // Generate a session token
  const sessionToken = crypto.randomUUID();
  const sessionKey = `session:${sessionToken}`;

  // Store session in KV
  await c.env.OAUTH_KV.put(sessionKey, JSON.stringify(authProps), {
    expirationTtl: 86400, // 24 hours
  });

  // Clean up OAuth state
  await c.env.OAUTH_KV.delete(stateKey);

  // Redirect back to client with authorization code
  const redirectUrl = new URL(oauthState.redirectUri);
  redirectUrl.searchParams.set("code", sessionToken);
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

  if (contentType?.includes("application/x-www-form-urlencoded")) {
    const body = await c.req.text();
    const params = new URLSearchParams(body);
    code = params.get("code");
    grantType = params.get("grant_type");
  } else if (contentType?.includes("application/json")) {
    const body = (await c.req.json()) as { code?: string; grant_type?: string };
    code = body.code || null;
    grantType = body.grant_type || null;
  }

  if (grantType !== "authorization_code" || !code) {
    return c.json({ error: "invalid_request" }, 400);
  }

  // Look up session
  const sessionKey = `session:${code}`;
  const sessionData = await c.env.OAUTH_KV.get(sessionKey);

  if (!sessionData) {
    return c.json({ error: "invalid_grant" }, 400);
  }

  const authProps: AuthProps = JSON.parse(sessionData);

  // Generate a new access token for the MCP client
  const mcpToken = crypto.randomUUID();
  const tokenKey = `token:${mcpToken}`;

  // Store token in KV
  await c.env.OAUTH_KV.put(tokenKey, JSON.stringify(authProps), {
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
