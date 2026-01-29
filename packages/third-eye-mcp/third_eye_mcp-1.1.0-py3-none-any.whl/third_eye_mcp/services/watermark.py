"""Watermark utility for adding sponsored messages to images."""

from PIL import Image, ImageDraw, ImageFont


def add_watermark(
    img: Image.Image,
    text: str,
    position: str = "bottom",
    opacity: int = 180,
) -> Image.Image:
    """
    Add a watermark text to an image.

    Args:
        img: PIL Image to watermark
        text: Text to add as watermark
        position: Where to place watermark ("bottom" or "top")
        opacity: Background opacity (0-255)

    Returns:
        New PIL Image with watermark added
    """
    # Create a copy to avoid modifying original
    img = img.copy()

    # Ensure image is in RGBA mode for transparency
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    font_size = max(12, img.width // 60)  # Scale font with image size
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # Calculate text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Add padding
    padding_x = 10
    padding_y = 5
    bar_height = text_height + (padding_y * 2)

    # Calculate position
    if position == "top":
        bar_y = 0
        text_y = padding_y
    else:  # bottom
        bar_y = img.height - bar_height
        text_y = bar_y + padding_y

    # Draw semi-transparent background bar
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(0, bar_y), (img.width, bar_y + bar_height)],
        fill=(0, 0, 0, opacity),
    )

    # Composite the overlay
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Draw text centered
    text_x = (img.width - text_width) // 2
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    # Convert back to RGB for PNG output
    return img.convert("RGB")
