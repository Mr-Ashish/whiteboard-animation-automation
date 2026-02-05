#!/usr/bin/env python3
"""
Diagonal zig-zag pencil drawing reveal animation
Creates a video where an image is revealed with a hand/pencil cursor moving in zig-zag pattern
from top-left to bottom-right at 45-degree angle

Supports both single image and multi-image array modes with automatic cleanup
"""

import sys
from pathlib import Path
# Relative imports for package structure (CLI in src/cli/, modules in src/)
from ..config.config import PENCIL_SIZE, TEMP_DIR, calculate_dimensions, ASPECT_RATIOS, QUALITY_PRESETS
from ..cursor.cursor_utils import load_pencil_cursor, create_simple_pencil_cursor
from ..video.video_writer import create_reveal_video, create_multi_reveal_video
# Relative import for grouped structure (download now in subdir)
from ..download.download_utils import is_url, resolve_audio_path
from ..cleanup.cleanup_utils import CleanupManager
from ..utils.error_handler import handle_error
from ..utils.config_utils import load_and_validate_image_configs
from ..utils.cli_utils import parse_common_options
# Colored logging for differentiation (success green, etc.)
from ..utils.log_utils import log_success, log_info


def main():
    """Main entry point for the pencil reveal animation tool"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single image mode:")
        print("    python -m src.cli.pencil_reveal <input_image> [OPTIONS]")
        print("    Example: python -m src.cli.pencil_reveal image.png output.mp4")
        print("    Example: python -m src.cli.pencil_reveal image.png hand_pencil.png output.mp4")
        print("    Example: python -m src.cli.pencil_reveal https://example.com/image.jpg output.mp4")
        print()
        print("  Multi-image mode:")
        print("    python -m src.cli.pencil_reveal --multi <config.json> [OPTIONS]")
        print("    Example: python -m src.cli.pencil_reveal --multi config.json output.mp4")
        print()
        print("  Options (single and multi):")
        print("    --audio <file>     Add background music (mp3, wav, etc.)")
        print("    --captions <file>  Add timed captions from JSON (word/letter timing)")
        print("    --volume <0.0-1.0> Set audio volume (default: 1.0)")
        print("    --upload           Upload video to AWS S3 (requires .env config)")
        print("    --captions <file>   Add timed captions from JSON (word/letter timing)")
        print("    --ratio <ratio>    Aspect ratio (default: 9:16)")
        print(f"                       Available: {', '.join(ASPECT_RATIOS.keys())}")
        print("    --quality <qual>   Video quality (default: 720p)")
        print(f"                       Available: {', '.join(QUALITY_PRESETS.keys())}")
        print()
        print("  Examples with audio:")
        print("    python -m src.cli.pencil_reveal image.png --audio music.mp3 output.mp4")
        print("    python -m src.cli.pencil_reveal --multi config.json --audio music.wav --volume 0.5 output.mp4")
        print()
        print("  Examples with aspect ratio and quality:")
        print("    python -m src.cli.pencil_reveal image.png --ratio 16:9 --quality 1080p output.mp4")
        print("    python -m src.cli.pencil_reveal --multi config.json --ratio 1:1 --quality 720p output.mp4")
        print()
        print("  Examples with AWS upload:")
        print("    python -m src.cli.pencil_reveal image.png --upload output.mp4")
        print("    python -m src.cli.pencil_reveal --multi config.json --audio music.mp3 --upload final.mp4")
        print()
        print("  Config JSON format for multi-image mode:")
        print('    [')
        print('      {"image": "path/to/image1.png", "seconds": 5},')
        print('      {"image": "https://example.com/image2.png", "seconds": 3}')
        print('    ]')
        print()
        print("  Captions JSON format (for --captions):")
        print('    [{"text": "word", "start": 0.0, "end": 0.5}, ...]')
        print()
        print("  Note: Both local file paths and image URLs are supported")
        print("  Output videos are saved to output/ directory")
        sys.exit(1)

    # Check for multi-image mode
    if sys.argv[1] == '--multi':
        _handle_multi_image_mode()
    else:
        _handle_single_image_mode()


def _handle_single_image_mode():
    """Handle single image mode processing with cleanup"""
    # Use modular common parser for options (removes if-else chain duplication)
    # Positionals: <input_image> [hand_pencil_cursor] [output.mp4]
    raw_args = sys.argv[1:]
    if not raw_args:
        handle_error("Input image required for single mode")
    input_image_arg = raw_args[0]

    # Parse common options (flags anywhere after input)
    # parse_common_options handles validations for audio/volume/captions/ratio/etc
    common_opts = parse_common_options(raw_args[1:], support_type=True, support_cursor=True)
    audio_path = common_opts["audio_path"]
    audio_volume = common_opts["audio_volume"]
    upload_to_aws = common_opts["upload_to_aws"]
    aspect_ratio = common_opts["aspect_ratio"]
    quality = common_opts["quality"]
    captions_path = common_opts["captions_path"]
    image_type = common_opts["image_type"]

    # Manual scan remaining args for mode-specific positionals (cursor/output; short, no chain)
    # (common parser's parse_known_args ignores these)
    hand_pencil_path = None
    use_custom_cursor = False
    output_video = None
    for arg in raw_args[1:]:
        if not arg.startswith("--") and Path(arg).suffix.lower() in ['.png', '.jpg', '.jpeg'] and not use_custom_cursor:
            # Hand pencil cursor (optional)
            hand_pencil_path = Path(arg)
            use_custom_cursor = True
        elif not arg.startswith("--") and Path(arg).suffix.lower() in ['.mp4', '.avi']:
            # Output video (optional)
            output_video = arg

    # Validate input (URL or local path)
    if not is_url(input_image_arg):
        input_path = Path(input_image_arg)
        if not input_path.exists():
            handle_error(f"Input image not found: {input_image_arg}")

    # Generate UUID filename if not provided
    if output_video is None:
        # Relative import for grouped structure (filename now in subdir)
        from ..filename.filename_utils import generate_timestamped_filename
        output_video = generate_timestamped_filename()
        log_info(f"Generated filename: {output_video}")

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

    # Load captions if requested (plus highlight options if in JSON)
    captions = None
    caption_options = {}
    if captions_path:
        # Relative import for grouped structure (captions now in subdir)
        from ..captions.caption_overlay import load_captions_from_json, extract_highlight_options
        captions = load_captions_from_json(str(captions_path))
        caption_options = extract_highlight_options(str(captions_path))
        log_info(f"Loaded {len(captions)} caption segments from {captions_path}")

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        # Resolve audio path/URL if provided
        if audio_path:
            audio_path = resolve_audio_path(audio_path, cleanup)

        # Handle based on image type
        if image_type == 'cover':
            # Create static 1-second video for cover image
            # Relative import for grouped structure (video now in subdir)
            from ..video.video_writer import create_static_cover_video
            video_path, s3_url = create_static_cover_video(
                input_image_arg, output_video,
                cleanup_manager=cleanup,
                audio_path=audio_path,
                audio_volume=audio_volume,
                upload_to_aws=upload_to_aws,
                aspect_ratio=aspect_ratio,
                quality=quality,
                duration_seconds=1.0,
                captions=captions,
                caption_options=caption_options,
            )

        else:
            # Normal reveal animation for scene type
            video_path, s3_url = create_reveal_video(
                input_image_arg, output_video, pencil_cursor, cursor_size,
                cleanup_manager=cleanup,
                audio_path=audio_path,
                audio_volume=audio_volume,
                upload_to_aws=upload_to_aws,
                aspect_ratio=aspect_ratio,
                quality=quality,
                captions=captions,
                caption_options=caption_options,
            )

    log_info("\n✓ Cleanup complete - all temporary files removed")

    # Display results
    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: <s3url>{s3_url}</s3url>")
        print(f"{'='*60}")
    else:
        log_success(f"\n✓ Success! Video saved locally: {video_path}")


def _handle_multi_image_mode():
    """Handle multi-image mode processing with cleanup"""
    if len(sys.argv) < 3:
        handle_error("Config JSON file required for multi-image mode")

    # Use shared config loader from utils (requires 'image' key + type validation)
    image_configs = load_and_validate_image_configs(
        sys.argv[2], require_image_key=True, validate_types=True
    )

    # Parse optional arguments using modular common parser (removes if-else chain)
    # Supports cursor/output as in single mode for multi compat
    raw_args = sys.argv[3:]
    common_opts = parse_common_options(raw_args, support_type=False, support_cursor=True)
    audio_path = common_opts["audio_path"]
    audio_volume = common_opts["audio_volume"]
    upload_to_aws = common_opts["upload_to_aws"]
    aspect_ratio = common_opts["aspect_ratio"]
    quality = common_opts["quality"]
    captions_path = common_opts["captions_path"]

    # Manual scan for mode-specific positionals (cursor/output; short, no options chain)
    hand_pencil_path = None
    use_custom_cursor = False
    output_video = None
    for arg in raw_args:
        if not arg.startswith("--") and Path(arg).suffix.lower() in ['.png', '.jpg', '.jpeg'] and not use_custom_cursor:
            # Hand pencil cursor (optional in multi too)
            hand_pencil_path = Path(arg)
            use_custom_cursor = True
        elif not arg.startswith("--") and Path(arg).suffix.lower() in ['.mp4', '.avi']:
            # Output video (optional)
            output_video = arg

    # Generate UUID filename if not provided
    if output_video is None:
        # Relative import for grouped structure (filename now in subdir)
        from ..filename.filename_utils import generate_timestamped_filename
        output_video = generate_timestamped_filename()
        log_info(f"Generated filename: {output_video}")

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

    # Load captions if requested (plus highlight options if in JSON)
    captions = None
    caption_options = {}
    if captions_path:
        # Relative import for grouped structure (captions now in subdir)
        from ..captions.caption_overlay import load_captions_from_json, extract_highlight_options
        captions = load_captions_from_json(str(captions_path))
        caption_options = extract_highlight_options(str(captions_path))
        log_info(f"Loaded {len(captions)} caption segments from {captions_path}")

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        # Resolve audio path/URL if provided
        if audio_path:
            audio_path = resolve_audio_path(audio_path, cleanup)

        video_path, s3_url = create_multi_reveal_video(
            image_configs, output_video, pencil_cursor, cursor_size,
            cleanup_manager=cleanup,
            audio_path=audio_path,
            audio_volume=audio_volume,
            upload_to_aws=upload_to_aws,
            aspect_ratio=aspect_ratio,
            quality=quality,
            captions=captions,
            caption_options=caption_options,
        )

    log_info("\n✓ Cleanup complete - all temporary files removed")

    # Display results
    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: <s3url>{s3_url}</s3url>")
        print(f"{'='*60}")
    else:
        log_success(f"\n✓ Success! Video saved locally: {video_path}")


def _load_cursor(hand_pencil_path, use_custom_cursor):
    """Load or create pencil cursor

    Args:
        hand_pencil_path: Path to custom cursor image (or None)
        use_custom_cursor: Whether to use custom cursor

    Returns:
        tuple: (pencil_cursor, cursor_size)
    """
    if use_custom_cursor and hand_pencil_path and hand_pencil_path.exists():
        print(f"Loading custom pencil cursor: {hand_pencil_path}")
        pencil_cursor = load_pencil_cursor(hand_pencil_path, PENCIL_SIZE)
        cursor_size = PENCIL_SIZE
    else:
        print("Creating default pencil cursor...")
        pencil_cursor = create_simple_pencil_cursor(PENCIL_SIZE)
        cursor_size = PENCIL_SIZE

    return pencil_cursor, cursor_size


if __name__ == "__main__":
    main()
