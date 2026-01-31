/**
 * MCP tool implementations for video-to-claude remote server.
 */

import { z } from "zod";
import type { R2Bucket } from "@cloudflare/workers-types";
import {
  listVideos,
  getManifest,
  getFrame,
  getSpectrogram,
  getWaveform,
  getAudioAnalysis,
  getAvailableFrames,
  getVideoOwner,
  arrayBufferToBase64,
} from "./r2.js";

/**
 * Tool response type for MCP.
 */
interface ToolResponse {
  content: Array<{
    type: "text" | "image";
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
}

/**
 * Create a text response.
 */
function textResponse(text: string): ToolResponse {
  return {
    content: [{ type: "text", text }],
  };
}

/**
 * Create an error response.
 */
function errorResponse(message: string): ToolResponse {
  return {
    content: [{ type: "text", text: `**Error:** ${message}` }],
  };
}

/**
 * Create an image response.
 */
function imageResponse(
  base64Data: string,
  mimeType: string,
  caption?: string
): ToolResponse {
  const content: ToolResponse["content"] = [];

  if (caption) {
    content.push({ type: "text", text: caption });
  }

  content.push({
    type: "image",
    data: base64Data,
    mimeType,
  });

  return { content };
}

// Tool schemas using Zod
export const ListVideosSchema = z.object({});

export const GetManifestSchema = z.object({
  video_id: z.string().describe("The video ID (shown in list_videos output)"),
});

export const GetFrameSchema = z.object({
  video_id: z.string().describe("The video ID"),
  frame_number: z.number().int().positive().describe("Frame number (1-indexed)"),
});

export const GetFramesSchema = z.object({
  video_id: z.string().describe("The video ID"),
  start: z.number().int().positive().optional().describe("Start frame number (default: 1)"),
  end: z.number().int().positive().optional().describe("End frame number (default: last frame)"),
  max_frames: z.number().int().positive().max(10).optional().describe("Maximum frames to return (default: 5, max: 10)"),
});

export const GetSpectrogramSchema = z.object({
  video_id: z.string().describe("The video ID"),
});

export const GetWaveformSchema = z.object({
  video_id: z.string().describe("The video ID"),
});

export const GetAudioAnalysisSchema = z.object({
  video_id: z.string().describe("The video ID"),
});

/**
 * List videos available to the current user.
 */
export async function handleListVideos(
  r2: R2Bucket,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Only show videos owned by this user
    const videos = await listVideos(r2, userLogin);

    if (videos.length === 0) {
      return textResponse(
        "No videos found. Upload videos using the video-to-claude CLI:\n\n" +
          "```bash\n" +
          "video-to-claude convert your_video.mp4\n" +
          "video-to-claude upload ./your_video_for_claude/ --name \"Your Video\"\n" +
          "```"
      );
    }

    const videoList = videos
      .map((v) => `- **${v.name}** (ID: \`${v.video_id}\`)`)
      .join("\n");

    return textResponse(
      `**Your Videos (${videos.length}):**\n\n${videoList}\n\n` +
        "Use `get_manifest(video_id)` to get details about a specific video."
    );
  } catch (error) {
    return errorResponse(`Failed to list videos: ${error}`);
  }
}

/**
 * Check if user owns a video. Returns error response if not.
 */
async function checkOwnership(
  r2: R2Bucket,
  videoId: string,
  userLogin?: string
): Promise<ToolResponse | null> {
  const owner = await getVideoOwner(r2, videoId);

  // Video doesn't exist
  if (owner === null) {
    return errorResponse(`Video not found: ${videoId}`);
  }

  // Check ownership (if user is authenticated)
  if (userLogin && owner && owner !== userLogin) {
    return errorResponse(`Access denied: you don't own this video`);
  }

  return null; // Access granted
}

/**
 * Get the manifest for a specific video.
 */
export async function handleGetManifest(
  r2: R2Bucket,
  args: z.infer<typeof GetManifestSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const manifest = await getManifest(r2, args.video_id);

    if (!manifest) {
      return errorResponse(`Video not found: ${args.video_id}`);
    }

    const summary = [
      `**${manifest.source.filename}**`,
      "",
      "**Video Info:**",
      `- Duration: ${manifest.video.duration_formatted} (${manifest.video.duration_seconds}s)`,
      `- Resolution: ${manifest.video.resolution}`,
      `- FPS: ${manifest.video.fps}`,
      `- Codec: ${manifest.video.codec}`,
      "",
      "**Frames:**",
      `- Count: ${manifest.frames.count}`,
      `- Interval: ${manifest.frames.interval_seconds}s between frames`,
      "",
      "**Audio:**",
      `- Available: ${manifest.audio.available ? "Yes" : "No"}`,
    ];

    if (manifest.audio.available && manifest.audio.description) {
      summary.push(`- Description: ${manifest.audio.description}`);
    }

    summary.push("");
    summary.push("**Available Files:**");
    summary.push(`- Frames: frame_001.jpg through frame_${manifest.frames.count.toString().padStart(3, "0")}.jpg`);

    if (manifest.files.spectrogram) {
      summary.push("- Spectrogram: spectrogram.png");
    }
    if (manifest.files.waveform) {
      summary.push("- Waveform: waveform.png");
    }
    if (manifest.files.audio_analysis) {
      summary.push("- Audio Analysis: audio_analysis.json");
    }

    summary.push("");
    summary.push("**Instructions:**");
    summary.push(manifest.viewing_instructions);

    return textResponse(summary.join("\n"));
  } catch (error) {
    return errorResponse(`Failed to get manifest: ${error}`);
  }
}

/**
 * Get a single frame image.
 */
export async function handleGetFrame(
  r2: R2Bucket,
  args: z.infer<typeof GetFrameSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const frame = await getFrame(r2, args.video_id, args.frame_number);

    if (!frame) {
      // Try to get available frames
      const available = await getAvailableFrames(r2, args.video_id);
      if (available.length === 0) {
        return errorResponse(`Video not found: ${args.video_id}`);
      }
      return errorResponse(
        `Frame ${args.frame_number} not found. Available frames: ${available[0]}-${available[available.length - 1]}`
      );
    }

    const manifest = await getManifest(r2, args.video_id);
    let caption = `Frame ${args.frame_number}`;

    if (manifest) {
      const frameInfo = manifest.frames.files.find(
        (f) => f.index === args.frame_number
      );
      if (frameInfo) {
        caption = `Frame ${args.frame_number} at ${frameInfo.timestamp_formatted}`;
      }
    }

    return imageResponse(
      arrayBufferToBase64(frame.data),
      frame.contentType,
      caption
    );
  } catch (error) {
    return errorResponse(`Failed to get frame: ${error}`);
  }
}

/**
 * Get multiple frames from a video.
 */
export async function handleGetFrames(
  r2: R2Bucket,
  args: z.infer<typeof GetFramesSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const manifest = await getManifest(r2, args.video_id);

    if (!manifest) {
      return errorResponse(`Video not found: ${args.video_id}`);
    }

    const totalFrames = manifest.frames.count;
    const start = args.start ?? 1;
    const end = args.end ?? totalFrames;
    const maxFrames = args.max_frames ?? 5;

    // Calculate which frames to fetch (evenly distributed)
    const range = end - start + 1;
    const step = Math.max(1, Math.floor(range / maxFrames));
    const frameNumbers: number[] = [];

    for (let i = start; i <= end && frameNumbers.length < maxFrames; i += step) {
      frameNumbers.push(i);
    }

    const content: ToolResponse["content"] = [];

    content.push({
      type: "text",
      text: `**Frames ${start}-${end}** (showing ${frameNumbers.length} of ${range}):`,
    });

    for (const frameNum of frameNumbers) {
      const frame = await getFrame(r2, args.video_id, frameNum);
      if (frame) {
        const frameInfo = manifest.frames.files.find((f) => f.index === frameNum);
        const timestamp = frameInfo
          ? frameInfo.timestamp_formatted
          : "unknown";

        content.push({
          type: "text",
          text: `\n**Frame ${frameNum}** (${timestamp}):`,
        });

        content.push({
          type: "image",
          data: arrayBufferToBase64(frame.data),
          mimeType: frame.contentType,
        });
      }
    }

    return { content };
  } catch (error) {
    return errorResponse(`Failed to get frames: ${error}`);
  }
}

/**
 * Get the spectrogram image.
 */
export async function handleGetSpectrogram(
  r2: R2Bucket,
  args: z.infer<typeof GetSpectrogramSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const spectrogram = await getSpectrogram(r2, args.video_id);

    if (!spectrogram) {
      return errorResponse(
        "No spectrogram available. The video may not have audio or audio was not processed."
      );
    }

    return imageResponse(
      arrayBufferToBase64(spectrogram.data),
      spectrogram.contentType,
      "**Spectrogram** - Shows frequency content over time:\n" +
        "- X-axis: Time (seconds)\n" +
        "- Y-axis: Frequency (Hz, 0-8000 range)\n" +
        "- Color: Power/intensity (dB)"
    );
  } catch (error) {
    return errorResponse(`Failed to get spectrogram: ${error}`);
  }
}

/**
 * Get the waveform image.
 */
export async function handleGetWaveform(
  r2: R2Bucket,
  args: z.infer<typeof GetWaveformSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const waveform = await getWaveform(r2, args.video_id);

    if (!waveform) {
      return errorResponse(
        "No waveform available. The video may not have audio or audio was not processed."
      );
    }

    return imageResponse(
      arrayBufferToBase64(waveform.data),
      waveform.contentType,
      "**Waveform** - Shows amplitude over time:\n" +
        "- X-axis: Time (seconds)\n" +
        "- Y-axis: Amplitude (-1 to 1, normalized)"
    );
  } catch (error) {
    return errorResponse(`Failed to get waveform: ${error}`);
  }
}

/**
 * Get detailed audio analysis.
 */
export async function handleGetAudioAnalysis(
  r2: R2Bucket,
  args: z.infer<typeof GetAudioAnalysisSchema>,
  userLogin?: string
): Promise<ToolResponse> {
  try {
    // Check ownership first
    const accessError = await checkOwnership(r2, args.video_id, userLogin);
    if (accessError) return accessError;

    const analysis = await getAudioAnalysis(r2, args.video_id);

    if (!analysis) {
      return errorResponse(
        "No audio analysis available. The video may not have audio or audio was not processed."
      );
    }

    const summary = [
      "**Audio Analysis**",
      "",
      "**Metadata:**",
      `- Duration: ${analysis.metadata.duration_seconds}s`,
      `- Sample Rate: ${analysis.metadata.sample_rate} Hz`,
      "",
      "**Characteristics:**",
      `- RMS Energy: ${analysis.overall_characteristics.rms_energy}`,
      `- Peak Amplitude: ${analysis.overall_characteristics.peak_amplitude}`,
      `- Dynamic Range: ${analysis.overall_characteristics.dynamic_range_db} dB`,
      "",
      "**Frequency Distribution:**",
    ];

    for (const [band, energy] of Object.entries(
      analysis.frequency_analysis.frequency_band_energy_percent
    )) {
      const bandName = band.replace(/_/g, " ").replace(/hz/g, "Hz");
      summary.push(`- ${bandName}: ${energy}%`);
    }

    summary.push("");
    summary.push(`**Spectral Centroid:** ${analysis.frequency_analysis.spectral_centroid_hz} Hz`);

    if (analysis.notable_events.length > 0) {
      summary.push("");
      summary.push(`**Notable Events:** ${analysis.notable_events.length} detected`);
      for (const event of analysis.notable_events.slice(0, 5)) {
        summary.push(
          `- ${event.time_seconds}s: ${event.event_type} (magnitude: ${event.magnitude})`
        );
      }
      if (analysis.notable_events.length > 5) {
        summary.push(`- ... and ${analysis.notable_events.length - 5} more`);
      }
    }

    summary.push("");
    summary.push("**Summary:**");
    summary.push(analysis.text_description);

    return textResponse(summary.join("\n"));
  } catch (error) {
    return errorResponse(`Failed to get audio analysis: ${error}`);
  }
}
