# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Downloader is a macOS desktop application built with Flet (Python's Flutter wrapper) and yt-dlp for downloading content from YouTube and Instagram. The app supports YouTube videos/playlists and Instagram posts/reels/stories with a dark-themed, modern UI.

## Core Architecture

### Application Entry Points
- **`run.py`**: Simple launcher that calls `launcher.py`
- **`launcher.py`**: Main entry point with dependency checking GUI and platform/mode selection menu
  - Checks for Python, Flet, yt-dlp, and FFmpeg dependencies
  - Shows platform selection: Instagram (featured) + YouTube (3 modes)
  - Adds common macOS paths to PATH for GUI app environment (`/opt/homebrew/bin`, `/usr/local/bin`, etc.)

### Downloader Modes
Each mode is a separate class that takes a `page` (Flet Page) and optional `on_back` callback:

**Instagram Mode:**
1. **`instagram_downloader.py`** (`InstagramDownloader`):
   - Analyzes Instagram posts, reels, and stories
   - Shows media preview with thumbnail
   - Four download options: Video, Audio Only, Photo/Image, or Thumbnail
   - Auto-detects media type from URL
   - Photo option: Downloads actual photo for image posts, or thumbnail for video posts
   - Thumbnail option: Always downloads the preview thumbnail image
   - Downloads to `~/Downloads/Instagram` by default
   - Uses `page.run_task()` for async UI updates from threads

**YouTube Modes:**
1. **`youtube_downloader_mvp.py`** (`YouTubeDownloaderMVP`): Simple mode
   - One-click downloads with preset best quality
   - Video (MP4) or Audio (MP3) toggle
   - Minimal configuration

2. **`youtube_downloader_advanced.py`** (`YouTubeDownloaderAdvanced`): Advanced mode
   - Fetches available formats via `yt-dlp`
   - Allows resolution selection (up to 4K)
   - Subtitle download support (multiple languages)
   - Format preview before download

3. **`youtube_playlist_downloader.py`** (`PlaylistDownloader`): Playlist mode
   - Fetches all videos from playlist
   - Select individual videos or download all
   - Parallel downloads (max 2 concurrent by default via `ThreadPoolExecutor`)
   - Uses `VideoItem` class to track each video's state
   - Thread-safe UI updates with `ui_lock`

### Shared Components
- **`ui_components.py`**: Contains `ProgressControl` class
  - Reusable progress bar component with stats (speed, ETA, size)
  - States: start_download, update_progress, complete, error, cancelled, reset
  - Includes "Show in Finder" button and cancel functionality

## Technology Stack

- **UI Framework**: Flet (Flutter for Python) with dark theme
- **Download Engine**: yt-dlp (fork of youtube-dl)
- **Media Processing**: FFmpeg (required for MP4/MP3 conversion and merging)
- **Fonts**: Inter (loaded via Google Fonts CDN)
- **Platform**: macOS-focused (uses Finder integration, Homebrew paths)

## Development Commands

### Running the Application
```bash
python3 run.py
```
This launches the GUI setup window which handles dependency checks.

### Installing Dependencies
```bash
# Python packages
pip install -r requirements.txt

# FFmpeg (macOS)
brew install ffmpeg
```

### Setup Script (manual dependency installation)
```bash
python3 setup.py
```
This script:
- Checks Python version (requires 3.7+)
- Installs Python packages (flet, yt-dlp, ffmpeg-python)
- Detects and installs FFmpeg via Homebrew (macOS)

### Building for Distribution
```bash
./publish.sh
```
This script:
1. Cleans previous builds
2. Installs/updates dependencies with `--break-system-packages` flag
3. Uses `flet pack` to create macOS `.app` bundle
4. Uses `pkgbuild` to create `.pkg` installer for `/Applications`
5. Outputs to `dist/` directory

## Key Technical Details

### yt-dlp Integration
- Uses `yt_dlp.YoutubeDL` context manager for all downloads
- Works with both YouTube and Instagram URLs automatically
- Common options across modes:
  - `format`: Format selection string (e.g., `bestvideo+bestaudio/best`, `best[ext=mp4]/best`)
  - `outtmpl`: Output path template
  - `merge_output_format`: Target format (mp4/mp3)
  - `postprocessors`: FFmpeg-based audio extraction for MP3
  - `progress_hooks`: Callback for download progress updates
- Instagram-specific: Extracts thumbnail, title, and available formats (video/audio/photo)

### Threading Model
- All downloads run in background threads to prevent UI blocking
- Playlist mode uses `concurrent.futures.ThreadPoolExecutor` for parallel downloads
- UI updates from threads must call `self.page.update()` or component's `.update()`
- Playlist mode uses `Lock()` for thread-safe UI operations

### File Picker
- Flet's `FilePicker` component used for folder selection
- Must be added to `page.overlay` before use
- Default download locations:
  - YouTube modes: `~/Downloads`
  - Instagram mode: `~/Downloads/Instagram` (auto-created)

### Path Handling
- Uses `pathlib.Path` for cross-platform compatibility
- Subprocess for opening Finder: `subprocess.run(["open", "-R", file_path])`

### Window Configuration
- All modes set fixed window dimensions (700-900px width, 600-800px height)
- Dark theme: `ft.ThemeMode.DARK`, bgcolor `#1a1a1a`
- Gradients and rounded corners used throughout UI

## Common Issues

### FFmpeg Not Found
The app requires FFmpeg in PATH. If not found:
- Launcher shows manual installation instructions
- Videos may download but fail to merge/convert without FFmpeg
- On macOS, install via `brew install ffmpeg`

### Frozen App Detection
`launcher.py` uses `getattr(sys, 'frozen', False)` to detect if running as packaged app vs source code.

### Language Notes
Error messages and UI text contain Uzbek language strings (e.g., "Dastur to'xtatildi", "O'rnatish muvaffaqiyatsiz tugadi"). This is intentional for the target audience.
