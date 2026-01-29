"""FFmpeg wrapper for video encoding and GIF creation."""

import subprocess
import tempfile
from pathlib import Path

from video_rendering.config import PIXEL_FORMAT, Codec, Quality
from video_rendering.exceptions import FFmpegError
from video_rendering.utils.ffmpeg_check import get_ffmpeg_path


class FFmpegWrapper:
    """Wrapper for FFmpeg command execution."""

    def __init__(self) -> None:
        """Initialize FFmpeg wrapper."""
        self._ffmpeg_path = get_ffmpeg_path()

    def create_video_from_images(
        self,
        image_pattern: str,
        output_path: str | Path,
        fps: int = 30,
        codec: Codec = Codec.H264,
        quality: Quality = Quality.HIGH,
    ) -> Path:
        """Create video from image sequence using pattern.

        Args:
            image_pattern: FFmpeg input pattern (e.g., "frames/%04d.png").
            output_path: Path for output video file.
            fps: Frames per second.
            codec: Video codec to use.
            quality: Quality preset.

        Returns:
            Path to created video file.

        Raises:
            FFmpegError: If encoding fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._ffmpeg_path,
            "-y",  # Overwrite output
            "-framerate",
            str(fps),
            "-i",
            image_pattern,
            "-c:v",
            codec.value,
            "-crf",
            str(quality.value),
            "-pix_fmt",
            PIXEL_FORMAT,
            "-movflags",
            "+faststart",  # Enable streaming
            str(output_path),
        ]

        self._run_command(cmd)
        return output_path

    def create_video_from_concat(
        self,
        concat_file: str | Path,
        output_path: str | Path,
        fps: int = 30,
        codec: Codec = Codec.H264,
        quality: Quality = Quality.HIGH,
    ) -> Path:
        """Create video from concat demuxer file.

        Args:
            concat_file: Path to FFmpeg concat file listing images.
            output_path: Path for output video file.
            fps: Frames per second.
            codec: Video codec to use.
            quality: Quality preset.

        Returns:
            Path to created video file.

        Raises:
            FFmpegError: If encoding fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-r",
            str(fps),
            "-i",
            str(concat_file),
            "-c:v",
            codec.value,
            "-crf",
            str(quality.value),
            "-pix_fmt",
            PIXEL_FORMAT,
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        self._run_command(cmd)
        return output_path

    def create_gif_from_images(
        self,
        concat_file: str | Path,
        output_path: str | Path,
        fps: int = 15,
        width: int | None = None,
    ) -> Path:
        """Create optimized GIF from image sequence using palette.

        Uses two-pass encoding with palette optimization for better quality.

        Args:
            concat_file: Path to FFmpeg concat file listing images.
            output_path: Path for output GIF file.
            fps: Frames per second.
            width: Optional width to resize to (maintains aspect ratio).

        Returns:
            Path to created GIF file.

        Raises:
            FFmpegError: If encoding fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build filter string
        filters = []
        if width:
            filters.append(f"scale={width}:-1:flags=lanczos")
        filters.append("split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse")
        filter_str = ",".join(filters) if len(filters) > 1 else filters[0]

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-r",
            str(fps),
            "-i",
            str(concat_file),
            "-vf",
            filter_str,
            "-loop",
            "0",  # Loop forever
            str(output_path),
        ]

        self._run_command(cmd)
        return output_path

    def convert_video_to_gif(
        self,
        input_path: str | Path,
        output_path: str | Path,
        fps: int = 10,
        width: int | None = None,
        start_time: float | None = None,
        duration: float | None = None,
    ) -> Path:
        """Convert video to optimized GIF using two-pass palette method.

        Args:
            input_path: Path to input video file.
            output_path: Path for output GIF file.
            fps: Output frames per second.
            width: Optional width to resize to (maintains aspect ratio).
            start_time: Optional start time in seconds.
            duration: Optional duration in seconds.

        Returns:
            Path to created GIF file.

        Raises:
            FFmpegError: If conversion fails.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build filter string for both passes
        filters = [f"fps={fps}"]
        if width:
            filters.append(f"scale={width}:-1:flags=lanczos")

        filter_base = ",".join(filters)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            palette_path = tmp.name

        try:
            # Pass 1: Generate palette
            cmd_palette = [self._ffmpeg_path, "-y"]

            if start_time is not None:
                cmd_palette.extend(["-ss", str(start_time)])
            if duration is not None:
                cmd_palette.extend(["-t", str(duration)])

            cmd_palette.extend(
                [
                    "-i",
                    str(input_path),
                    "-vf",
                    f"{filter_base},palettegen=stats_mode=diff",
                    str(palette_path),
                ]
            )

            self._run_command(cmd_palette)

            # Pass 2: Create GIF with palette
            cmd_gif = [self._ffmpeg_path, "-y"]

            if start_time is not None:
                cmd_gif.extend(["-ss", str(start_time)])
            if duration is not None:
                cmd_gif.extend(["-t", str(duration)])

            cmd_gif.extend(
                [
                    "-i",
                    str(input_path),
                    "-i",
                    palette_path,
                    "-lavfi",
                    f"{filter_base}[x];[x][1:v]paletteuse",
                    "-loop",
                    "0",
                    str(output_path),
                ]
            )

            self._run_command(cmd_gif)

        finally:
            # Clean up palette file
            Path(palette_path).unlink(missing_ok=True)

        return output_path

    def _run_command(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute FFmpeg command.

        Args:
            cmd: Command and arguments to execute.

        Returns:
            Completed process result.

        Raises:
            FFmpegError: If command fails.
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"FFmpeg command failed: {' '.join(cmd)}", e.stderr) from e

    def get_video_info(self, video_path: str | Path) -> dict[str, str | int | float]:
        """Get video metadata using ffprobe.

        Args:
            video_path: Path to video file.

        Returns:
            Dictionary with video information.

        Raises:
            FFmpegError: If ffprobe fails.
        """
        from video_rendering.utils.ffmpeg_check import get_ffprobe_path

        ffprobe_path = get_ffprobe_path()
        video_path = Path(video_path)

        cmd = [
            ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json

            return json.loads(result.stdout)  # type: ignore[no-any-return]
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"Failed to get video info: {video_path}", e.stderr) from e
