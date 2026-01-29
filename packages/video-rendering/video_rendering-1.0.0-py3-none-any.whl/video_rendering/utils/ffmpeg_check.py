"""FFmpeg detection and validation utilities."""

import shutil
import subprocess
from functools import lru_cache

from video_rendering.exceptions import FFmpegNotFoundError


@lru_cache(maxsize=1)
def get_ffmpeg_path() -> str:
    """Find the FFmpeg binary path.

    Returns:
        Path to ffmpeg binary.

    Raises:
        FFmpegNotFoundError: If FFmpeg is not found.
    """
    path = shutil.which("ffmpeg")
    if path is None:
        raise FFmpegNotFoundError()
    return path


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is available.
    """
    try:
        get_ffmpeg_path()
        return True
    except FFmpegNotFoundError:
        return False


@lru_cache(maxsize=1)
def get_ffmpeg_version() -> str:
    """Get FFmpeg version string.

    Returns:
        Version string from ffmpeg -version.

    Raises:
        FFmpegNotFoundError: If FFmpeg is not found.
    """
    ffmpeg_path = get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # First line contains version info
        first_line = result.stdout.split("\n")[0]
        return first_line
    except subprocess.CalledProcessError as e:
        raise FFmpegNotFoundError(f"FFmpeg version check failed: {e.stderr}") from e


def get_ffprobe_path() -> str:
    """Find the FFprobe binary path.

    Returns:
        Path to ffprobe binary.

    Raises:
        FFmpegNotFoundError: If FFprobe is not found.
    """
    path = shutil.which("ffprobe")
    if path is None:
        raise FFmpegNotFoundError(
            "FFprobe not found. FFprobe is usually installed alongside FFmpeg."
        )
    return path
