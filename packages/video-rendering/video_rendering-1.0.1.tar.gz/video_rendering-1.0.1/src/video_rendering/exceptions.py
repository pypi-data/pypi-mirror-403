"""Custom exceptions for video-rendering package."""


class VideoRenderingError(Exception):
    """Base exception for video-rendering package."""

    pass


class FFmpegNotFoundError(VideoRenderingError):
    """Raised when FFmpeg is not installed or not found in PATH."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
        )


class FFmpegError(VideoRenderingError):
    """Raised when FFmpeg command fails."""

    def __init__(self, message: str, stderr: str | None = None) -> None:
        full_message = message
        if stderr:
            full_message = f"{message}\nFFmpeg output: {stderr}"
        super().__init__(full_message)
        self.stderr = stderr


class NoImagesFoundError(VideoRenderingError):
    """Raised when no images are found in the specified directory."""

    def __init__(self, directory: str, pattern: str | None = None) -> None:
        msg = f"No images found in directory: {directory}"
        if pattern:
            msg += f" (pattern: {pattern})"
        super().__init__(msg)
        self.directory = directory
        self.pattern = pattern


class InvalidImageError(VideoRenderingError):
    """Raised when an image file is invalid or corrupted."""

    def __init__(self, path: str, reason: str | None = None) -> None:
        msg = f"Invalid image file: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path
        self.reason = reason


class InvalidVideoError(VideoRenderingError):
    """Raised when a video file is invalid or corrupted."""

    def __init__(self, path: str, reason: str | None = None) -> None:
        msg = f"Invalid video file: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path
        self.reason = reason


class OutputPathError(VideoRenderingError):
    """Raised when output path is invalid or not writable."""

    def __init__(self, path: str, reason: str | None = None) -> None:
        msg = f"Invalid output path: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path
        self.reason = reason
