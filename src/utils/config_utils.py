import json
from pathlib import Path

from .error_handler import handle_error
# Relative import for grouped structure (download now in subdir)
from ..download.download_utils import is_url


def validate_image_configs(image_configs, require_image_key=True, validate_types=False):
    """Validate image configs list (common; supports optional 'direction', 'avatar_video' for pan_zoom)."""
    if not isinstance(image_configs, list):
        handle_error("Config JSON must be an array of objects")

    for idx, config in enumerate(image_configs):
        if require_image_key:
            if "image" not in config:
                handle_error(f"Missing 'image' key in config at index {idx}")
        else:
            if "image" not in config and "url" not in config:
                handle_error(f"Missing 'image' or 'url' key in config at index {idx}")

        image_arg = config.get("image") or config.get("url")
        # Only validate local paths, URLs will be validated during download
        if not is_url(image_arg):
            image_path = Path(image_arg)
            if not image_path.exists():
                handle_error(f"Image not found: {image_arg}")

        if validate_types:
            image_type = config.get("type", "scene")
            if image_type not in ["scene", "cover"]:
                handle_error(f"Invalid type '{image_type}' at index {idx}. Must be 'scene' or 'cover'")

        # Optional per-image pan direction (for pan_zoom; ignored elsewhere; defaults to config root)
        dir_val = config.get("direction")
        if dir_val and dir_val not in ["up", "down", "left", "right"]:
            handle_error(f"Invalid 'direction' '{dir_val}' at index {idx}. Must be up/down/left/right or omit for default.")

        # Optional avatar_video (URL for green-screen character video; validated on resolve)
        avatar_val = config.get("avatar_video")
        if avatar_val and not (is_url(avatar_val) or Path(avatar_val).exists()):
            handle_error(f"Invalid 'avatar_video' at index {idx}: must be URL or existing file")


def load_and_validate_image_configs(config_path_str, require_image_key=True, validate_types=False):
    """Load from JSON then validate (uses shared validate)."""
    config_path = Path(config_path_str)
    if not config_path.exists():
        handle_error(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            image_configs = json.load(f)
    except json.JSONDecodeError as e:
        handle_error(f"Invalid JSON in config file: {e}")

    validate_image_configs(image_configs, require_image_key, validate_types)
    return image_configs
