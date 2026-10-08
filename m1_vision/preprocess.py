from pathlib import Path
from PIL import Image


def validate_image(input_path: str):
    """Validate a P&ID image before further processing."""

    image_path = Path(input_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with Image.open(image_path) as image:
        image.verify()

    with Image.open(image_path) as image:
        width, height = image.size
        mode = image.mode

    if width <= 0 or height <= 0:
        raise ValueError("Image has invalid dimensions.")

    return {
        "file": str(image_path),
        "width": width,
        "height": height,
        "mode": mode,
    }