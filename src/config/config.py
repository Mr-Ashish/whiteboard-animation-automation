"""Configuration constants for the pencil reveal animation"""

from pathlib import Path

# Project root directory (robust for subdir structure like config/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Folder paths
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

# Aspect ratio presets (width:height)
ASPECT_RATIOS = {
    '16:9': (16, 9),    # Landscape (YouTube, TV)
    '9:16': (9, 16),    # Vertical/Portrait (Instagram Stories, TikTok)
    '1:1': (1, 1),      # Square (Instagram Post)
    '4:5': (4, 5),      # Portrait (Instagram Feed)
    '4:3': (4, 3),      # Classic (Old TV)
}

# Quality presets (height in pixels)
QUALITY_PRESETS = {
    '480p': 480,
    '720p': 720,
    '1080p': 1080,
    '1440p': 1440,
    '2160p': 2160,  # 4K
}

# Default settings
DEFAULT_ASPECT_RATIO = '9:16'
DEFAULT_QUALITY = '720p'

def calculate_dimensions(aspect_ratio=None, quality=None):
    """Calculate WIDTH and HEIGHT from aspect ratio and quality preset

    Args:
        aspect_ratio: String like '16:9' or '9:16' (None uses default)
        quality: String like '720p' or '1080p' (None uses default)

    Returns:
        tuple: (width, height)
    """
    # Use defaults if None
    if aspect_ratio is None:
        aspect_ratio = DEFAULT_ASPECT_RATIO
    if quality is None:
        quality = DEFAULT_QUALITY

    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect ratio '{aspect_ratio}'. Must be one of {list(ASPECT_RATIOS.keys())}")

    if quality not in QUALITY_PRESETS:
        raise ValueError(f"Invalid quality '{quality}'. Must be one of {list(QUALITY_PRESETS.keys())}")

    ratio_w, ratio_h = ASPECT_RATIOS[aspect_ratio]
    target_height = QUALITY_PRESETS[quality]

    # Calculate width based on aspect ratio and target height
    width = int((ratio_w / ratio_h) * target_height)
    height = target_height

    return width, height

# Video dimensions (default)
WIDTH, HEIGHT = calculate_dimensions()
FPS = 30

# Animation settings
DEFAULT_REVEAL_DURATION = 3.0  # seconds for the reveal animation
DEFAULT_TOTAL_DURATION = 6.0   # total video duration (reveal + hold at end)
ZIG_ZAG_AMPLITUDE = 350  # how far perpendicular to the diagonal path (pixels)
DIAGONAL_ANGLE = 45  # degrees from horizontal (top-left to bottom-right)

# Cursor settings
PENCIL_SIZE = 350  # default size of the pencil cursor (for 720p vertical)
CURSOR_FADE_IN_FRAMES = 20
CURSOR_FADE_OUT_FRAMES = 20

def calculate_cursor_size(width, height):
    """Calculate appropriate cursor size based on video dimensions

    Args:
        width: Video width in pixels
        height: Video height in pixels

    Returns:
        int: Cursor size in pixels
    """
    # Base cursor size is 350 for 405x720 (9:16 @ 720p)
    # Scale proportionally based on the shorter dimension
    base_dimension = 405  # width of 9:16 @ 720p
    base_cursor_size = 350

    shorter_dimension = min(width, height)
    cursor_size = int((shorter_dimension / base_dimension) * base_cursor_size)

    # Reduce by 1/4 (multiply by 0.75 or 3/4)
    cursor_size = int(cursor_size * 0.25)

    # Ensure minimum and maximum bounds
    cursor_size = max(100, min(cursor_size, 800))

    return cursor_size

# Pan-zoom animation settings
DEFAULT_ZOOM_LEVEL = 1.1  # 10% zoom in (1.0 = no zoom, 1.1 = 10% larger)
DEFAULT_PAN_DISTANCE_RATIO = 0.15  # 15% of image height as pan distance
