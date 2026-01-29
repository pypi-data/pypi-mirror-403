"""Command-line interface for themefetch."""

from __future__ import annotations

import logging
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click
from tqdm import tqdm

from .downloader import download_audio
from .filter import filter_theme_candidates, rank_and_select
from .scanner import has_theme_file, scan_library
from .search import (
    format_date,
    format_duration,
    format_views,
    search_with_fallback,
    search_youtube_full,
)


def setup_logging(verbose: bool) -> logging.Logger:
    """Configure logging based on verbose flag."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    return logging.getLogger(__name__)


@click.group()
def main():
    """Emby Theme Downloader - Download TV show theme songs from YouTube."""
    pass


@main.command(name="download")
@click.argument("url")
@click.argument("output_dir", type=click.Path())
@click.option("--quality", default="128", help="Audio bitrate in kbps (default: 128)")
def download_command(url: str, output_dir: str, quality: str) -> None:
    """Download theme song from YouTube URL.

    URL: YouTube video URL

    OUTPUT_DIR: Directory to save theme.mp3
    """
    success = download_audio(url, output_dir, quality)
    sys.exit(0 if success else 1)


@main.command(name="search")
@click.argument("show_name")
@click.argument("year", type=int)
@click.argument("output_dir", type=click.Path())
@click.option("--quality", default="128", help="Audio bitrate in kbps (default: 128)")
@click.option("--verbose", is_flag=True, help="Enable detailed logging")
@click.option("--dry-run", is_flag=True, help="Preview actions without downloading")
def search_command(
    show_name: str,
    year: int,
    output_dir: str,
    quality: str,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Search YouTube for show theme song and download.

    SHOW_NAME: TV show name (e.g., "Breaking Bad")

    YEAR: Release year (e.g., 2008)

    OUTPUT_DIR: Directory to save theme.mp3
    """
    logger = setup_logging(verbose)

    # Search with 3-tier fallback (series theme song → opening theme → intro)
    best = search_with_fallback(show_name, year, max_results=10, verbose=verbose)

    if best is None:
        logger.info("No matching theme found")
        sys.exit(1)

    logger.debug(f"Selected: {best.get('title')}")
    logger.debug(f"  URL: {best.get('webpage_url') or best.get('url')}")
    logger.debug(f"  Views: {best.get('view_count', 0):,}")

    # Dry-run or download
    if dry_run:
        logger.info(f"[DRY RUN] Would download: {best['title']}")
        logger.info(f"[DRY RUN] URL: {best.get('webpage_url') or best.get('url')}")
        logger.info(f"[DRY RUN] Output: {output_dir}/theme.mp3")
        sys.exit(0)

    # Actual download
    logger.info(f"Downloading: {best['title']}")
    url = best.get("webpage_url") or best.get("url")
    if not url:
        logger.error("No URL found in search result")
        sys.exit(1)
    success = download_audio(url, output_dir, quality)
    sys.exit(0 if success else 1)


def display_dry_run_results(
    will_download: list[tuple[dict[str, Any], dict[str, Any]]],
    no_match: list[dict[str, Any]],
    already_exists: list[dict[str, Any]],
    verbose: bool,
    library_dir: str,
) -> None:
    """Display dry-run results in organized sections with metadata.

    Args:
        will_download: List of (show, video) tuples for matched shows
        no_match: List of shows with no theme found
        already_exists: List of shows that already have themes
        verbose: Whether to show "Already Exists" section
        library_dir: Base library directory for relative path calculation
    """
    print()
    print("=" * 70)

    # Section 1: Will Download
    if will_download:
        print(f"Will Download ({len(will_download)})")
        print("=" * 70)

        for show, video in will_download:
            rel_path = os.path.relpath(show["path"], library_dir)
            print(f"\n{show['show_name']} ({show['year']})")
            print(f"  URL: {video.get('webpage_url') or video.get('url')}")
            print(f"  Title: {video.get('title')}")
            print(f"  Duration: {format_duration(video.get('duration'))}")
            print(f"  Views: {format_views(video.get('view_count'))}")
            print(
                f"  Channel: {video.get('channel') or video.get('uploader') or 'N/A'}"
            )
            print(f"  Upload Date: {format_date(video.get('upload_date'))}")
            print(f"  Destination: {rel_path}/theme.mp3")

    # Section 2: No Match
    if no_match:
        print()
        print("=" * 70)
        print(f"No Match ({len(no_match)})")
        print("=" * 70)

        for show in no_match:
            rel_path = os.path.relpath(show["path"], library_dir)
            print(f"  {show['show_name']} ({show['year']})")
            print("    No theme found")

    # Section 3: Already Exists (only with --verbose)
    if already_exists and verbose:
        print()
        print("=" * 70)
        print(f"Already Exists ({len(already_exists)})")
        print("=" * 70)

        for show in already_exists:
            rel_path = os.path.relpath(show["path"], library_dir)
            print(f"  {show['show_name']} ({show['year']})")
            print(f"    Path: {rel_path}")

    # Summary
    print()
    print("=" * 70)
    total = len(will_download) + len(no_match) + len(already_exists)
    print(
        f"Total: {total} shows | Will download: {len(will_download)} | "
        f"No match: {len(no_match)} | Already exists: {len(already_exists)}"
    )
    print("=" * 70)
    print()


def display_download_results(
    results: list[dict[str, Any]],
    library_dir: str,
) -> None:
    """Display download results with detailed metadata matching dry-run format.

    Args:
        results: List of result dicts from process_show() with status/video/show
        library_dir: Base library directory for relative path calculation
    """
    # Group results by status
    success = []
    skipped = []
    failed = []

    for result in results:
        if result["status"] == "success" and "video" in result:
            success.append(result)
        elif result["status"] == "skipped":
            skipped.append(result)
        elif result["status"] == "failed":
            failed.append(result)

    # Sort each section alphabetically by show name
    success.sort(key=lambda x: x["show"]["show_name"])
    skipped.sort(key=lambda x: x["show"]["show_name"])
    failed.sort(key=lambda x: x["show"]["show_name"])

    print()
    print("=" * 70)

    # Section 1: Downloaded (success with metadata)
    if success:
        print(f"Downloaded ({len(success)})")
        print("=" * 70)

        for result in success:
            show = result["show"]
            video = result["video"]
            rel_path = os.path.relpath(show["path"], library_dir)
            print(f"\n{show['show_name']} ({show['year']})")
            print(f"  URL: {video.get('webpage_url') or video.get('url')}")
            print(f"  Title: {video.get('title')}")
            print(f"  Duration: {format_duration(video.get('duration'))}")
            print(f"  Views: {format_views(video.get('view_count'))}")
            print(
                f"  Channel: {video.get('channel') or video.get('uploader') or 'N/A'}"
            )
            print(f"  Upload Date: {format_date(video.get('upload_date'))}")
            print(f"  Destination: {rel_path}/theme.mp3")

    # Section 2: Skipped
    if skipped:
        print()
        print("=" * 70)
        print(f"Skipped ({len(skipped)})")
        print("=" * 70)

        for result in skipped:
            show = result["show"]
            reason = result.get("reason", "Unknown")
            print(f"  {show['show_name']} ({show['year']})")
            print(f"    {reason}")

    # Section 3: Failed
    if failed:
        print()
        print("=" * 70)
        print(f"Failed ({len(failed)})")
        print("=" * 70)

        for result in failed:
            show = result["show"]
            reason = result.get("reason", "Unknown")
            print(f"  {show['show_name']} ({show['year']})")
            print(f"    {reason}")

    # Summary
    print()
    print("=" * 70)
    total = len(success) + len(skipped) + len(failed)
    print(
        f"Total: {total} shows | Downloaded: {len(success)} | "
        f"Skipped: {len(skipped)} | Failed: {len(failed)}"
    )
    print("=" * 70)
    print()


@main.command(name="list")
@click.argument(
    "library_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--verbose", is_flag=True, help="Show folder paths")
def list_command(library_dir: str, verbose: bool) -> None:
    """List shows missing theme.mp3 (fast, no YouTube searches).

    LIBRARY_DIR: Path to TV library root (e.g., /media/TV)
    """
    logger = setup_logging(verbose)

    # Scan library for shows missing themes (replace_all=False for fast scan)
    shows = scan_library(library_dir, replace_all=False)

    if not shows:
        logger.info("All shows have themes")
        sys.exit(0)

    logger.info(f"Shows missing theme.mp3: {len(shows)}")

    # Sort shows alphabetically by show_name
    sorted_shows = sorted(shows, key=lambda x: x["show_name"])

    for show in sorted_shows:
        logger.info(f"  {show['show_name']} ({show['year']})")
        if verbose:
            logger.info(f"    Path: {show['path']}")

    sys.exit(0)


@main.command(name="batch")
@click.argument(
    "library_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--quality", default="128", help="Audio bitrate in kbps (default: 128)")
@click.option("--replace-all", is_flag=True, help="Re-download existing themes")
@click.option("--verbose", is_flag=True, help="Enable detailed logging")
@click.option("--dry-run", is_flag=True, help="Preview actions without downloading")
@click.option("--workers", default=4, help="Number of parallel downloads (default: 4)")
def batch_command(
    library_dir: str,
    quality: str,
    replace_all: bool,
    verbose: bool,
    dry_run: bool,
    workers: int,
) -> None:
    """Batch process TV library directory for theme downloads.

    LIBRARY_DIR: Path to TV library root (e.g., /media/TV)
    """
    logger = setup_logging(verbose)

    # Scan library for ALL shows (including those with existing themes) for dry-run
    logger.info(f"Scanning library: {library_dir}")
    shows = scan_library(library_dir, replace_all=True, silent=dry_run)

    if not shows:
        logger.info("No shows found in library")
        sys.exit(0)

    if not dry_run:
        logger.info(f"Found {len(shows)} shows to process")

    # Enhanced dry-run with full metadata preview
    if dry_run:
        will_download = []
        no_match = []
        already_exists = []

        logger.info("Searching YouTube for theme songs...")

        # Define search function for parallel execution
        def search_show(show: dict) -> dict:
            """Search YouTube for a single show's theme.

            Returns:
                dict with keys: show, status (match/no_match/exists), video (if match)
            """
            show_name = show["show_name"]
            year = show["year"]

            try:
                # Check if theme already exists
                if has_theme_file(Path(show["path"])):
                    return {"show": show, "status": "exists", "video": None}

                # Search YouTube with full metadata
                results = search_youtube_full(show_name, year)

                if not results:
                    return {"show": show, "status": "no_match", "video": None}

                # Filter candidates
                filtered = filter_theme_candidates(
                    results, ["theme", "opening", "intro", "soundtrack", "ost"]
                )

                if not filtered:
                    return {"show": show, "status": "no_match", "video": None}

                # Select best match
                selected = rank_and_select(filtered)

                if selected is None:
                    return {"show": show, "status": "no_match", "video": None}

                # Add delay between searches to avoid rate limits
                time.sleep(random.uniform(2, 5))

                return {"show": show, "status": "match", "video": selected}

            except Exception as e:
                logger.error(f"  Error searching {show_name}: {e}")
                return {"show": show, "status": "no_match", "video": None}

        # Execute searches in parallel if workers > 1, otherwise sequential
        if workers > 1:
            # Parallel execution with progress bar
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(search_show, show) for show in shows]
                for future in tqdm(
                    as_completed(futures), total=len(shows), desc="Searching YouTube"
                ):
                    result = future.result()
                    if result["status"] == "match":
                        will_download.append((result["show"], result["video"]))
                    elif result["status"] == "no_match":
                        no_match.append(result["show"])
                    elif result["status"] == "exists":
                        already_exists.append(result["show"])
        else:
            # Sequential execution (original behavior for workers=1)
            for show in shows:
                logger.info(f"  Searching: {show['show_name']} ({show['year']})")
                result = search_show(show)
                if result["status"] == "match":
                    will_download.append((result["show"], result["video"]))
                elif result["status"] == "no_match":
                    no_match.append(result["show"])
                elif result["status"] == "exists":
                    already_exists.append(result["show"])

        # Sort each category alphabetically by show_name
        will_download.sort(key=lambda x: x[0]["show_name"])
        no_match.sort(key=lambda x: x["show_name"])
        already_exists.sort(key=lambda x: x["show_name"])

        # Display grouped results
        display_dry_run_results(
            will_download, no_match, already_exists, verbose, library_dir
        )

        sys.exit(0)

    # For actual downloads, scan only shows missing themes
    shows = scan_library(library_dir, replace_all)

    # Define process_show function for parallel execution
    def process_show(show: dict) -> dict:
        """Process a single show: search, filter, and download theme.

        Returns:
            dict with keys: show, status (success/failed/skipped), reason, video (if match)
        """
        show_name = show["show_name"]
        year = show["year"]
        show_path = show["path"]

        try:
            # Search with 3-tier fallback (verbose=False for batch operations)
            best = search_with_fallback(show_name, year, max_results=10, verbose=False)

            if best is None:
                return {"show": show, "status": "skipped", "reason": "No theme found"}

            # Dry-run or download
            if dry_run:
                logger.info(f"  [DRY RUN] Would download: {best['title']}")
                result = {
                    "show": show,
                    "status": "success",
                    "reason": f"Dry-run: {best['title']}",
                }
            else:
                logger.info(f"  Downloading: {best['title']}")
                url = best.get("webpage_url") or best.get("url")
                if not url:
                    return {
                        "show": show,
                        "status": "failed",
                        "reason": "No URL in search result",
                    }
                success = download_audio(url, show_path, quality)

                if success:
                    result = {
                        "show": show,
                        "status": "success",
                        "reason": f"Downloaded: {best['title']}",
                        "video": best,
                    }
                else:
                    result = {
                        "show": show,
                        "status": "failed",
                        "reason": "Download failed after 3 retries",
                    }

            # Add random delay between 2-5 seconds to avoid rate limits
            delay = random.uniform(2, 5)
            time.sleep(delay)

            return result

        except Exception as e:
            error_message = str(e)

            # Check for rate limiting (HTTP 429)
            if "429" in error_message or "Too Many Requests" in error_message:
                logger.warning(f"  Rate limited for {show_name}, backing off...")
                time.sleep(60)
                return {
                    "show": show,
                    "status": "failed",
                    "reason": "Rate limited (HTTP 429)",
                }

            logger.error(f"  ✗ Error processing {show_name}: {e}")
            return {"show": show, "status": "failed", "reason": str(e)}

    # Execute shows in parallel using ThreadPoolExecutor with progress bar
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_show, show) for show in shows]
        for future in tqdm(
            as_completed(futures), total=len(shows), desc="Processing shows"
        ):
            results.append(future.result())

    # Display detailed results with metadata
    display_download_results(results, library_dir)


if __name__ == "__main__":
    main()
