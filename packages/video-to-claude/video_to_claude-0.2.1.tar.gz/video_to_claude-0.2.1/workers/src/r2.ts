/**
 * R2 storage helpers for video-to-claude.
 */

import type { R2Bucket } from "@cloudflare/workers-types";
import type { VideoIndex, VideoManifest, AudioAnalysis } from "./types.js";

/**
 * List videos in the R2 bucket, optionally filtered by owner.
 */
export async function listVideos(
  r2: R2Bucket,
  owner?: string
): Promise<VideoIndex[]> {
  const videos: VideoIndex[] = [];

  // List all objects and find _index.json files
  let cursor: string | undefined;

  do {
    const listed = await r2.list({ cursor });
    cursor = listed.truncated ? listed.cursor : undefined;

    for (const object of listed.objects) {
      if (object.key.endsWith("/_index.json")) {
        try {
          const indexObj = await r2.get(object.key);
          if (indexObj) {
            const indexData = (await indexObj.json()) as VideoIndex;
            // Filter by owner if specified
            if (!owner || indexData.owner === owner) {
              videos.push(indexData);
            }
          }
        } catch (error) {
          // Skip invalid index files
          console.error(`Failed to read index ${object.key}:`, error);
        }
      }
    }
  } while (cursor);

  return videos;
}

/**
 * Get the owner of a video.
 */
export async function getVideoOwner(
  r2: R2Bucket,
  videoId: string
): Promise<string | null> {
  const key = `${videoId}/_index.json`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  const indexData = (await obj.json()) as VideoIndex;
  return indexData.owner || null;
}

/**
 * Get a video's manifest from R2.
 */
export async function getManifest(
  r2: R2Bucket,
  videoId: string
): Promise<VideoManifest | null> {
  const key = `${videoId}/manifest.json`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  return (await obj.json()) as VideoManifest;
}

/**
 * Get a frame image from R2.
 */
export async function getFrame(
  r2: R2Bucket,
  videoId: string,
  frameNumber: number
): Promise<{ data: ArrayBuffer; contentType: string } | null> {
  const key = `${videoId}/frame_${frameNumber.toString().padStart(3, "0")}.jpg`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  return {
    data: await obj.arrayBuffer(),
    contentType: obj.httpMetadata?.contentType || "image/jpeg",
  };
}

/**
 * Get the spectrogram image from R2.
 */
export async function getSpectrogram(
  r2: R2Bucket,
  videoId: string
): Promise<{ data: ArrayBuffer; contentType: string } | null> {
  const key = `${videoId}/spectrogram.png`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  return {
    data: await obj.arrayBuffer(),
    contentType: obj.httpMetadata?.contentType || "image/png",
  };
}

/**
 * Get the waveform image from R2.
 */
export async function getWaveform(
  r2: R2Bucket,
  videoId: string
): Promise<{ data: ArrayBuffer; contentType: string } | null> {
  const key = `${videoId}/waveform.png`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  return {
    data: await obj.arrayBuffer(),
    contentType: obj.httpMetadata?.contentType || "image/png",
  };
}

/**
 * Get the audio analysis from R2.
 */
export async function getAudioAnalysis(
  r2: R2Bucket,
  videoId: string
): Promise<AudioAnalysis | null> {
  const key = `${videoId}/audio_analysis.json`;
  const obj = await r2.get(key);

  if (!obj) {
    return null;
  }

  return (await obj.json()) as AudioAnalysis;
}

/**
 * Check if a video exists in R2.
 */
export async function videoExists(
  r2: R2Bucket,
  videoId: string
): Promise<boolean> {
  const key = `${videoId}/manifest.json`;
  const obj = await r2.head(key);
  return obj !== null;
}

/**
 * Get available frame numbers for a video.
 */
export async function getAvailableFrames(
  r2: R2Bucket,
  videoId: string
): Promise<number[]> {
  const frames: number[] = [];
  const prefix = `${videoId}/frame_`;

  let cursor: string | undefined;

  do {
    const listed = await r2.list({ prefix, cursor });
    cursor = listed.truncated ? listed.cursor : undefined;

    for (const object of listed.objects) {
      // Extract frame number from key like "video-id/frame_001.jpg"
      const match = object.key.match(/frame_(\d+)\.jpg$/);
      if (match) {
        frames.push(parseInt(match[1], 10));
      }
    }
  } while (cursor);

  return frames.sort((a, b) => a - b);
}

/**
 * Convert ArrayBuffer to base64 string.
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Upload a file to R2.
 */
export async function uploadFile(
  r2: R2Bucket,
  key: string,
  data: ArrayBuffer | string,
  contentType: string
): Promise<void> {
  await r2.put(key, data, {
    httpMetadata: { contentType },
  });
}

/**
 * Create a video ID from name.
 */
export function createVideoId(name: string): string {
  // Slugify the name
  let slug = name.toLowerCase();
  slug = slug.replace(/[\s_]+/g, "-");
  slug = slug.replace(/[^a-z0-9-]/g, "");
  slug = slug.replace(/-+/g, "-");
  slug = slug.replace(/^-|-$/g, "");

  // Add random suffix for uniqueness
  const suffix = Math.random().toString(36).substring(2, 8);
  return `${slug}-${suffix}`;
}

/**
 * Upload a complete video package to R2.
 */
export async function uploadVideo(
  r2: R2Bucket,
  videoId: string,
  name: string,
  files: Map<string, { data: ArrayBuffer; contentType: string }>,
  owner?: string
): Promise<void> {
  const uploadedFiles: string[] = [];

  // Upload all files
  for (const [filename, { data, contentType }] of files) {
    const key = `${videoId}/${filename}`;
    await uploadFile(r2, key, data, contentType);
    uploadedFiles.push(filename);
  }

  // Create index file with owner
  const indexData: VideoIndex = {
    video_id: videoId,
    name,
    files: uploadedFiles,
    manifest: `${videoId}/manifest.json`,
    uploaded_at: new Date().toISOString(),
    owner,
  };

  await uploadFile(
    r2,
    `${videoId}/_index.json`,
    JSON.stringify(indexData, null, 2),
    "application/json"
  );
}
