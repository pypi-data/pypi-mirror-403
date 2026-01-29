# themefetch

Automatically download TV show theme songs from YouTube and save them as `theme.mp3` files for Emby/Jellyfin media servers.

## Requirements

- Python 3.10 or higher
- ffmpeg (system package, required for audio conversion)

### Installing ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Installation

### Quick Start (Recommended)

Run themefetch without installation using `uvx`:

```bash
uvx themefetch batch /path/to/tv/library
```

### Install as Tool

Install themefetch as a persistent command:

```bash
uv tool install themefetch
themefetch batch /path/to/tv/library
```

### Traditional pip install

```bash
pip install themefetch
themefetch batch /path/to/tv/library
```

## Commands

themefetch provides four commands for different workflows:

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `batch` | Process entire library | Most common - download themes for all shows |
| `list` | Fast scan without searches | Preview which shows need themes |
| `search` | Search and download one show | Download theme for specific show by name |
| `download` | Download from YouTube URL | Use a specific YouTube video as theme |

## Usage

### Batch Processing (Most Common)

Scan your entire TV library and download theme songs for all shows:

```bash
# Process entire library
themefetch batch /path/to/tv/library

# Dry run (preview what would be downloaded)
themefetch batch --dry-run /path/to/tv/library

# Parallel downloads with 6 workers (default: 4)
themefetch batch --workers 6 /path/to/tv/library

# Show verbose logging
themefetch batch --verbose /path/to/tv/library
```

### List Shows Needing Themes

See which shows don't have theme songs yet (fast, no YouTube searches):

```bash
themefetch list /path/to/tv/library
```

### Search for Single Show

Search YouTube and download theme for a specific show by name:

```bash
themefetch search "Breaking Bad" 2008 "/path/to/tv/library/Breaking Bad (2008)"

# Dry run to preview before downloading
themefetch search "The Wire" 2002 "/path/to/tv/library/The Wire (2002)" --dry-run
```

### Download from Specific URL

Download theme from a specific YouTube URL:

```bash
themefetch download "https://www.youtube.com/watch?v=VIDEO_ID" "/path/to/tv/library/Show Name (Year)"
```

## Features

- **Intelligent 3-tier search**: Progressive query fallback (series theme → opening theme → intro)
- **Smart filtering**: Blocks trailers, covers, reactions using keyword patterns
- **Accuracy over completeness**: Skips shows rather than downloading incorrect themes
- **Batch processing**: Scan and process entire TV libraries automatically
- **Parallel downloads**: Configurable workers for faster processing (default: 4)
- **Dry-run mode**: Preview actions with full metadata before downloading
- **Skip existing**: Automatically skips shows that already have `theme.mp3`
- **Cross-platform**: Works on Windows, macOS, and Linux

## Library Format

Your TV shows must be organized in "Name (Year)" folder format:

```
/path/to/tv/library/
├── Breaking Bad (2008)/
├── The Wire (2002)/
├── Friends (1994)/
└── ...
```

Theme songs are saved as `theme.mp3` in each show folder.

## How It Works

themefetch uses a multi-stage filtering pipeline to ensure accurate theme downloads:

### 1. Library Scanning
- Scans library for shows in "Name (Year)" folder format
- Skips shows with existing `theme.mp3` (unless `--replace-all` flag used)

### 2. Intelligent Search with 3-Tier Fallback
Progressively broader queries until a match is found:
1. **"{show} series theme song"** - TV-specific, avoids movies
2. **"{show} opening theme"** - Broader match
3. **"{show} intro"** - Broadest match

### 3. Smart Filtering
Results are filtered through multiple criteria:

**Duration filtering:**
- Must be 20-180 seconds (typical theme song length)
- Filters out full episodes and short clips

**View count threshold:**
- Minimum 5,000 views to filter spam/low-quality uploads

**Keyword matching:**
- Must contain: theme, opening, intro, soundtrack, or ost
- Uses fuzzy matching (70% threshold) to handle typos

**Negative keyword filtering (word boundaries):**
- **Blocks trailers:** trailer, teaser, preview, promo
- **Blocks covers/remixes:** cover, remix, acoustic, piano version, orchestral
- **Blocks reactions/analysis:** reaction, reacting, breakdown, analysis, review

### 4. Ranking and Selection
- **Primary:** View count (higher is better)
- **Bonus:** Official channels (+1M views equivalent for official/vevo/records/music)
- **Tiebreaker:** Newer upload date

### 5. Download and Conversion
- Downloads best audio quality available
- Converts to MP3 using ffmpeg (default: 128kbps)
- Saves as `theme.mp3` in show folder
- Retries: 3 attempts with exponential backoff (2s, 4s, 8s)

## Advanced Options

**Global flags (all commands):**
- `--verbose` - Show detailed logging and filter statistics
- `--quality N` - Audio bitrate in kbps (default: 128)

**Batch-specific flags:**
- `--workers N` - Number of parallel downloads (default: 4)
- `--dry-run` - Preview actions with full metadata before downloading
- `--replace-all` - Re-download existing themes

**Search-specific flags:**
- `--dry-run` - Preview selected video before downloading

## Development

themefetch uses modern Python tooling for code quality:

### Code Quality Tools

**Linting and formatting with ruff:**
```bash
# Check code style and lint issues
uv run ruff check .

# Auto-fix issues where possible
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Type checking with mypy:**
```bash
# Run type checking from project root
uv run mypy .

# Or check the src directory
uv run mypy src/
```

**Run all checks:**
```bash
# Lint, format, and type check in one command
uv run ruff check . && uv run ruff format . && uv run mypy .
```

### Installing Development Dependencies

Development tools are installed automatically with uv, but you can install them explicitly:

```bash
uv pip install -e ".[dev]"
```

## Troubleshooting

### "No matching theme found"

The filters may be too strict for some shows. This happens when:
- All results are filtered out (trailers, covers, wrong duration)
- Show has low YouTube presence (< 5,000 views)
- Theme song isn't available on YouTube

**Solution:** This is working as intended - accuracy over completeness. You can manually download using the `download` command with a specific URL.

### Wrong theme downloaded

themefetch prioritizes accuracy, but mismatches can occur for:
- Shows with similar names (word boundary matching helps but isn't perfect)
- Shows where "official" uploads are lower quality than fan uploads

**Solution:** Delete the incorrect `theme.mp3` and use `themefetch download <URL> <path>` with a specific YouTube URL.

### Rate limiting / HTTP 429 errors

themefetch includes built-in rate limiting protection:
- Random 2-5 second delays between searches
- 60 second backoff on HTTP 429 errors

**Solution:** If you still hit rate limits, reduce `--workers` to 1 or 2 for slower sequential processing.

### "ffmpeg not found" errors

ffmpeg must be installed separately (see Requirements section above).

**Solution:** Install ffmpeg using your system package manager.

## Technical Details

**YouTube integration:**
- Uses yt-dlp for YouTube searches (no API key required)
- No quota limits - yt-dlp uses built-in search

**Performance:**
- Parallel processing with ThreadPoolExecutor (default 4 workers)
- Dry-run mode uses parallel search for fast previews

**Reliability:**
- 3 retry attempts with exponential backoff (2s, 4s, 8s)
- Random delays (2-5s) between operations to avoid rate limits
- 60s backoff on HTTP 429 (Too Many Requests)

**Filtering accuracy:**
- Fuzzy keyword matching with RapidFuzz (70% threshold for typos)
- Word boundary matching for show names (avoids "Trust" matching "In Family We Trust")
- Negative patterns use regex word boundaries to avoid false positives

**Cross-platform:**
- `windowsfilenames=True` in yt-dlp for safe filenames on all platforms
- Path handling uses Python's pathlib for OS-independent paths
