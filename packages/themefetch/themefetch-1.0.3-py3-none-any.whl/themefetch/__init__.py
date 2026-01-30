"""themefetch - Download TV show theme songs from YouTube.

This package provides automated theme song downloading for TV shows from YouTube,
with intelligent search filtering and batch processing capabilities.
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = ["download_audio"]

from .downloader import download_audio
