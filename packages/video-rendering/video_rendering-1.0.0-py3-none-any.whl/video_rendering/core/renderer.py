"""VideoRenderer for converting image sequences to video/GIF."""

import tempfile
from pathlib import Path

from tqdm import tqdm

from video_rendering.config import (
    DEFAULT_CODEC,
    DEFAULT_FPS,
    DEFAULT_GIF_QUALITY,
    DEFAULT_VIDEO_QUALITY,
    Codec,
    Quality,
    SortOrder,
)
from video_rendering.core.ffmpeg import FFmpegWrapper
from video_rendering.exceptions import NoImagesFoundError, OutputPathError
from video_rendering.utils.images import load_images_from_directory


class VideoRenderer:
    """Render image sequences to video or GIF files.

    Example:
        >>> renderer = VideoRenderer()
        >>> renderer.render("./frames/", "output.mp4", fps=30)
        >>> renderer.render("./frames/", "output.gif", fps=15)
    """

    def __init__(self) -> None:
        """Initialize VideoRenderer."""
        self._ffmpeg = FFmpegWrapper()

    def render(
        self,
        input_directory: str | Path,
        output_path: str | Path,
        fps: int = DEFAULT_FPS,
        pattern: str | None = None,
        sort_order: SortOrder = SortOrder.NATURAL,
        codec: Codec = DEFAULT_CODEC,
        quality: Quality | None = None,
        show_progress: bool = True,
    ) -> Path:
        """Render images from directory to video or GIF.

        Output format is determined by the output file extension:
        - .mp4, .mov, .avi, .mkv, .webm -> Video
        - .gif -> GIF

        Args:
            input_directory: Directory containing image files.
            output_path: Output file path (.mp4, .gif, etc.).
            fps: Frames per second.
            pattern: Optional glob pattern to filter images (e.g., "frame_*.png").
            sort_order: How to sort images before rendering.
            codec: Video codec (only used for video output).
            quality: Quality preset. Defaults to HIGH for video, MEDIUM for GIF.
            show_progress: Whether to show progress messages.

        Returns:
            Path to the created output file.

        Raises:
            NoImagesFoundError: If no images found in directory.
            OutputPathError: If output path is invalid.
            FFmpegError: If encoding fails.
        """
        input_directory = Path(input_directory)
        output_path = Path(output_path)

        # Validate output path
        self._validate_output_path(output_path)

        # Load and sort images
        images = load_images_from_directory(input_directory, pattern, sort_order)

        if not images:
            raise NoImagesFoundError(str(input_directory), pattern)

        # Show progress
        if show_progress:
            tqdm.write(f"Found {len(images)} images in {input_directory}")

        # Determine if output is GIF
        is_gif = output_path.suffix.lower() == ".gif"

        # Set default quality based on output type
        if quality is None:
            quality = DEFAULT_GIF_QUALITY if is_gif else DEFAULT_VIDEO_QUALITY

        # Create concat file for ffmpeg
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as concat_file:
            for image in images:
                # Escape single quotes in paths
                escaped_path = str(image.absolute()).replace("'", "'\\''")
                concat_file.write(f"file '{escaped_path}'\n")
                concat_file.write(f"duration {1/fps}\n")

            # Add last image again (FFmpeg concat quirk)
            escaped_path = str(images[-1].absolute()).replace("'", "'\\''")
            concat_file.write(f"file '{escaped_path}'\n")

            concat_path = concat_file.name

        try:
            if is_gif:
                result = self._ffmpeg.create_gif_from_images(
                    concat_file=concat_path,
                    output_path=output_path,
                    fps=fps,
                    quality=quality,
                )
            else:
                result = self._ffmpeg.create_video_from_concat(
                    concat_file=concat_path,
                    output_path=output_path,
                    fps=fps,
                    codec=codec,
                    quality=quality,
                )

            if show_progress:
                tqdm.write(f"Created: {result}")

            return result

        finally:
            # Clean up concat file
            Path(concat_path).unlink(missing_ok=True)

    def render_with_progress(
        self,
        input_directory: str | Path,
        output_path: str | Path,
        fps: int = DEFAULT_FPS,
        pattern: str | None = None,
        sort_order: SortOrder = SortOrder.NATURAL,
        codec: Codec = DEFAULT_CODEC,
        quality: Quality | None = None,
    ) -> Path:
        """Render with tqdm progress bar.

        Same as render() but always shows progress bar.
        """
        return self.render(
            input_directory=input_directory,
            output_path=output_path,
            fps=fps,
            pattern=pattern,
            sort_order=sort_order,
            codec=codec,
            quality=quality,
            show_progress=True,
        )

    def get_image_count(
        self,
        input_directory: str | Path,
        pattern: str | None = None,
    ) -> int:
        """Get count of images in directory.

        Args:
            input_directory: Directory to scan.
            pattern: Optional glob pattern.

        Returns:
            Number of images found.
        """
        try:
            images = load_images_from_directory(input_directory, pattern)
            return len(images)
        except NoImagesFoundError:
            return 0

    def list_images(
        self,
        input_directory: str | Path,
        pattern: str | None = None,
        sort_order: SortOrder = SortOrder.NATURAL,
    ) -> list[Path]:
        """List images that would be rendered.

        Args:
            input_directory: Directory to scan.
            pattern: Optional glob pattern.
            sort_order: How to sort the images.

        Returns:
            Sorted list of image paths.
        """
        return load_images_from_directory(input_directory, pattern, sort_order)

    def _validate_output_path(self, output_path: Path) -> None:
        """Validate output path is writable.

        Args:
            output_path: Path to validate.

        Raises:
            OutputPathError: If path is invalid.
        """
        # Check extension
        valid_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}
        if output_path.suffix.lower() not in valid_extensions:
            raise OutputPathError(
                str(output_path),
                f"Unsupported format: {output_path.suffix}. "
                f"Supported: {', '.join(valid_extensions)}",
            )

        # Check parent directory
        parent = output_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OutputPathError(str(output_path), f"Cannot create directory: {e}") from e
