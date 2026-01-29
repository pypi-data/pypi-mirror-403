"""Image loading and validation utilities."""

from pathlib import Path

from natsort import natsorted
from PIL import Image

from video_rendering.config import IMAGE_EXTENSIONS, SortOrder
from video_rendering.exceptions import InvalidImageError, NoImagesFoundError


def load_images_from_directory(
    directory: str | Path,
    pattern: str | None = None,
    sort_order: SortOrder = SortOrder.NATURAL,
) -> list[Path]:
    """Load and sort image files from a directory.

    Args:
        directory: Path to directory containing images.
        pattern: Optional glob pattern (e.g., "frame_*.png").
        sort_order: How to sort the images.

    Returns:
        List of sorted image paths.

    Raises:
        NoImagesFoundError: If no images are found.
    """
    directory = Path(directory)

    if not directory.exists():
        raise NoImagesFoundError(str(directory), pattern)

    if not directory.is_dir():
        raise NoImagesFoundError(str(directory), "Path is not a directory")

    # Collect images
    images: list[Path] = []

    if pattern:
        # Use provided glob pattern
        images = [p for p in directory.glob(pattern) if p.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        # Find all supported image files
        images = [p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]

    if not images:
        raise NoImagesFoundError(str(directory), pattern)

    # Sort images
    images = _sort_images(images, sort_order)

    return images


def _sort_images(images: list[Path], sort_order: SortOrder) -> list[Path]:
    """Sort images according to the specified order.

    Args:
        images: List of image paths.
        sort_order: Sorting method to use.

    Returns:
        Sorted list of image paths.
    """
    if sort_order == SortOrder.NATURAL:
        # Natural sort: 1, 2, 10 instead of 1, 10, 2
        return natsorted(images, key=lambda p: str(p.name))
    elif sort_order == SortOrder.ALPHABETICAL:
        return sorted(images, key=lambda p: p.name)
    elif sort_order == SortOrder.MODIFICATION_TIME:
        return sorted(images, key=lambda p: p.stat().st_mtime)
    elif sort_order == SortOrder.CREATION_TIME:
        return sorted(images, key=lambda p: p.stat().st_ctime)
    else:
        return list(images)


def validate_image(path: str | Path) -> bool:
    """Validate that a file is a valid image.

    Args:
        path: Path to image file.

    Returns:
        True if the image is valid.

    Raises:
        InvalidImageError: If the image is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise InvalidImageError(str(path), "File does not exist")

    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise InvalidImageError(str(path), f"Unsupported format: {path.suffix}")

    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as e:
        raise InvalidImageError(str(path), str(e)) from e


def get_image_dimensions(path: str | Path) -> tuple[int, int]:
    """Get dimensions of an image.

    Args:
        path: Path to image file.

    Returns:
        Tuple of (width, height).

    Raises:
        InvalidImageError: If the image cannot be read.
    """
    path = Path(path)

    try:
        with Image.open(path) as img:
            return img.size
    except Exception as e:
        raise InvalidImageError(str(path), str(e)) from e
