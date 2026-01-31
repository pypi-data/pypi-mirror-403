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
