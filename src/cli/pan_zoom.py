#!/usr/bin/env python3
"""
Pan and zoom video animation
Creates videos where images are zoomed in and pan vertically with alternating directions
"""

import argparse
from pathlib import Path
# Relative imports for package structure (CLI in src/cli/, modules in src/)
from ..config.config import ASPECT_RATIOS, QUALITY_PRESETS, TEMP_DIR
# Relative import for grouped structure (download now in subdir)
from ..download.download_utils import is_url, resolve_audio_path
from ..cleanup.cleanup_utils import CleanupManager
from ..utils.error_handler import handle_error
from ..utils.config_utils import load_and_validate_image_configs
# Colored logging for differentiation (success green, etc.)
from ..utils.log_utils import log_success, log_info


def main():
    """Main entry point for the pan-zoom animation tool"""
    parser = argparse.ArgumentParser(
        description="Pan and zoom video animation. Creates videos where images "
                    "are zoomed in and pan vertically with alternating directions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
    python -m src.cli.pan_zoom images_config.json output.mp4
    python -m src.cli.pan_zoom images_config.json --audio music.mp3 output.mp4
    python -m src.cli.pan_zoom images_config.json --ratio 16:9 --quality 1080p output.mp4
    python -m src.cli.pan_zoom images_config.json --upload output.mp4

Config JSON format:
    [
      {"image": "path/to/image1.png", "seconds": 5},
      {"image": "https://example.com/image2.png", "seconds": 4}
    ]

Captions JSON format (for --captions):
    [{"text": "word", "start": 0.0, "end": 0.5}, ...]

Note: Both local file paths and image URLs are supported.
Output videos are saved to output/ directory.
"""
    )
    parser.add_argument("config", help="Config JSON file containing list of images")
    parser.add_argument("output", nargs="?", help="Output video file (optional, defaults to timestamped name)")
    parser.add_argument("--audio", help="Background music file or URL")
    parser.add_argument("--volume", type=float, default=1.0, help="Audio volume (0.0-1.0, default: 1.0)")
    parser.add_argument("--upload", action="store_true", help="Upload video to AWS S3")
    parser.add_argument("--captions", help="Timed captions JSON file")
    parser.add_argument(
        "--ratio",
        choices=list(ASPECT_RATIOS.keys()),
        help=f"Aspect ratio (default: 9:16). Available: {', '.join(ASPECT_RATIOS.keys())}",
    )
    parser.add_argument(
        "--quality",
        choices=list(QUALITY_PRESETS.keys()),
        help=f"Video quality (default: 720p). Available: {', '.join(QUALITY_PRESETS.keys())}",
    )
    parsed = parser.parse_args()

    # Use shared config loader from utils (supports 'url' key)
    image_configs = load_and_validate_image_configs(parsed.config, require_image_key=False)

    output_video = parsed.output
    audio_path = parsed.audio
    audio_volume = parsed.volume
    upload_to_aws = parsed.upload
    aspect_ratio = parsed.ratio
    quality = parsed.quality
    captions_path = parsed.captions

    if not 0.0 <= audio_volume <= 1.0:
        handle_error("--volume must be between 0.0 and 1.0")

    if captions_path:
        captions_path = Path(captions_path)
        if not captions_path.exists():
            handle_error(f"Captions file not found: {captions_path}")

    if audio_path:
        if not is_url(audio_path):
            audio_p = Path(audio_path)
            if not audio_p.exists():
                handle_error(f"Audio file not found: {audio_path}")
            audio_path = audio_p

    if output_video is None:
        # Relative import for package structure
        # Relative import for grouped structure (filename now in subdir)
        from ..filename.filename_utils import generate_timestamped_filename
        output_video = generate_timestamped_filename()
        log_info(f"Generated filename: {output_video}")

    captions = None
    if captions_path:
        # Relative import for grouped structure (captions now in subdir)
        from ..captions.caption_overlay import load_captions_from_json
        captions = load_captions_from_json(str(captions_path))
        log_info(f"Loaded {len(captions)} caption segments from {captions_path}")

    with CleanupManager(TEMP_DIR) as cleanup:
        if audio_path:
            audio_path = resolve_audio_path(audio_path, cleanup)

        # Relative import for grouped structure (video now in subdir)
        from ..video.video_writer import create_pan_zoom_video
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

    log_info("\n✓ Cleanup complete - all temporary files removed")

    if s3_url:
        print(f"\n{'='*60}")
        print(f"S3 URL: <s3url>{s3_url}</s3url>")
        print(f"{'='*60}")
    else:
        log_success(f"\n✓ Success! Video saved locally: {video_path}")


if __name__ == "__main__":
    main()
