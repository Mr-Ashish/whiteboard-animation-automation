#!/usr/bin/env python3
"""
Diagonal zig-zag pencil drawing reveal animation
Creates a video where an image is revealed with a hand/pencil cursor moving in zig-zag pattern
from top-left to bottom-right at 45-degree angle

Supports both single image and multi-image array modes with automatic cleanup
"""

import sys
import json
from pathlib import Path
from src.config import PENCIL_SIZE, TEMP_DIR, calculate_dimensions, ASPECT_RATIOS, QUALITY_PRESETS
from src.cursor_utils import load_pencil_cursor, create_simple_pencil_cursor
from src.video_writer import create_reveal_video, create_multi_reveal_video
from src.download_utils import is_url, resolve_audio_path
from src.cleanup_utils import CleanupManager


def main():
    """Main entry point for the pencil reveal animation tool"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single image mode:")
        print("    python pencil_reveal.py <input_image> [OPTIONS]")
        print("    Example: python pencil_reveal.py image.png output.mp4")
        print("    Example: python pencil_reveal.py image.png hand_pencil.png output.mp4")
        print("    Example: python pencil_reveal.py https://example.com/image.jpg output.mp4")
        print()
        print("  Multi-image mode:")
        print("    python pencil_reveal.py --multi <config.json> [OPTIONS]")
        print("    Example: python pencil_reveal.py --multi config.json output.mp4")
        print()
        print("  Options:")
        print("    --audio <file>     Add background music (mp3, wav, etc.)")
        print("    --volume <0.0-1.0> Set audio volume (default: 1.0)")
        print("    --upload           Upload video to AWS S3 (requires .env config)")
        print("    --ratio <ratio>    Aspect ratio (default: 9:16)")
        print(f"                       Available: {', '.join(ASPECT_RATIOS.keys())}")
        print("    --quality <qual>   Video quality (default: 720p)")
        print(f"                       Available: {', '.join(QUALITY_PRESETS.keys())}")
        print()
        print("  Examples with audio:")
        print("    python pencil_reveal.py image.png --audio music.mp3 output.mp4")
        print("    python pencil_reveal.py --multi config.json --audio music.wav --volume 0.5 output.mp4")
        print()
        print("  Examples with aspect ratio and quality:")
        print("    python pencil_reveal.py image.png --ratio 16:9 --quality 1080p output.mp4")
        print("    python pencil_reveal.py --multi config.json --ratio 1:1 --quality 720p output.mp4")
        print()
        print("  Examples with AWS upload:")
        print("    python pencil_reveal.py image.png --upload output.mp4")
        print("    python pencil_reveal.py --multi config.json --audio music.mp3 --upload final.mp4")
        print()
        print("  Config JSON format for multi-image mode:")
        print('    [')
        print('      {"image": "path/to/image1.png", "seconds": 5},')
        print('      {"image": "https://example.com/image2.png", "seconds": 3}')
        print('    ]')
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
    args = sys.argv[1:]
    input_image_arg = args[0]

    # Parse arguments
    hand_pencil_path = None
    use_custom_cursor = False
    output_video = None  # Will be set to UUID if not provided
    audio_path = None
    audio_volume = 1.0
    upload_to_aws = False
    aspect_ratio = None
    quality = None

    i = 1
    while i < len(args):
        arg = args[i]

        if arg == '--upload':
            upload_to_aws = True
            i += 1

        elif arg == '--ratio':
            if i + 1 < len(args):
                aspect_ratio = args[i + 1]
                if aspect_ratio not in ASPECT_RATIOS:
                    print(f"Error: Invalid aspect ratio '{aspect_ratio}'")
                    print(f"Available: {', '.join(ASPECT_RATIOS.keys())}")
                    sys.exit(1)
                i += 2
            else:
                print("Error: --ratio requires a value")
                sys.exit(1)

        elif arg == '--quality':
            if i + 1 < len(args):
                quality = args[i + 1]
                if quality not in QUALITY_PRESETS:
                    print(f"Error: Invalid quality '{quality}'")
                    print(f"Available: {', '.join(QUALITY_PRESETS.keys())}")
                    sys.exit(1)
                i += 2
            else:
                print("Error: --quality requires a value")
                sys.exit(1)

        elif arg == '--audio':
            if i + 1 < len(args):
                audio_arg = args[i + 1]
                # Validate: check if URL or local file exists
                if not is_url(audio_arg):
                    audio_path = Path(audio_arg)
                    if not audio_path.exists():
                        print(f"Error: Audio file not found: {audio_arg}")
                        sys.exit(1)
                else:
                    # It's a URL, store as string
                    audio_path = audio_arg
                i += 2
            else:
                print("Error: --audio requires a file path or URL")
                sys.exit(1)

        elif arg == '--volume':
            if i + 1 < len(args):
                try:
                    audio_volume = float(args[i + 1])
                    if not 0.0 <= audio_volume <= 1.0:
                        print("Error: --volume must be between 0.0 and 1.0")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print("Error: --volume requires a number")
                    sys.exit(1)
            else:
                print("Error: --volume requires a value")
                sys.exit(1)

        elif Path(arg).suffix.lower() in ['.png', '.jpg', '.jpeg'] and not use_custom_cursor:
            # Hand pencil cursor
            hand_pencil_path = Path(arg)
            use_custom_cursor = True
            i += 1

        elif Path(arg).suffix.lower() in ['.mp4', '.avi']:
            # Output video
            output_video = arg
            i += 1

        else:
            i += 1

    # Validate input (URL or local path)
    if not is_url(input_image_arg):
        input_path = Path(input_image_arg)
        if not input_path.exists():
            print(f"Error: Input image not found: {input_image_arg}")
            sys.exit(1)

    # Generate UUID filename if not provided
    if output_video is None:
        from src.filename_utils import generate_timestamped_filename
        output_video = generate_timestamped_filename()
        print(f"Generated filename: {output_video}")

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        # Resolve audio path/URL if provided
        if audio_path:
            audio_path = resolve_audio_path(audio_path, cleanup)

        video_path, s3_url = create_reveal_video(
            input_image_arg, output_video, pencil_cursor, cursor_size,
            cleanup_manager=cleanup,
            audio_path=audio_path,
            audio_volume=audio_volume,
            upload_to_aws=upload_to_aws,
            aspect_ratio=aspect_ratio,
            quality=quality
        )

    print("\n✓ Cleanup complete - all temporary files removed")

    # Display results
    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: {s3_url}")
        print(f"{'='*60}")
    else:
        print(f"\n✓ Success! Video saved locally: {video_path}")


def _handle_multi_image_mode():
    """Handle multi-image mode processing with cleanup"""
    if len(sys.argv) < 3:
        print("Error: Config JSON file required for multi-image mode")
        sys.exit(1)

    config_path = Path(sys.argv[2])

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    # Load config
    try:
        with open(config_path, 'r') as f:
            image_configs = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)

    if not isinstance(image_configs, list):
        print("Error: Config JSON must be an array of objects")
        sys.exit(1)

    # Validate image paths and URLs
    for idx, config in enumerate(image_configs):
        if 'image' not in config:
            print(f"Error: Missing 'image' key in config at index {idx}")
            sys.exit(1)

        image_arg = config['image']
        # Only validate local paths, URLs will be validated during download
        if not is_url(image_arg):
            image_path = Path(image_arg)
            if not image_path.exists():
                print(f"Error: Image not found: {image_arg}")
                sys.exit(1)

    # Parse optional arguments
    args = sys.argv[3:]
    hand_pencil_path = None
    use_custom_cursor = False
    output_video = None  # Will be set to UUID if not provided
    audio_path = None
    audio_volume = 1.0
    upload_to_aws = False
    aspect_ratio = None
    quality = None

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == '--upload':
            upload_to_aws = True
            i += 1

        elif arg == '--ratio':
            if i + 1 < len(args):
                aspect_ratio = args[i + 1]
                if aspect_ratio not in ASPECT_RATIOS:
                    print(f"Error: Invalid aspect ratio '{aspect_ratio}'")
                    print(f"Available: {', '.join(ASPECT_RATIOS.keys())}")
                    sys.exit(1)
                i += 2
            else:
                print("Error: --ratio requires a value")
                sys.exit(1)

        elif arg == '--quality':
            if i + 1 < len(args):
                quality = args[i + 1]
                if quality not in QUALITY_PRESETS:
                    print(f"Error: Invalid quality '{quality}'")
                    print(f"Available: {', '.join(QUALITY_PRESETS.keys())}")
                    sys.exit(1)
                i += 2
            else:
                print("Error: --quality requires a value")
                sys.exit(1)

        elif arg == '--audio':
            if i + 1 < len(args):
                audio_arg = args[i + 1]
                # Validate: check if URL or local file exists
                if not is_url(audio_arg):
                    audio_path = Path(audio_arg)
                    if not audio_path.exists():
                        print(f"Error: Audio file not found: {audio_arg}")
                        sys.exit(1)
                else:
                    # It's a URL, store as string
                    audio_path = audio_arg
                i += 2
            else:
                print("Error: --audio requires a file path or URL")
                sys.exit(1)

        elif arg == '--volume':
            if i + 1 < len(args):
                try:
                    audio_volume = float(args[i + 1])
                    if not 0.0 <= audio_volume <= 1.0:
                        print("Error: --volume must be between 0.0 and 1.0")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print("Error: --volume requires a number")
                    sys.exit(1)
            else:
                print("Error: --volume requires a value")
                sys.exit(1)

        elif Path(arg).suffix.lower() in ['.png', '.jpg', '.jpeg'] and not use_custom_cursor:
            # Hand pencil cursor
            hand_pencil_path = Path(arg)
            use_custom_cursor = True
            i += 1

        elif Path(arg).suffix.lower() in ['.mp4', '.avi']:
            # Output video
            output_video = arg
            i += 1

        else:
            i += 1

    # Generate UUID filename if not provided
    if output_video is None:
        from src.filename_utils import generate_timestamped_filename
        output_video = generate_timestamped_filename()
        print(f"Generated filename: {output_video}")

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

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
            quality=quality
        )

    print("\n✓ Cleanup complete - all temporary files removed")

    # Display results
    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: {s3_url}")
        print(f"{'='*60}")
    else:
        print(f"\n✓ Success! Video saved locally: {video_path}")


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
