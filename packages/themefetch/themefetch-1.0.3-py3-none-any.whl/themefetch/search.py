"""YouTube search functionality using yt-dlp."""

from __future__ import annotations

from typing import Any, cast

import yt_dlp

from .filter import filter_theme_candidates, rank_and_select


def search_youtube(
    show_name: str,
    year: int,  # noqa: ARG001 - kept for API compatibility
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search YouTube for TV show theme songs using yt-dlp's built-in search.

    Uses yt-dlp's ytsearch: prefix to search YouTube without separate API.
    Returns metadata-only results (no downloads) for fast searching.

    Args:
        show_name: TV show name (e.g., "Breaking Bad")
        year: Release year (kept for API compatibility but not used in query)
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of video metadata dictionaries with fields:
        - title: Video title (str)
        - view_count: View count (int or None)
        - upload_date: Upload date as YYYYMMDD (str or None)
        - duration: Duration in seconds (int or None)
        - channel: Channel name (str or None)
        - id: Video ID (str)
        - url: Full YouTube URL (str)

    Example:
        >>> results = search_youtube("Breaking Bad", 2008)
        >>> print(results[0]['title'])
        'Breaking Bad - Main Theme Song'
    """
    # Build query string: "ShowName series theme song" (year dropped per Phase 6 decision)
    query_string = f"{show_name} series theme song"

    # Configure yt-dlp for fast search (metadata only)
    ydl_opts = {
        "extract_flat": True,  # Critical: fast search, no full video info
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearchN: prefix returns top N results
            search_query = f"ytsearch{max_results}:{query_string}"
            result = ydl.extract_info(search_query, download=False)

            # Return entries list (metadata dictionaries)
            return cast(list[dict[str, Any]], result.get("entries", []))

    except Exception as e:
        # Return empty list on search failure
        print(f"Search failed: {e}")
        return []


def search_youtube_full(
    show_name: str,
    year: int,  # noqa: ARG001 - kept for API compatibility
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search YouTube for TV show theme songs with full metadata extraction.

    Unlike search_youtube(), this variant extracts full metadata (views, channel,
    upload_date, duration) by setting extract_flat=False. This is slower but
    provides complete information needed for dry-run preview with metadata.

    Args:
        show_name: TV show name (e.g., "Breaking Bad")
        year: Release year (kept for API compatibility but not used in query)
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of video metadata dictionaries with full fields:
        - title: Video title (str)
        - view_count: View count (int or None)
        - upload_date: Upload date as YYYYMMDD (str or None)
        - duration: Duration in seconds (int or None)
        - channel: Channel name (str or None)
        - uploader: Uploader name if channel not available (str or None)
        - id: Video ID (str)
        - url: Full YouTube URL (str)
        - webpage_url: Full YouTube URL (str)

    Example:
        >>> results = search_youtube_full("Breaking Bad", 2008)
        >>> print(f"{results[0]['title']} - {results[0]['view_count']} views")
        'Breaking Bad - Main Theme Song - 5000000 views'
    """
    # Build query string: "ShowName series theme song" (year dropped per Phase 6 decision)
    query_string = f"{show_name} series theme song"

    # Configure yt-dlp for full metadata extraction (slower but complete)
    ydl_opts = {
        "skip_download": True,  # Don't download video files, just metadata
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearchN: prefix returns top N results
            search_query = f"ytsearch{max_results}:{query_string}"
            result = ydl.extract_info(search_query, download=False)

            # Return entries list (metadata dictionaries with full fields)
            return cast(list[dict[str, Any]], result.get("entries", []))

    except Exception as e:
        # Return empty list on search failure
        print(f"Search failed: {e}")
        return []


def format_duration(seconds: int | None) -> str:
    """Format duration from seconds to M:SS or H:MM:SS format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1:30" or "1:05:30")

    Examples:
        >>> format_duration(90)
        '1:30'
        >>> format_duration(3930)
        '1:05:30'
        >>> format_duration(None)
        'N/A'
    """
    if seconds is None:
        return "N/A"

    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}:{secs:02d}"

    hours, mins = divmod(minutes, 60)
    return f"{hours}:{mins:02d}:{secs:02d}"


def format_views(count: int | None) -> str:
    """Format view count with thousands separators.

    Args:
        count: View count as integer

    Returns:
        Formatted view count string (e.g., "2,100,000")

    Examples:
        >>> format_views(2100000)
        '2,100,000'
        >>> format_views(None)
        'N/A'
    """
    if count is None:
        return "N/A"
    return f"{count:,}"


def format_date(date_str: str | None) -> str:
    """Format upload date from YYYYMMDD to YYYY-MM-DD.

    Args:
        date_str: Upload date in YYYYMMDD format

    Returns:
        Formatted date string (e.g., "2023-05-15")

    Examples:
        >>> format_date("20230515")
        '2023-05-15'
        >>> format_date(None)
        'N/A'
        >>> format_date("invalid")
        'N/A'
    """
    if not date_str or len(date_str) != 8:
        return "N/A"
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def search_with_fallback(
    show_name: str, year: int, max_results: int = 10, verbose: bool = False
) -> dict[str, Any] | None:
    """Search with progressive query fallback and filtering.

    Query variations (in order):
    1. "{show_name} series theme song" - TV disambiguation without year
    2. "{show_name} opening theme" - Broader match
    3. "{show_name} intro" - Broadest match

    Returns best match or None if all queries filtered out.

    Args:
        show_name: TV show name (e.g., "Breaking Bad")
        year: Release year (kept for API compatibility but not used in query)
        max_results: Maximum results per query (default: 10)
        verbose: Enable verbose logging of filter statistics

    Returns:
        Best matching video or None

    Example:
        >>> result = search_with_fallback("Breaking Bad", 2008, verbose=True)
        >>> result is not None
        True
    """
    # Query variations from specific to broad (year dropped per user decision)
    queries = [
        f"{show_name} series theme song",
        f"{show_name} opening theme",
        f"{show_name} intro",
    ]

    for i, query in enumerate(queries, 1):
        # Search with full metadata extraction
        results = search_youtube_full(show_name, year, max_results)

        # Override query string in the search (year removed)
        if verbose:
            print(f"Query {i}: {query}")

        # Apply filtering
        filtered = filter_theme_candidates(results)

        if filtered:
            # Found valid results, rank and return best
            best = rank_and_select(filtered)
            if best and verbose:
                print(
                    f"Query {i} found {len(filtered)} candidates, selected: {best.get('title', 'N/A')}"
                )
            return best

        # Log why all results were filtered (verbose mode)
        if verbose and results:
            # Count filter reasons
            trailer_count = sum(
                1 for r in results if "trailer" in r.get("title", "").lower()
            )
            cover_count = sum(
                1 for r in results if "cover" in r.get("title", "").lower()
            )
            reaction_count = sum(
                1 for r in results if "reaction" in r.get("title", "").lower()
            )
            low_views = sum(1 for r in results if (r.get("view_count", 0) or 0) < 5000)

            reasons = []
            if trailer_count:
                reasons.append(f"{trailer_count} trailers")
            if cover_count:
                reasons.append(f"{cover_count} covers")
            if reaction_count:
                reasons.append(f"{reaction_count} reactions")
            if low_views:
                reasons.append(f"{low_views} low_views")

            if reasons:
                print(f"Query {i} filtered all results: {', '.join(reasons)}")
            else:
                print(f"Query {i} returned no results")

    return None  # All queries exhausted
