"""Command-line interface for video-rendering package."""

import sys
from pathlib import Path

import click

from video_rendering import __version__
from video_rendering.config import Codec, Quality, SortOrder
from video_rendering.core.converter import GifConverter
from video_rendering.core.renderer import VideoRenderer
from video_rendering.exceptions import (
    FFmpegNotFoundError,
    InvalidVideoError,
    NoImagesFoundError,
    OutputPathError,
    VideoRenderingError,
)
from video_rendering.utils.ffmpeg_check import check_ffmpeg, get_ffmpeg_version


@click.group()
@click.version_option(__version__, "-V", "--version")
def main() -> None:
    """video-render: Convert images to video/GIF and videos to GIF.

    Use 'video-render COMMAND --help' for command-specific help.
    """
    pass


@main.command("images")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file path (.mp4, .gif, etc.)",
)
@click.option(
    "--fps",
    type=int,
    default=30,
    show_default=True,
    help="Frames per second",
)
@click.option(
    "--pattern",
    type=str,
    default=None,
    help="Glob pattern to filter images (e.g., 'frame_*.png')",
)
@click.option(
    "--sort",
    type=click.Choice(["natural", "alphabetical", "mtime", "ctime"]),
    default="natural",
    show_default=True,
    help="Image sorting order",
)
@click.option(
    "--codec",
    type=click.Choice(["h264", "h265", "vp9"]),
    default="h264",
    show_default=True,
    help="Video codec (for video output only)",
)
@click.option(
    "--quality",
    type=click.Choice(["low", "medium", "high", "lossless"]),
    default=None,
    help="Quality preset (default: high for video, medium for gif)",
)
def images_command(
    folder: Path,
    output: Path,
    fps: int,
    pattern: str | None,
    sort: str,
    codec: str,
    quality: str | None,
) -> None:
    """Convert image sequence to video or GIF.

    FOLDER is the directory containing image files.

    Examples:

        video-render images ./frames/ -o output.mp4

        video-render images ./frames/ -o output.gif --fps 15

        video-render images ./frames/ -o output.mp4 --pattern "frame_*.png"
    """
    # Map string options to enums
    sort_order_map = {
        "natural": SortOrder.NATURAL,
        "alphabetical": SortOrder.ALPHABETICAL,
        "mtime": SortOrder.MODIFICATION_TIME,
        "ctime": SortOrder.CREATION_TIME,
    }
    codec_map = {
        "h264": Codec.H264,
        "h265": Codec.H265,
        "vp9": Codec.VP9,
    }
    quality_map = {
        "low": Quality.LOW,
        "medium": Quality.MEDIUM,
        "high": Quality.HIGH,
        "lossless": Quality.LOSSLESS,
    }

    try:
        renderer = VideoRenderer()
        renderer.render(
            input_directory=folder,
            output_path=output,
            fps=fps,
            pattern=pattern,
            sort_order=sort_order_map[sort],
            codec=codec_map[codec],
            quality=quality_map[quality] if quality else None,
            show_progress=True,
        )
    except FFmpegNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Run 'video-render doctor' to check your FFmpeg installation.", err=True)
        sys.exit(1)
    except NoImagesFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except OutputPathError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except VideoRenderingError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("convert")
@click.argument("video", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output GIF path",
)
@click.option(
    "--fps",
    type=int,
    default=10,
    show_default=True,
    help="Output frames per second",
)
@click.option(
    "--width",
    type=int,
    default=None,
    help="Output width in pixels (maintains aspect ratio)",
)
@click.option(
    "--start",
    type=float,
    default=None,
    help="Start time in seconds",
)
@click.option(
    "--duration",
    type=float,
    default=None,
    help="Duration in seconds",
)
def convert_command(
    video: Path,
    output: Path,
    fps: int,
    width: int | None,
    start: float | None,
    duration: float | None,
) -> None:
    """Convert video to GIF with palette optimization.

    VIDEO is the input video file path.

    Examples:

        video-render convert video.mp4 -o output.gif

        video-render convert video.mp4 -o output.gif --fps 10 --width 480

        video-render convert video.mp4 -o output.gif --start 5 --duration 10
    """
    try:
        converter = GifConverter()
        converter.convert(
            input_path=video,
            output_path=output,
            fps=fps,
            width=width,
            start_time=start,
            duration=duration,
            show_progress=True,
        )
    except FFmpegNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Run 'video-render doctor' to check your FFmpeg installation.", err=True)
        sys.exit(1)
    except InvalidVideoError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except OutputPathError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except VideoRenderingError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("version")
def version_command() -> None:
    """Show version information."""
    click.echo(f"video-rendering {__version__}")


@main.command("doctor")
def doctor_command() -> None:
    """Check FFmpeg installation and system requirements."""
    click.echo("Checking system requirements...\n")

    # Check FFmpeg
    click.echo("FFmpeg:")
    if check_ffmpeg():
        try:
            version = get_ffmpeg_version()
            click.echo(f"  [OK] {version}")
        except Exception:
            click.echo("  [OK] FFmpeg found")
    else:
        click.echo("  [ERROR] FFmpeg not found")
        click.echo("")
        click.echo("Installation instructions:")
        click.echo("  macOS:   brew install ffmpeg")
        click.echo("  Ubuntu:  sudo apt install ffmpeg")
        click.echo("  Windows: https://ffmpeg.org/download.html")
        sys.exit(1)

    # Check FFprobe
    click.echo("\nFFprobe:")
    from video_rendering.utils.ffmpeg_check import get_ffprobe_path

    try:
        ffprobe_path = get_ffprobe_path()
        click.echo(f"  [OK] Found at {ffprobe_path}")
    except FFmpegNotFoundError:
        click.echo("  [WARNING] FFprobe not found (optional, used for video info)")

    click.echo("\nAll checks passed!")


if __name__ == "__main__":
    main()
