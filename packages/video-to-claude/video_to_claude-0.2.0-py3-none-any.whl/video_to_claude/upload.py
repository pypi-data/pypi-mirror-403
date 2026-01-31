"""Upload processed video content to Cloudflare R2."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
except ImportError:
    boto3 = None
    Config = None


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Strip leading/trailing hyphens
    text = text.strip('-')
    return text


def get_r2_client(
    account_id: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
):
    """
    Create an S3 client configured for Cloudflare R2.

    Credentials can be provided directly or via environment variables:
    - CLOUDFLARE_ACCOUNT_ID
    - CLOUDFLARE_R2_ACCESS_KEY_ID (or AWS_ACCESS_KEY_ID)
    - CLOUDFLARE_R2_SECRET_ACCESS_KEY (or AWS_SECRET_ACCESS_KEY)

    Args:
        account_id: Cloudflare account ID
        access_key_id: R2 access key ID
        secret_access_key: R2 secret access key

    Returns:
        boto3 S3 client configured for R2
    """
    if boto3 is None:
        raise ImportError(
            "boto3 is required for R2 uploads. "
            "Install with: pip install video-to-claude[upload]"
        )

    # Get credentials from environment if not provided
    account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    access_key_id = access_key_id or os.environ.get(
        "CLOUDFLARE_R2_ACCESS_KEY_ID",
        os.environ.get("AWS_ACCESS_KEY_ID")
    )
    secret_access_key = secret_access_key or os.environ.get(
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
        os.environ.get("AWS_SECRET_ACCESS_KEY")
    )

    if not account_id:
        raise ValueError(
            "Cloudflare account ID required. "
            "Set CLOUDFLARE_ACCOUNT_ID environment variable or pass account_id."
        )

    if not access_key_id or not secret_access_key:
        raise ValueError(
            "R2 credentials required. "
            "Set CLOUDFLARE_R2_ACCESS_KEY_ID and CLOUDFLARE_R2_SECRET_ACCESS_KEY "
            "environment variables, or pass access_key_id and secret_access_key."
        )

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"}
        ),
    )


def upload_to_r2(
    output_dir: Path | str,
    name: str,
    bucket: str = "video-to-claude-storage",
    account_id: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
) -> str:
    """
    Upload processed video output to Cloudflare R2.

    Args:
        output_dir: Directory containing the processed video files
        name: Human-readable name for the video
        bucket: R2 bucket name (default: video-to-claude-storage)
        account_id: Cloudflare account ID (or use env var)
        access_key_id: R2 access key ID (or use env var)
        secret_access_key: R2 secret access key (or use env var)

    Returns:
        Video ID (the prefix used in R2)

    Raises:
        ValueError: If manifest.json not found or credentials missing
        RuntimeError: If upload fails
    """
    output_dir = Path(output_dir).resolve()
    manifest_path = output_dir / "manifest.json"

    if not manifest_path.exists():
        raise ValueError(f"No manifest.json found in {output_dir}")

    # Create video ID from slug + short hash
    slug = slugify(name)
    dir_hash = hashlib.md5(str(output_dir).encode()).hexdigest()[:6]
    video_id = f"{slug}-{dir_hash}"

    # Get R2 client
    client = get_r2_client(account_id, access_key_id, secret_access_key)

    # Files to upload
    files_to_upload = [
        "manifest.json",
        "audio_analysis.json",
        "spectrogram.png",
        "waveform.png",
    ]

    # Add all frame files
    for frame in output_dir.glob("frame_*.jpg"):
        files_to_upload.append(frame.name)

    # Upload each file
    uploaded = []
    for filename in files_to_upload:
        file_path = output_dir / filename
        if not file_path.exists():
            continue

        # Determine content type
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = "application/octet-stream"

        r2_key = f"{video_id}/{filename}"

        try:
            with open(file_path, "rb") as f:
                client.put_object(
                    Bucket=bucket,
                    Key=r2_key,
                    Body=f,
                    ContentType=content_type,
                )
            uploaded.append(filename)
        except Exception as e:
            raise RuntimeError(f"Failed to upload {filename}: {e}")

    # Create an index file listing the video
    index_key = f"{video_id}/_index.json"
    index_data = {
        "video_id": video_id,
        "name": name,
        "files": uploaded,
        "manifest": f"{video_id}/manifest.json",
    }

    try:
        client.put_object(
            Bucket=bucket,
            Key=index_key,
            Body=json.dumps(index_data, indent=2),
            ContentType="application/json",
        )
    except Exception as e:
        raise RuntimeError(f"Failed to upload index: {e}")

    return video_id


def list_videos_in_r2(
    bucket: str = "video-to-claude-storage",
    account_id: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
) -> list[dict]:
    """
    List all videos in the R2 bucket.

    Args:
        bucket: R2 bucket name
        account_id: Cloudflare account ID (or use env var)
        access_key_id: R2 access key ID (or use env var)
        secret_access_key: R2 secret access key (or use env var)

    Returns:
        List of video info dictionaries
    """
    client = get_r2_client(account_id, access_key_id, secret_access_key)

    videos = []

    # List all _index.json files
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/_index.json"):
                # Get the index file
                try:
                    response = client.get_object(Bucket=bucket, Key=key)
                    index_data = json.loads(response["Body"].read())
                    videos.append(index_data)
                except Exception:
                    # Skip invalid index files
                    continue

    return videos


def download_from_r2(
    video_id: str,
    output_dir: Path | str,
    bucket: str = "video-to-claude-storage",
    account_id: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
) -> Path:
    """
    Download a video's processed files from R2.

    Args:
        video_id: Video ID (prefix in R2)
        output_dir: Directory to download files to
        bucket: R2 bucket name
        account_id: Cloudflare account ID (or use env var)
        access_key_id: R2 access key ID (or use env var)
        secret_access_key: R2 secret access key (or use env var)

    Returns:
        Path to the output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = get_r2_client(account_id, access_key_id, secret_access_key)

    # List all files for this video
    prefix = f"{video_id}/"
    paginator = client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key[len(prefix):]  # Remove prefix

            if filename.startswith("_"):
                continue  # Skip internal files like _index.json

            # Download the file
            local_path = output_dir / filename
            client.download_file(bucket, key, str(local_path))

    return output_dir
