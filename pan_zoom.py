#!/usr/bin/env python3
"""
Pan and zoom video animation
Creates videos where images are zoomed in and pan vertically with alternating directions
"""

import sys
import json
from pathlib import Path
from src.config import ASPECT_RATIOS, QUALITY_PRESETS, TEMP_DIR
from src.video_writer import create_pan_zoom_video
from src.download_utils import is_url, resolve_audio_path
from src.cleanup_utils import CleanupManager


def main():
    """Main entry point for the pan-zoom animation tool"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pan_zoom.py <config.json> [OPTIONS] [output.mp4]")
        print()
        print("  Options:")
        print("    --audio <file>     Add background music (mp3, wav, etc.)")
        print("    --volume <0.0-1.0> Set audio volume (default: 1.0)")
        print("    --upload           Upload video to AWS S3 (requires .env config)")
        print("    --captions <file>  Add timed captions from JSON (word/letter timing)")
        print("    --ratio <ratio>    Aspect ratio (default: 9:16)")
        print(f"                       Available: {', '.join(ASPECT_RATIOS.keys())}")
        print("    --quality <qual>   Video quality (default: 720p)")
        print(f"                       Available: {', '.join(QUALITY_PRESETS.keys())}")
        print()
        print("  Examples:")
        print("    python pan_zoom.py images_config.json output.mp4")
        print("    python pan_zoom.py images_config.json --audio music.mp3 output.mp4")
        print("    python pan_zoom.py images_config.json --ratio 16:9 --quality 1080p output.mp4")
        print("    python pan_zoom.py images_config.json --upload output.mp4")
        print()
        print("  Config JSON format:")
        print('    [')
        print('      {"image": "path/to/image1.png", "seconds": 5},')
        print('      {"image": "https://example.com/image2.png", "seconds": 4}')
        print('    ]')
        print()
        print("  Captions JSON format (for --captions):")
        print('    [{"text": "word", "start": 0.0, "end": 0.5}, ...]')
        print()
        print("  Note: Both local file paths and image URLs are supported")
        print("  Output videos are saved to output/ directory")
        sys.exit(1)

    # Parse arguments
    config_path = Path(sys.argv[1])

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

    # Validate image configs
    for idx, config in enumerate(image_configs):
        if 'image' not in config and 'url' not in config:
            print(f"Error: Missing 'image' or 'url' key in config at index {idx}")
            sys.exit(1)

        image_arg = config.get('image') or config.get('url')
        # Only validate local paths, URLs will be validated during download
        if not is_url(image_arg):
            image_path = Path(image_arg)
            if not image_path.exists():
                print(f"Error: Image not found: {image_arg}")
                sys.exit(1)

    # Parse optional arguments
    args = sys.argv[2:]
    output_video = None
    audio_path = None
    audio_volume = 1.0
    upload_to_aws = False
    aspect_ratio = None
    quality = None
    captions_path = None

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == '--captions':
            if i + 1 < len(args):
                captions_path = Path(args[i + 1])
                if not captions_path.exists():
                    print(f"Error: Captions file not found: {captions_path}")
                    sys.exit(1)
                i += 2
            else:
                print("Error: --captions requires a JSON file path")
                sys.exit(1)

        elif arg == '--upload':
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

    # Load captions if requested
    captions = None
    if captions_path:
        from src.caption_overlay import load_captions_from_json
        captions = load_captions_from_json(str(captions_path))
        print(f"Loaded {len(captions)} caption segments from {captions_path}")

    # Generate video with cleanup
    with CleanupManager(TEMP_DIR) as cleanup:
        # Resolve audio path/URL if provided
        if audio_path:
            audio_path = resolve_audio_path(audio_path, cleanup)

        video_path, s3_url = create_pan_zoom_video(
            image_configs, output_video,
            cleanup_manager=cleanup,
            audio_path=audio_path,
            audio_volume=audio_volume,
            upload_to_aws=upload_to_aws,
            aspect_ratio=aspect_ratio,
            quality=quality,
            captions=captions,
        )

    print("\n✓ Cleanup complete - all temporary files removed")

    # Display results
    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: <s3url>{s3_url}</s3url>")
        print(f"{'='*60}")
    else:
        print(f"\n✓ Success! Video saved locally: {video_path}")


if __name__ == "__main__":
    main()
