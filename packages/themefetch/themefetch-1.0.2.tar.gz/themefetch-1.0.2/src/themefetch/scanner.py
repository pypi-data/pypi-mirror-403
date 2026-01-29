"""Directory scanning and show folder detection for TV libraries."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_show_folder(folder_name: str) -> tuple[str, int] | None:
    """Parse TV show folder name in "Name (Year)" format.

    Args:
        folder_name: Folder name to parse (e.g., "Breaking Bad (2008)")

    Returns:
        Tuple of (show_name, year) if format matches, None otherwise

    Examples:
        >>> parse_show_folder("Breaking Bad (2008)")
        ('Breaking Bad', 2008)
        >>> parse_show_folder("Friends (1994)")
        ('Friends', 1994)
        >>> parse_show_folder("InvalidFolder")
        None
    """
    # Pattern: Name (Year) where Year is 4 digits
    pattern = r"^(.+?)\s+\((\d{4})\)$"
    match = re.match(pattern, folder_name)

    if match:
        show_name = match.group(1).strip()
        year = int(match.group(2))
        return (show_name, year)

    return None


def has_theme_file(folder_path: Path) -> bool:
    """Check if theme.mp3 exists in the given folder.

    Args:
        folder_path: Path to show folder

    Returns:
        True if theme.mp3 exists and is a file, False otherwise

    Examples:
        >>> from pathlib import Path
        >>> has_theme_file(Path("/tmp/test_show"))
        False
    """
    theme_file = folder_path / "theme.mp3"
    return theme_file.exists() and theme_file.is_file()


def scan_library(
    library_dir: str, replace_all: bool = False, silent: bool = False
) -> list[dict]:
    """Scan TV library directory for shows needing theme downloads.

    Iterates over immediate subdirectories (not recursive), parses folder names
    in "Name (Year)" format, and checks for existing theme.mp3 files.

    Args:
        library_dir: Path to TV library root directory
        replace_all: If True, include shows with existing themes (default: False)
        silent: If True, suppress "Replacing existing theme" and "Skipping" log messages (default: False)

    Returns:
        List of show dictionaries with keys:
        - show_name: TV show name (str)
        - year: Release year (int)
        - path: Full path to show folder (str)

    Examples:
        >>> scan_library("/media/TV", replace_all=False)
        [{'show_name': 'Breaking Bad', 'year': 2008, 'path': '/media/TV/Breaking Bad (2008)'}]
    """
    library_path = Path(library_dir)

    if not library_path.exists():
        logger.error(f"Library directory does not exist: {library_dir}")
        return []

    if not library_path.is_dir():
        logger.error(f"Library path is not a directory: {library_dir}")
        return []

    shows_to_process = []

    # Iterate over immediate subdirectories only (not recursive)
    for item in library_path.iterdir():
        if not item.is_dir():
            continue

        folder_name = item.name

        # Parse folder name
        parsed = parse_show_folder(folder_name)
        if parsed is None:
            logger.debug(f"Skipping invalid format: {folder_name}")
            continue

        show_name, year = parsed

        # Check for existing theme.mp3
        if has_theme_file(item):
            if replace_all:
                if not silent:
                    logger.info(f"Replacing existing theme: {folder_name}")
            else:
                if not silent:
                    logger.info(f"Skipping (theme exists): {folder_name}")
                continue

        # Add to processing list
        shows_to_process.append(
            {"show_name": show_name, "year": year, "path": str(item)}
        )

    if not silent:
        logger.info(f"Found {len(shows_to_process)} shows to process")
    return shows_to_process
