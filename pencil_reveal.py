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
from src.config import PENCIL_SIZE, TEMP_DIR
from src.cursor_utils import load_pencil_cursor, create_simple_pencil_cursor
from src.video_writer import create_reveal_video, create_multi_reveal_video
from src.download_utils import is_url
from src.cleanup_utils import CleanupManager


def main():
    """Main entry point for the pencil reveal animation tool"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single image mode:")
        print("    python pencil_reveal.py <input_image> [hand_pencil_image] [output_video.mp4]")
        print("    Example: python pencil_reveal.py image.png hand_pencil.png output.mp4")
        print("    Example: python pencil_reveal.py https://example.com/image.jpg output.mp4")
        print()
        print("  Multi-image mode:")
        print("    python pencil_reveal.py --multi <config.json> [hand_pencil_image] [output_video.mp4]")
        print("    Example: python pencil_reveal.py --multi config.json hand_pencil.png output.mp4")
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
    input_image_arg = sys.argv[1]

    # Determine arguments
    if len(sys.argv) >= 3 and Path(sys.argv[2]).suffix.lower() in ['.png', '.jpg', '.jpeg']:
        # Hand pencil image provided
        hand_pencil_path = Path(sys.argv[2])
        output_video = sys.argv[3] if len(sys.argv) > 3 else "pencil_reveal.mp4"
        use_custom_cursor = True
    else:
        # No hand pencil image
        hand_pencil_path = None
        output_video = sys.argv[2] if len(sys.argv) > 2 else "pencil_reveal.mp4"
        use_custom_cursor = False

    # Validate input (URL or local path)
    if not is_url(input_image_arg):
        input_path = Path(input_image_arg)
        if not input_path.exists():
            print(f"Error: Input image not found: {input_image_arg}")
            sys.exit(1)

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        create_reveal_video(input_image_arg, output_video, pencil_cursor, cursor_size,
                          cleanup_manager=cleanup)
    print("\n✓ Cleanup complete - all temporary files removed")


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

    # Determine cursor and output arguments
    if len(sys.argv) >= 4 and Path(sys.argv[3]).suffix.lower() in ['.png', '.jpg', '.jpeg']:
        # Hand pencil image provided
        hand_pencil_path = Path(sys.argv[3])
        output_video = sys.argv[4] if len(sys.argv) > 4 else "multi_reveal.mp4"
        use_custom_cursor = True
    else:
        # No hand pencil image
        hand_pencil_path = None
        output_video = sys.argv[3] if len(sys.argv) > 3 else "multi_reveal.mp4"
        use_custom_cursor = False

    # Load or create pencil cursor
    pencil_cursor, cursor_size = _load_cursor(hand_pencil_path, use_custom_cursor)

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        create_multi_reveal_video(image_configs, output_video, pencil_cursor, cursor_size,
                                cleanup_manager=cleanup)
    print("\n✓ Cleanup complete - all temporary files removed")


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
