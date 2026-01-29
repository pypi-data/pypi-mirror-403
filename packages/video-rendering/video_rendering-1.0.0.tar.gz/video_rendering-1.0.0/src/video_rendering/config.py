"""Configuration enums and constants for video-rendering package."""

from enum import Enum


class Quality(Enum):
    """Video quality presets using FFmpeg CRF values.

    Lower CRF = higher quality, larger file size.
    """

    LOW = 28  # Quick previews, small files
    MEDIUM = 23  # Balanced quality (default for GIF)
    HIGH = 18  # High quality (default for video)
    LOSSLESS = 0  # Maximum quality, largest files


class Codec(Enum):
    """Video codec options."""

    H264 = "libx264"  # Most compatible
    H265 = "libx265"  # Better compression, less compatible
    VP9 = "libvpx-vp9"  # WebM format


class SortOrder(Enum):
    """Image sorting options."""

    NATURAL = "natural"  # 1, 2, 10 (not 1, 10, 2)
    ALPHABETICAL = "alphabetical"  # Standard string sort
    MODIFICATION_TIME = "mtime"  # By file modification time
    CREATION_TIME = "ctime"  # By file creation time


# Supported image extensions
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"})

# Supported video extensions for conversion
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})

# Default values
DEFAULT_FPS = 30
DEFAULT_VIDEO_QUALITY = Quality.HIGH
DEFAULT_GIF_QUALITY = Quality.MEDIUM
DEFAULT_CODEC = Codec.H264
DEFAULT_SORT_ORDER = SortOrder.NATURAL

# FFmpeg pixel format for compatibility
PIXEL_FORMAT = "yuv420p"
