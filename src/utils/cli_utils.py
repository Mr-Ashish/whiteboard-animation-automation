import argparse
from pathlib import Path

from .error_handler import handle_error
# Relative import for grouped structure (download now in subdir)
from ..download.download_utils import is_url
from ..config.config import ASPECT_RATIOS, QUALITY_PRESETS


def parse_common_options(args_list, support_type=False, support_cursor=False):
    """Parse common CLI options (audio, ratio, etc.) using argparse.
    Modular helper to eliminate if-else chains; shared across modes/scripts.
    """
    parser = argparse.ArgumentParser(add_help=False)  # Sub-parser style, no help
    parser.add_argument("--audio", help="Background music file or URL")
    parser.add_argument("--volume", type=float, default=1.0, help="Audio volume (0.0-1.0)")
    parser.add_argument("--upload", action="store_true", help="Upload to AWS S3")
    parser.add_argument("--captions", help="Timed captions JSON file")
    parser.add_argument(
        "--ratio",
        choices=list(ASPECT_RATIOS.keys()),
        help="Aspect ratio",
    )
    parser.add_argument(
        "--quality",
        choices=list(QUALITY_PRESETS.keys()),
        help="Video quality",
    )
    if support_type:
        parser.add_argument("--type", choices=["scene", "cover"], default="scene", help="Image type")
    if support_cursor:
        # Cursor handled separately in logic
        pass

    # Parse known args, ignore unknowns for flexibility
    parsed, _ = parser.parse_known_args(args_list)

    # Post-parse validations (volume, paths)
    if not 0.0 <= parsed.volume <= 1.0:
        handle_error("--volume must be between 0.0 and 1.0")

    captions_path = None
    if parsed.captions:
        captions_path = Path(parsed.captions)
        if not captions_path.exists():
            handle_error(f"Captions file not found: {captions_path}")

    audio_path = None
    if parsed.audio:
        audio_arg = parsed.audio
        if not is_url(audio_arg):
            audio_p = Path(audio_arg)
            if not audio_p.exists():
                handle_error(f"Audio file not found: {audio_arg}")
            audio_path = audio_p
        else:
            audio_path = audio_arg

    return {
        "audio_path": audio_path,
        "audio_volume": parsed.volume,
        "upload_to_aws": parsed.upload,
        "aspect_ratio": parsed.ratio,
        "quality": parsed.quality,
        "captions_path": captions_path,
        "image_type": getattr(parsed, "type", "scene") if support_type else None,
    }
