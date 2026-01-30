"""Image to ASCII/Braille art converter."""

from io import BytesIO

import httpx
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# Braille Unicode base: U+2800
# Dot positions (bit values):
# 1 (0x01)  4 (0x08)
# 2 (0x02)  5 (0x10)
# 3 (0x04)  6 (0x20)
# 7 (0x40)  8 (0x80)
BRAILLE_BASE = 0x2800

# Braille dot bit positions for each pixel in a 2x4 cell
# [row][col] -> bit value
BRAILLE_DOTS = [
    [0x01, 0x08],  # row 0
    [0x02, 0x10],  # row 1
    [0x04, 0x20],  # row 2
    [0x40, 0x80],  # row 3
]


def image_to_braille(
    image: Image.Image,
    width: int = 60,
    edge_mode: bool = True,
) -> str:
    """Convert PIL Image to Braille Unicode art.

    Each Braille character represents a 2x4 pixel block.
    """
    # Calculate dimensions (2 pixels per char width, 4 pixels per char height)
    char_width = width
    pixel_width = char_width * 2

    # Maintain aspect ratio
    aspect_ratio = image.height / image.width
    pixel_height = int(pixel_width * aspect_ratio)
    # Round up to multiple of 4
    pixel_height = ((pixel_height + 3) // 4) * 4

    # Resize image
    image = image.resize((pixel_width, pixel_height), Image.Resampling.LANCZOS)

    # Convert to grayscale
    image = image.convert("L")

    if edge_mode:
        # Edge detection for line art (better for circle cuts)
        image = image.filter(ImageFilter.FIND_EDGES)
        image = ImageOps.invert(image)
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        # Use Otsu-like thresholding
        pixels = list(image.getdata())
        threshold = sum(pixels) // len(pixels)  # Mean as threshold
    else:
        # Dithering for photos/gradients
        image = image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        pixels = list(image.getdata())
        threshold = 1  # Binary image, 0 = black, 255 = white

    pixels = list(image.getdata())

    def get_pixel(x: int, y: int) -> bool:
        """Get pixel value as boolean (True = dark/filled)."""
        if x >= pixel_width or y >= pixel_height:
            return False
        idx = y * pixel_width + x
        if idx >= len(pixels):
            return False
        # Dark pixels become dots
        return pixels[idx] < threshold

    lines = []
    for char_y in range(pixel_height // 4):
        line = []
        for char_x in range(char_width):
            # Calculate braille character for this 2x4 block
            code = BRAILLE_BASE
            px = char_x * 2
            py = char_y * 4

            for row in range(4):
                for col in range(2):
                    if get_pixel(px + col, py + row):
                        code |= BRAILLE_DOTS[row][col]

            line.append(chr(code))
        lines.append("".join(line))

    return "\n".join(lines)


def fetch_image_as_braille(url: str, width: int = 40, edge_mode: bool = False) -> str:
    """Fetch image from URL and convert to Braille art.

    Default width=40 for circle cuts (typically 180x252, tall images).
    Default edge_mode=False uses dithering for better gradation.
    """
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content))
    return image_to_braille(image, width, edge_mode)
