"""Preview generation via Pillow compositing."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from ascii_tee.models import Design, Color

# Paths
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
CACHE_DIR = Path.home() / ".ascii-tee" / "cache"

# ASCII art rendering settings (base size)
BASE_FONT_SIZE = 14
BASE_LINE_HEIGHT = 16

# System font paths
SYSTEM_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  # Linux
    "C:\\Windows\\Fonts\\consola.ttf",  # Windows
]


def get_font(size: int = BASE_FONT_SIZE) -> ImageFont.FreeTypeFont:
    """Load the monospace font for ASCII rendering at specified size."""
    bundled_font = ASSETS_DIR / "JetBrainsMono-Regular.ttf"
    if bundled_font.exists():
        return ImageFont.truetype(str(bundled_font), size)

    for font_path in SYSTEM_FONTS:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def get_char_width(font: ImageFont.FreeTypeFont) -> float:
    """Get the actual character width for a monospace font."""
    bbox = font.getbbox("MMMMMMMMMM")
    return (bbox[2] - bbox[0]) / 10


def render_ascii_to_image(ascii_art: str, color: Color, scale: float = 1.0) -> Image.Image:
    """Render ASCII art to a transparent PNG.

    This is the SINGLE source of truth for ASCII rendering.
    Both preview and print use this function - just at different scales.

    Args:
        ascii_art: The ASCII art text
        color: Shirt color (determines text color - inverse)
        scale: Scale factor (1.0 = base size for preview, higher for print)

    Returns:
        PIL Image with transparent background
    """
    lines = ascii_art.split("\n")

    # Scale font and line height
    font_size = int(BASE_FONT_SIZE * scale)
    line_height = int(BASE_LINE_HEIGHT * scale)
    padding = int(20 * scale)

    font = get_font(font_size)
    char_width = get_char_width(font)

    # Calculate dimensions
    max_line_width = max(len(line) for line in lines) if lines else 0
    img_width = int(max_line_width * char_width) + padding * 2
    img_height = len(lines) * line_height + padding * 2

    # Create transparent image
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Text color is inverse of shirt color
    text_color = (255, 255, 255, 255) if color == "black" else (0, 0, 0, 255)

    # Draw each line (identical logic regardless of scale)
    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill=text_color)
        y += line_height

    return img


def get_mockup_path(color: Color) -> Path:
    """Get path to mockup template for given color."""
    # Try different naming conventions and formats
    for name in [f"{color}.jpg", f"{color}.png", f"mockup_{color}.png", f"mockup_{color}.jpg"]:
        path = ASSETS_DIR / name
        if path.exists():
            return path
    return ASSETS_DIR / f"{color}.jpg"  # Default


def generate_preview(design: Design, color: Color) -> Path:
    """Generate a t-shirt preview by compositing ASCII onto mockup.

    Args:
        design: The design with ASCII art
        color: Shirt color

    Returns:
        Path to the generated preview image
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{design.id}_{color}.png"

    # Return cached if exists
    if cache_path.exists():
        return cache_path

    # Load mockup template
    mockup_path = get_mockup_path(color)
    if not mockup_path.exists():
        raise FileNotFoundError(
            f"Mockup template not found: {mockup_path}\n"
            f"Please add {color}.jpg or {color}.png to the assets/ directory."
        )

    mockup = Image.open(mockup_path).convert("RGBA")

    # Render ASCII art
    ascii_img = render_ascii_to_image(design.ascii_art, color)

    # Scale ASCII image to fit on chest area (about 18% of mockup width)
    target_width = int(mockup.width * 0.18)
    scale = target_width / ascii_img.width if ascii_img.width > 0 else 1
    new_size = (int(ascii_img.width * scale), int(ascii_img.height * scale))
    ascii_img = ascii_img.resize(new_size, Image.Resampling.LANCZOS)

    # Calculate position (centered on chest - roughly 45% down from top)
    x = (mockup.width - ascii_img.width) // 2
    y = int(mockup.height * 0.45) - (ascii_img.height // 2)

    # Composite
    mockup.paste(ascii_img, (x, y), ascii_img)

    # Save
    mockup.save(cache_path, "PNG")
    return cache_path


def generate_print_file(design: Design, color: Color) -> Path:
    """Generate a high-resolution print file for Printful.

    Uses the EXACT same rendering as preview, just scaled up.
    This guarantees identical proportions.

    Args:
        design: The design with ASCII art
        color: Shirt color (determines text color - inverse)

    Returns:
        Path to the generated print PNG
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{design.id}_{color}_print.png"

    if cache_path.exists():
        return cache_path

    # Printful canvas: 3600x4800 pixels (12"x16" at 300 DPI)
    PRINT_WIDTH = 3600
    PRINT_HEIGHT = 4800

    # First, render at base scale to measure dimensions
    base_img = render_ascii_to_image(design.ascii_art, color, scale=1.0)

    # Calculate scale to fill ~85% of print width
    target_width = int(PRINT_WIDTH * 0.85)
    scale = target_width / base_img.width

    # Render at high resolution using THE SAME function
    ascii_img = render_ascii_to_image(design.ascii_art, color, scale=scale)

    # Create Printful canvas and center the art
    canvas = Image.new("RGBA", (PRINT_WIDTH, PRINT_HEIGHT), (0, 0, 0, 0))
    x = (PRINT_WIDTH - ascii_img.width) // 2
    y = (PRINT_HEIGHT - ascii_img.height) // 2
    canvas.paste(ascii_img, (x, y), ascii_img)

    canvas.save(cache_path, "PNG")
    return cache_path


def clear_cache() -> int:
    """Clear all cached previews.

    Returns:
        Number of files deleted
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for file in CACHE_DIR.glob("*.png"):
        file.unlink()
        count += 1

    return count
