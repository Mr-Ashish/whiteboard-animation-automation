"""Configuration constants for the pencil reveal animation"""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Folder paths
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

# Video dimensions
WIDTH = 1080
HEIGHT = 1920
FPS = 60

# Animation settings
DEFAULT_REVEAL_DURATION = 3.0  # seconds for the reveal animation
DEFAULT_TOTAL_DURATION = 6.0   # total video duration (reveal + hold at end)
ZIG_ZAG_AMPLITUDE = 350  # how far perpendicular to the diagonal path (pixels)
DIAGONAL_ANGLE = 45  # degrees from horizontal (top-left to bottom-right)

# Cursor settings
PENCIL_SIZE = 350  # size of the pencil cursor if no image provided
CURSOR_FADE_IN_FRAMES = 20
CURSOR_FADE_OUT_FRAMES = 20
