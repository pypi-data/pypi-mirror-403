"""GifConverter for converting videos to GIF format."""

from pathlib import Path

from tqdm import tqdm

from video_rendering.config import VIDEO_EXTENSIONS
from video_rendering.core.ffmpeg import FFmpegWrapper
from video_rendering.exceptions import InvalidVideoError, OutputPathError


class GifConverter:
    """Convert video files to optimized GIF format.

    Uses two-pass palette optimization for better quality and smaller file size.

    Example:
        >>> converter = GifConverter()
        >>> converter.convert("video.mp4", "output.gif", fps=10, width=480)
    """

    def __init__(self) -> None:
        """Initialize GifConverter."""
        self._ffmpeg = FFmpegWrapper()

    def convert(
        self,
        input_path: str | Path,
        output_path: str | Path,
        fps: int = 10,
        width: int | None = None,
        start_time: float | None = None,
        duration: float | None = None,
        show_progress: bool = True,
    ) -> Path:
        """Convert video to GIF with palette optimization.

        Args:
            input_path: Path to input video file.
            output_path: Path for output GIF file.
            fps: Output frames per second (default: 10).
            width: Optional width to resize to (maintains aspect ratio).
            start_time: Optional start time in seconds.
            duration: Optional duration in seconds.
            show_progress: Whether to show progress messages.

        Returns:
            Path to created GIF file.

        Raises:
            InvalidVideoError: If input video is invalid.
            OutputPathError: If output path is invalid.
            FFmpegError: If conversion fails.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Validate input
        self._validate_input(input_path)

        # Validate output
        self._validate_output(output_path)

        if show_progress:
            tqdm.write(f"Converting: {input_path}")
            if width:
                tqdm.write(f"  Resizing to width: {width}px")
            if start_time is not None or duration is not None:
                time_info = []
                if start_time is not None:
                    time_info.append(f"start={start_time}s")
                if duration is not None:
                    time_info.append(f"duration={duration}s")
                tqdm.write(f"  Time range: {', '.join(time_info)}")

        result = self._ffmpeg.convert_video_to_gif(
            input_path=input_path,
            output_path=output_path,
            fps=fps,
            width=width,
            start_time=start_time,
            duration=duration,
        )

        if show_progress:
            file_size = result.stat().st_size
            size_str = self._format_file_size(file_size)
            tqdm.write(f"Created: {result} ({size_str})")

        return result

    def get_video_info(self, video_path: str | Path) -> dict[str, str | int | float]:
        """Get video metadata.

        Args:
            video_path: Path to video file.

        Returns:
            Dictionary with video information including:
            - duration: Video duration in seconds
            - width: Video width in pixels
            - height: Video height in pixels
            - fps: Frames per second
            - codec: Video codec name
        """
        video_path = Path(video_path)
        self._validate_input(video_path)

        raw_info = self._ffmpeg.get_video_info(video_path)

        # Extract useful info from ffprobe output
        result: dict[str, str | int | float] = {}

        if "format" in raw_info:
            format_info = raw_info["format"]
            if isinstance(format_info, dict) and "duration" in format_info:
                result["duration"] = float(format_info["duration"])

        if "streams" in raw_info:
            streams = raw_info["streams"]
            if isinstance(streams, list):
                for stream in streams:
                    if isinstance(stream, dict) and stream.get("codec_type") == "video":
                        if "width" in stream:
                            result["width"] = int(stream["width"])
                        if "height" in stream:
                            result["height"] = int(stream["height"])
                        if "codec_name" in stream:
                            result["codec"] = str(stream["codec_name"])
                        if "r_frame_rate" in stream:
                            # Parse frame rate like "30/1" or "30000/1001"
                            fps_str = str(stream["r_frame_rate"])
                            if "/" in fps_str:
                                num, den = fps_str.split("/")
                                result["fps"] = float(num) / float(den)
                            else:
                                result["fps"] = float(fps_str)
                        break

        return result

    def _validate_input(self, input_path: Path) -> None:
        """Validate input video file.

        Args:
            input_path: Path to validate.

        Raises:
            InvalidVideoError: If file is invalid.
        """
        if not input_path.exists():
            raise InvalidVideoError(str(input_path), "File does not exist")

        if not input_path.is_file():
            raise InvalidVideoError(str(input_path), "Path is not a file")

        if input_path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise InvalidVideoError(
                str(input_path),
                f"Unsupported format: {input_path.suffix}. "
                f"Supported: {', '.join(VIDEO_EXTENSIONS)}",
            )

    def _validate_output(self, output_path: Path) -> None:
        """Validate output path.

        Args:
            output_path: Path to validate.

        Raises:
            OutputPathError: If path is invalid.
        """
        if output_path.suffix.lower() != ".gif":
            raise OutputPathError(
                str(output_path),
                f"Output must be .gif, got: {output_path.suffix}",
            )

        # Ensure parent directory exists or can be created
        parent = output_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OutputPathError(str(output_path), f"Cannot create directory: {e}") from e

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted string like "1.5 MB".
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024  # type: ignore[assignment]
        return f"{size_bytes:.1f} TB"
