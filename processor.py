import logging
import os
from pathlib import Path

import pyheif
from PIL import Image, ImageOps

from utils import get_file_extension

LOGGER = logging.getLogger(__name__)
HEIF_EXTENSIONS = {".heic", ".heif"}
DEFAULT_MAX_WIDTH = int(os.getenv("MAX_WIDTH", "0"))
DEFAULT_MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "0"))
DEFAULT_QUALITY = int(os.getenv("JPEG_QUALITY", "85"))



def process_image(
    input_path: str,
    output_path: str,
    *,
    max_width: int = DEFAULT_MAX_WIDTH,
    max_height: int = DEFAULT_MAX_HEIGHT,
    quality: int = DEFAULT_QUALITY,
) -> dict:
    """Load an image, normalize it, and write a compressed JPEG output."""
    source = Path(input_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with _load_image(source) as image:
        original_size = image.size
        processed = ImageOps.exif_transpose(image)
        processed = _resize_image(processed, max_width=max_width, max_height=max_height)
        processed = _prepare_for_jpeg(processed)
        processed.save(destination, format="JPEG", quality=quality, optimize=True)

    LOGGER.info(
        "Processed image %s -> %s (original=%s, final=%s, quality=%s)",
        source,
        destination,
        original_size,
        processed.size,
        quality,
    )
    return {
        "input_path": str(source),
        "output_path": str(destination),
        "original_size": original_size,
        "output_size": processed.size,
        "quality": quality,
    }



def _load_image(path: Path) -> Image.Image:
    extension = get_file_extension(path.name)
    LOGGER.info("Opening image %s with extension %s", path, extension)

    if extension in HEIF_EXTENSIONS:
        return _load_heif_image(path)

    image = Image.open(path)
    image.load()
    return image



def _load_heif_image(path: Path) -> Image.Image:
    """Read HEIC/HEIF data and convert it into a Pillow image."""
    heif_file = pyheif.read(str(path))
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    image.load()
    return image



def _resize_image(image: Image.Image, *, max_width: int, max_height: int) -> Image.Image:
    """Resize in place only when max dimensions were configured."""
    if max_width <= 0 and max_height <= 0:
        LOGGER.info("Resize skipped because MAX_WIDTH and MAX_HEIGHT are not set")
        return image

    target_width = max_width if max_width > 0 else image.width
    target_height = max_height if max_height > 0 else image.height
    resized = image.copy()
    resized.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
    LOGGER.info("Resized image from %s to %s", image.size, resized.size)
    return resized



def _prepare_for_jpeg(image: Image.Image) -> Image.Image:
    """JPEG does not support alpha, so flatten transparency when needed."""
    if image.mode in {"RGB", "L"}:
        return image.convert("RGB")

    if image.mode in {"RGBA", "LA", "P"}:
        rgba_image = image.convert("RGBA")
        background = Image.new("RGB", rgba_image.size, (255, 255, 255))
        background.paste(rgba_image, mask=rgba_image.getchannel("A"))
        return background

    return image.convert("RGB")
