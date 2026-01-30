"""Keyword filtering and ranking logic for theme song candidates."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

# Negative keyword patterns with word boundaries to avoid false positives
NEGATIVE_PATTERNS = {
    "trailer": [
        r"\btrailer\b",
        r"\bteaser\b",
        r"\bpreview\b",
        r"\bpromo\b",
    ],
    "cover": [
        r"\bcover\b",
        r"\bremix\b",
        r"\bacoustic\b",
        r"\bpiano\s+version\b",
        r"\borchestral\b",
    ],
    "reaction": [
        r"\breaction\b",
        r"\breacting\b",
        r"\bbreakdown\b",
        r"\banalysis\b",
        r"\breview\b",
    ],
}


def check_negative_filters(title: str) -> tuple[bool, str]:
    """Check if title matches negative patterns.

    Returns:
        (is_filtered, category_name): is_filtered is True if title should be blocked

    Examples:
        >>> check_negative_filters('Breaking Bad Theme Song')
        (False, '')
        >>> check_negative_filters('Breaking Bad Official Trailer')
        (True, 'trailer')
        >>> check_negative_filters('Theme Song Cover')
        (True, 'cover')
    """
    title_lower = title.lower()

    for category, patterns in NEGATIVE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return True, category

    return False, ""


def matches_show_name(video_title: str, show_name: str) -> bool:
    """Check if video title contains show name as whole words using word boundaries.

    Args:
        video_title: Video title to check
        show_name: Show name to match

    Returns:
        True if show name matches as whole words

    Examples:
        >>> matches_show_name('Trust Theme Song', 'Trust')
        True
        >>> matches_show_name('In Family We Trust Theme', 'Trust')
        False
    """
    # Escape special regex characters in show name (e.g., M*A*S*H, The 100)
    escaped = re.escape(show_name)
    # Build pattern with word boundaries
    pattern = r"\b" + escaped + r"\b"
    return bool(re.search(pattern, video_title, re.IGNORECASE))


def filter_theme_candidates(
    results: list[dict[str, Any]],
    keywords: list[str] | None = None,
    min_fuzzy_score: int = 70,
    duration_range: tuple[int, int] = (20, 180),
    min_view_count: int = 5000,
) -> list[dict[str, Any]]:
    """Filter search results to find likely theme songs.

    Uses two-pass keyword matching:
    1. Fast path: Exact substring match (case-insensitive)
    2. Slow path: Fuzzy match using RapidFuzz (handles typos)

    Args:
        results: Raw search results from yt-dlp
        keywords: Theme-related keywords (default: ['theme', 'opening', 'intro', 'soundtrack', 'ost'])
        min_fuzzy_score: Minimum fuzzy match score 0-100 (default: 70)
        duration_range: (min_seconds, max_seconds) for theme length (default: 20-180)
        min_view_count: Minimum view count to filter spam (default: 5000)

    Returns:
        Filtered list of candidate videos

    Example:
        >>> results = [{'title': 'Breaking Bad Theme', 'duration': 45, 'view_count': 10000, ...}]
        >>> filtered = filter_theme_candidates(results)
        >>> len(filtered) >= 1
        True
    """
    if keywords is None:
        keywords = ["theme", "opening", "intro", "soundtrack", "ost"]

    candidates = []
    min_dur, max_dur = duration_range

    for result in results:
        title = result.get("title", "")
        duration = result.get("duration")

        # Filter by duration first (skip if None or outside range)
        if duration is None:
            # Skip videos with no duration metadata
            continue
        if not (min_dur <= duration <= max_dur):
            continue

        # Filter by view count (skip low-quality/spam uploads)
        view_count = result.get("view_count", 0) or 0
        if view_count < min_view_count:
            continue

        # Filter by keywords (exact or fuzzy match)
        if not _matches_any_keyword(title, keywords, min_fuzzy_score):
            continue

        # Filter by negative keywords (skip trailers, covers, reactions)
        is_filtered, category = check_negative_filters(title)
        if is_filtered:
            continue

        candidates.append(result)

    return candidates


def _matches_any_keyword(text: str, keywords: list[str], min_score: int) -> bool:
    """Check if text matches any keyword (exact or fuzzy).

    Args:
        text: Text to search (e.g., video title)
        keywords: Keywords to match
        min_score: Minimum fuzzy match score 0-100

    Returns:
        True if any keyword matches
    """
    text_lower = text.lower()

    # Fast path: exact substring match
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True

    # Slow path: fuzzy match for typos
    for keyword in keywords:
        # partial_ratio handles substring matching well
        score = fuzz.partial_ratio(keyword.lower(), text_lower)
        if score >= min_score:
            return True

    return False


def rank_and_select(
    candidates: list[dict[str, Any]], prefer_official: bool = True
) -> dict[str, Any] | None:
    """Rank filtered candidates and select the best match.

    Ranking criteria:
    1. Primary: view_count (higher is better)
    2. Bonus: Official channel markers (+1M views equivalent)
    3. Secondary: Newer upload_date for tiebreaking

    Args:
        candidates: Filtered search results
        prefer_official: Prioritize official/verified channels (default: True)

    Returns:
        Best candidate or None if no candidates

    Example:
        >>> candidates = [
        ...     {'title': 'Theme', 'view_count': 5000000, 'channel': 'Official'},
        ...     {'title': 'Cover', 'view_count': 100000, 'channel': 'RandomUser'}
        ... ]
        >>> best = rank_and_select(candidates)
        >>> best['view_count']
        5000000
    """
    if not candidates:
        return None

    def score_candidate(candidate: dict) -> tuple:
        """Return sortable score tuple (higher is better)."""
        view_count = candidate.get("view_count", 0) or 0  # Handle None
        upload_date = candidate.get("upload_date", "00000000")  # YYYYMMDD format
        channel = (candidate.get("channel") or "").lower()

        # Bonus for official-looking channels
        official_score = 0
        if prefer_official:
            official_markers = ["official", "vevo", "records", "music"]
            if any(marker in channel for marker in official_markers):
                official_score = 1000000  # Equivalent to 1M views

        # Primary: view count + official bonus
        # Secondary: newer upload date (YYYYMMDD string sorts correctly)
        return (view_count + official_score, upload_date)

    # Sort by score and return top result
    ranked = sorted(candidates, key=score_candidate, reverse=True)
    return ranked[0]
