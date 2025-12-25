"""
Shared utilities for Flet YouTube/Instagram downloader
Centralizes common code to eliminate duplication across all downloader modes
"""

import sys
import re
import time
import subprocess
from pathlib import Path


# ============================================================================
# CONSTANTS
# ============================================================================

COLORS = {
    'youtube_simple': '#FFD700',  # Yellow
    'youtube_advanced': '#FF0000',  # Red
    'youtube_playlist': '#3498db',  # Blue
    'instagram': '#E4405F',  # Instagram pink
    'primary_bg': '#1a1a1a',
    'secondary_bg': '#2d2d2d',
    'border': '#333333',
    'text_primary': 'white',
    'text_secondary': '#888888',
}

DEFAULT_DOWNLOAD_PATHS = {
    'youtube': str(Path.home() / "Downloads"),
    'instagram': str(Path.home() / "Downloads" / "Instagram"),
}


# ============================================================================
# RESPONSIVE DIMENSIONS
# ============================================================================

def get_responsive_dimensions(page, width_factor=0.65, height_factor=0.80,
                              min_width=700, max_width=950,
                              min_height=750, max_height=1050):
    """
    Calculate responsive window dimensions based on screen size.
    Single source of truth for all downloader window sizing.

    Args:
        page: Flet Page object
        width_factor: Fraction of screen width to use (default 65%)
        height_factor: Fraction of screen height to use (default 80%)
        min_width: Minimum window width
        max_width: Maximum window width
        min_height: Minimum window height
        max_height: Maximum window height

    Returns:
        Tuple: (window_width, window_height)
    """
    try:
        screen_width = 1440
        screen_height = 900
        window_width = max(min_width, min(max_width, int(screen_width * width_factor)))
        window_height = max(min_height, min(max_height, int(screen_height * height_factor)))
        return window_width, window_height
    except Exception:
        return max_width, max_height


# ============================================================================
# PLATFORM DETECTION
# ============================================================================

def is_macos():
    """Check if running on macOS"""
    return sys.platform == "darwin"


def is_windows():
    """Check if running on Windows"""
    return sys.platform == "win32"


def is_linux():
    """Check if running on Linux"""
    return sys.platform.startswith("linux")


# ============================================================================
# URL VALIDATION
# ============================================================================

def validate_youtube_url(url):
    """
    Validate if URL is a valid YouTube URL.

    Returns:
        Tuple: (is_valid: bool, error_message: str or None)
    """
    if not url or not url.strip():
        return False, "URL kiriting"

    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'youtube\.com/playlist\?list='
    ]

    if not any(re.search(pattern, url) for pattern in youtube_patterns):
        return False, "YouTube URL emas. Iltimos, to'g'ri YouTube havolasini kiriting."

    return True, None


def validate_instagram_url(url):
    """
    Validate if URL is a valid Instagram URL.

    Returns:
        Tuple: (is_valid: bool, error_message: str or None)
    """
    if not url or not url.strip():
        return False, "URL kiriting"

    instagram_patterns = [
        r'(https?://)?(www\.)?instagram\.com/(p|reel|stories)/',
        r'instagram\.com/(p|reel|stories)/',
    ]

    if not any(re.search(pattern, url) for pattern in instagram_patterns):
        return False, "Instagram URL emas. Post, reel yoki story havolasini kiriting."

    return True, None


# ============================================================================
# ERROR MESSAGE TRANSLATION
# ============================================================================

def translate_error(exception):
    """
    Convert raw exceptions to user-friendly Uzbek messages.

    Args:
        exception: Exception object or string

    Returns:
        str: User-friendly Uzbek error message
    """
    error_str = str(exception).lower()

    if '403' in error_str or 'forbidden' in error_str:
        return "Video bloklangan yoki shaxsiy. Boshqa video tanlang."
    elif '404' in error_str or 'not found' in error_str:
        return "Video topilmadi. URL to'g'riligini tekshiring."
    elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
        return "Internet ulanishi bilan muammo. Ulanishni tekshiring."
    elif 'ffmpeg' in error_str:
        return "FFmpeg topilmadi. Iltimos, FFmpeg o'rnating:\nbrew install ffmpeg"
    elif 'private' in error_str:
        return "Bu video shaxsiy. Ommaviy videoni tanlang."
    elif 'copyright' in error_str or 'blocked' in error_str:
        return "Video mualliflik huquqi sabab yuklab bo'lmaydi."
    elif 'age' in error_str or 'restricted' in error_str:
        return "Bu video yoshga bo'ysunadi. Ruxsat uchun kiriting."
    else:
        return f"Xatolik: {str(exception)}"


# ============================================================================
# FFMPEG INSTALLATION CHECK
# ============================================================================

def check_ffmpeg_installed():
    """
    Check if FFmpeg is installed and accessible.

    Returns:
        Tuple: (is_installed: bool, error_message: str or None)
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True,
                              timeout=5)
        if result.returncode == 0:
            return True, None
        else:
            return False, "FFmpeg topilmadi."
    except FileNotFoundError:
        return False, "FFmpeg o'rnatilmagan. Yuklab olish uchun FFmpeg kerak.\n\nO'rnatish:\nbrew install ffmpeg"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg tekshirishda vaqt tugadi."
    except Exception as e:
        return False, f"FFmpeg tekshirishda xatolik: {str(e)}"


# ============================================================================
# BYTE FORMATTING
# ============================================================================

def format_bytes(bytes_val):
    """
    Convert bytes to human-readable format.

    Args:
        bytes_val: Number of bytes (int or float)

    Returns:
        str: Formatted string (e.g., "123.4 MB")
    """
    if bytes_val is None or bytes_val == 0:
        return "N/A"

    bytes_val = float(bytes_val)

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0

    return f"{bytes_val:.1f} TB"


# ============================================================================
# METADATA CACHE
# ============================================================================

class MetadataCache:
    """
    Cache video metadata to prevent duplicate yt-dlp API calls.
    Each cache entry expires after TTL (default 5 minutes).
    """

    def __init__(self, ttl=300):
        """
        Initialize metadata cache.

        Args:
            ttl: Time-to-live in seconds (default 300 = 5 minutes)
        """
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl

    def get(self, url):
        """
        Get cached metadata if valid (not expired).

        Args:
            url: Video URL to look up

        Returns:
            dict: Cached metadata, or None if not found/expired
        """
        if url not in self._cache:
            return None

        # Check if expired
        if time.time() - self._timestamps[url] >= self._ttl:
            # Expired, remove
            del self._cache[url]
            del self._timestamps[url]
            return None

        return self._cache[url]

    def set(self, url, metadata):
        """
        Cache metadata for a video URL.

        Args:
            url: Video URL (key)
            metadata: Video metadata (value)
        """
        self._cache[url] = metadata
        self._timestamps[url] = time.time()

    def clear(self):
        """Clear all cached metadata."""
        self._cache.clear()
        self._timestamps.clear()

    def clear_expired(self):
        """Remove only expired entries."""
        current_time = time.time()
        expired_urls = [
            url for url, timestamp in self._timestamps.items()
            if current_time - timestamp >= self._ttl
        ]

        for url in expired_urls:
            del self._cache[url]
            del self._timestamps[url]


# Global metadata cache instance
# Use: from utils import metadata_cache
metadata_cache = MetadataCache(ttl=300)  # 5 minute TTL
