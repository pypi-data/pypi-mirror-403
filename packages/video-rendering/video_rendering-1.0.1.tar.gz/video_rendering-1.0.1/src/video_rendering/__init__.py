"""video-rendering: Convert image sequences to MP4/GIF and videos to GIF.

Example:
    >>> from video_rendering import VideoRenderer, GifConverter
    >>>
    >>> # Images to video
    >>> renderer = VideoRenderer()
    >>> renderer.render("./frames/", "output.mp4", fps=30)
    >>> renderer.render("./frames/", "output.gif", fps=15)
    >>>
    >>> # Video to GIF
    >>> converter = GifConverter()
    >>> converter.convert("video.mp4", "output.gif", fps=10, width=480)
"""

from video_rendering.config import Codec, Quality, SortOrder
from video_rendering.core.converter import GifConverter
from video_rendering.core.renderer import VideoRenderer
from video_rendering.exceptions import (
    FFmpegError,
    FFmpegNotFoundError,
    InvalidImageError,
    InvalidVideoError,
    NoImagesFoundError,
    OutputPathError,
    VideoRenderingError,
)
from video_rendering.utils.ffmpeg_check import check_ffmpeg, get_ffmpeg_version

__version__ = "1.0.1"
__all__ = [
    # Main classes
    "VideoRenderer",
    "GifConverter",
    # Configuration
    "Quality",
    "Codec",
    "SortOrder",
    # Exceptions
    "VideoRenderingError",
    "FFmpegNotFoundError",
    "FFmpegError",
    "NoImagesFoundError",
    "InvalidImageError",
    "InvalidVideoError",
    "OutputPathError",
    # Utilities
    "check_ffmpeg",
    "get_ffmpeg_version",
    # Version
    "__version__",
]
