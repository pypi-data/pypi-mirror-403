"""Core download logic for YouTube audio extraction."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import yt_dlp


def download_audio(url: str, output_dir: str, quality: str = "128") -> bool:
    """Download audio from YouTube URL and save as MP3 with retry logic.

    Args:
        url: YouTube video URL
        output_dir: Directory to save theme.mp3
        quality: Audio bitrate in kbps (default: 128)

    Returns:
        True if download succeeded, False otherwise
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        "outtmpl": str(output_path / "theme.%(ext)s"),
        "windowsfilenames": True,  # Cross-platform filename safety
        "quiet": True,
        "no_warnings": True,
    }

    # Retry loop with exponential backoff (3 attempts total)
    for attempt in range(1, 4):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if attempt > 1:
                    print(f"Retry {attempt}/3...")
                else:
                    print(f"Downloading from: {url}")

                ydl.download([url])
                print(f"✓ Downloaded to: {output_path / 'theme.mp3'}")
                return True

        except yt_dlp.utils.DownloadError as e:
            if attempt < 3:
                # Exponential backoff: 2s, 4s, 8s
                delay = 2**attempt
                print(f"✗ Download failed (attempt {attempt}/3): {e}", file=sys.stderr)
                print(f"Retrying after {delay}s...", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"✗ Download failed after 3 retries: {e}", file=sys.stderr)
                # Clean up partial files
                _cleanup_partial_files(output_path)
                return False

        except Exception as e:
            if attempt < 3:
                delay = 2**attempt
                print(f"✗ Unexpected error (attempt {attempt}/3): {e}", file=sys.stderr)
                print(f"Retrying after {delay}s...", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"✗ Unexpected error after 3 retries: {e}", file=sys.stderr)
                _cleanup_partial_files(output_path)
                return False

    return False


def _cleanup_partial_files(directory: Path) -> None:
    """Remove .part files from failed downloads."""
    for part_file in directory.glob("*.part"):
        try:
            part_file.unlink()
            print(f"Cleaned up partial file: {part_file.name}")
        except Exception as e:
            print(f"Warning: Could not remove {part_file.name}: {e}", file=sys.stderr)
