/**
 * Type definitions for video-to-claude remote MCP server.
 */

import type { KVNamespace, R2Bucket } from "@cloudflare/workers-types";

/**
 * Cloudflare Worker environment bindings.
 */
export interface Env {
  // R2 bucket for storing processed videos
  R2: R2Bucket;

  // KV namespace for OAuth tokens
  OAUTH_KV: KVNamespace;

  // GitHub OAuth credentials (set via wrangler secret put)
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;

  // Cookie encryption key for OAuth state
  COOKIE_ENCRYPTION_KEY: string;

  // Environment indicator
  ENVIRONMENT: string;
}

/**
 * User properties from OAuth authentication.
 */
export interface AuthProps {
  login: string;
  name: string;
  email: string;
  accessToken: string;
}

/**
 * Video manifest structure (matches Python version).
 */
export interface VideoManifest {
  version: string;
  generated_at: string;
  generator: string;
  source: {
    filename: string;
    path: string;
  };
  video: {
    duration_seconds: number;
    duration_formatted: string;
    resolution: string;
    width: number;
    height: number;
    fps: number;
    codec: string;
  };
  frames: {
    count: number;
    interval_seconds: number;
    files: FrameInfo[];
  };
  audio: {
    available: boolean;
    codec?: string;
    sample_rate?: number;
    characteristics?: Record<string, number>;
    frequency_analysis?: Record<string, unknown>;
    description?: string;
  };
  files: {
    manifest: string;
    frames: string[];
    audio_analysis?: string;
    spectrogram?: string;
    waveform?: string;
  };
  viewing_instructions: string;
}

/**
 * Frame metadata.
 */
export interface FrameInfo {
  filename: string;
  index: number;
  timestamp_seconds: number;
  timestamp_formatted: string;
}

/**
 * Video index stored in R2 for listing.
 */
export interface VideoIndex {
  video_id: string;
  name: string;
  files: string[];
  manifest: string;
  uploaded_at?: string;
  owner?: string; // GitHub login of the user who uploaded
}

/**
 * Audio analysis structure.
 */
export interface AudioAnalysis {
  metadata: {
    sample_rate: number;
    duration_seconds: number;
    total_samples: number;
  };
  overall_characteristics: {
    rms_energy: number;
    peak_amplitude: number;
    dynamic_range_db: number;
    zero_crossing_rate: number;
  };
  frequency_analysis: {
    frequency_band_energy_percent: Record<string, number>;
    spectral_centroid_hz: number;
  };
  temporal_analysis: Array<{
    time_seconds: number;
    rms_energy: number;
    energy_level: string;
  }>;
  notable_events: Array<{
    time_seconds: number;
    event_type: string;
    magnitude: number;
  }>;
  text_description: string;
}

/**
 * RFC 9728 - OAuth 2.0 Protected Resource Metadata
 */
export interface ProtectedResourceMetadata {
  resource: string;
  authorization_servers: string[];
  bearer_methods_supported?: string[];
  resource_signing_alg_values_supported?: string[];
  resource_documentation?: string;
  resource_policy_uri?: string;
  resource_tos_uri?: string;
}

/**
 * RFC 8414 - OAuth 2.0 Authorization Server Metadata
 */
export interface AuthorizationServerMetadata {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  registration_endpoint?: string;
  scopes_supported?: string[];
  response_types_supported: string[];
  response_modes_supported?: string[];
  grant_types_supported?: string[];
  token_endpoint_auth_methods_supported?: string[];
  code_challenge_methods_supported?: string[];
  service_documentation?: string;
}

/**
 * RFC 7591 - OAuth 2.0 Dynamic Client Registration
 */
export interface ClientRegistrationRequest {
  redirect_uris: string[];
  token_endpoint_auth_method?: string;
  grant_types?: string[];
  response_types?: string[];
  client_name?: string;
  client_uri?: string;
  logo_uri?: string;
  scope?: string;
  contacts?: string[];
  tos_uri?: string;
  policy_uri?: string;
  software_id?: string;
  software_version?: string;
}

export interface ClientRegistrationResponse {
  client_id: string;
  client_secret?: string;
  client_id_issued_at?: number;
  client_secret_expires_at?: number;
  redirect_uris: string[];
  token_endpoint_auth_method: string;
  grant_types: string[];
  response_types: string[];
  client_name?: string;
}

/**
 * Registered OAuth client stored in KV.
 */
export interface RegisteredClient {
  client_id: string;
  client_secret?: string;
  redirect_uris: string[];
  client_name?: string;
  grant_types: string[];
  response_types: string[];
  token_endpoint_auth_method: string;
  created_at: number;
}
