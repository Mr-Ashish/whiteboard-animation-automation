"""Video writing and stitching utilities"""

import cv2
import subprocess
from pathlib import Path
from .config import (
    WIDTH, HEIGHT, FPS, DEFAULT_REVEAL_DURATION,
    DEFAULT_TOTAL_DURATION, ZIG_ZAG_AMPLITUDE, OUTPUT_DIR, TEMP_DIR
)
from .image_utils import load_and_resize_image
from .animation import create_single_reveal_animation
from .cleanup_utils import ensure_output_dir


def write_frames_to_video(frames, output_path, show_progress=True):
    """Write frames to a video file

    Args:
        frames: List of frames (numpy.ndarray)
        output_path: Path to output video file
        show_progress: Whether to show progress updates

    Returns:
        Path: Path to the created video file
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, FPS, (WIDTH, HEIGHT))

    if not out.isOpened():
        raise ValueError(f"Could not open video writer for: {output_path}")

    total_frames = len(frames)
    for frame_idx, frame in enumerate(frames):
        out.write(frame)
        # Progress indicator
        if show_progress and frame_idx % 60 == 0:
            print(f"Progress: {frame_idx}/{total_frames} frames ({frame_idx*100//total_frames}%)")

    out.release()
    return output_path


def convert_to_h264(video_path):
    """Convert video to H.264 codec using ffmpeg

    Args:
        video_path: Path to the video file to convert

    Returns:
        bool: True if conversion successful, False otherwise
    """
    print("\nConverting to H.264 (if ffmpeg available)...")
    temp_output = video_path.with_suffix('.tmp.mp4')

    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', str(video_path),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-pix_fmt', 'yuv420p', str(temp_output)
        ], check=True, capture_output=True)

        # Replace original with converted
        video_path.unlink()
        temp_output.rename(video_path)
        print(f"✓ Converted to H.264: {video_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: ffmpeg not found or failed. Video saved as mp4v codec.")
        if temp_output.exists():
            temp_output.unlink()
        return False


def create_reveal_video(image_path, output_path, pencil_cursor, pencil_cursor_size,
                       reveal_duration=None, total_duration=None, cleanup_manager=None):
    """Create the diagonal zig-zag reveal animation video for a single image

    Args:
        image_path: Path to the image file or URL
        output_path: Path to output video file
        pencil_cursor: Cursor image with alpha channel
        pencil_cursor_size: Size of cursor in pixels
        reveal_duration: Duration of reveal animation in seconds (optional)
        total_duration: Total duration including hold time in seconds (optional)
        cleanup_manager: Optional CleanupManager for temp file cleanup

    Returns:
        Path: Path to the created video file
    """
    if reveal_duration is None:
        reveal_duration = DEFAULT_REVEAL_DURATION
    if total_duration is None:
        total_duration = DEFAULT_TOTAL_DURATION

    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    # Load and prepare image
    print(f"Loading image: {image_path}")
    main_image = load_and_resize_image(image_path, WIDTH, HEIGHT, cleanup_manager)

    print(f"Generating diagonal zig-zag animation...")
    print(f"Reveal duration: {reveal_duration}s, Total duration: {total_duration}s")

    # Create animation frames
    frames = create_single_reveal_animation(main_image, pencil_cursor, pencil_cursor_size,
                                           reveal_duration, total_duration, ZIG_ZAG_AMPLITUDE)

    print(f"Creating video: {output_path}")

    # Write frames to video
    write_frames_to_video(frames, output_path)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    return output_path


def create_multi_reveal_video(image_configs, output_path, pencil_cursor, pencil_cursor_size,
                             cleanup_manager=None):
    """Create a video with multiple image reveals stitched together

    Args:
        image_configs: List of dicts with 'image' (path/URL) and 'seconds' (duration) keys
                      Example: [
                          {'image': 'path/to/img1.png', 'seconds': 5},
                          {'image': 'https://example.com/img2.png', 'seconds': 3}
                      ]
        output_path: Path to output video file
        pencil_cursor: Cursor image with alpha channel
        pencil_cursor_size: Size of cursor in pixels
        cleanup_manager: Optional CleanupManager for temp file cleanup

    Returns:
        Path: Path to the created video file
    """
    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    all_frames = []

    for idx, config in enumerate(image_configs):
        image_path = config.get('image')
        seconds = config.get('seconds', DEFAULT_TOTAL_DURATION)

        if not image_path:
            raise ValueError(f"Missing 'image' key in config at index {idx}")

        # Calculate reveal duration (half of total duration by default)
        reveal_duration = seconds * 0.5
        total_duration = seconds

        print(f"\n[{idx+1}/{len(image_configs)}] Processing: {image_path}")
        print(f"  Duration: {seconds}s (reveal: {reveal_duration}s)")

        # Load image
        main_image = load_and_resize_image(image_path, WIDTH, HEIGHT, cleanup_manager)

        # Generate frames for this image
        frames = create_single_reveal_animation(main_image, pencil_cursor, pencil_cursor_size,
                                               reveal_duration, total_duration, ZIG_ZAG_AMPLITUDE)
        all_frames.extend(frames)
        print(f"  Generated {len(frames)} frames")

    # Write all frames to video
    print(f"\nWriting final video: {output_path}")
    print(f"Total frames: {len(all_frames)}, Duration: {len(all_frames)/FPS:.1f}s")

    write_frames_to_video(all_frames, output_path)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    return output_path


def _resolve_output_path(output_path):
    """Resolve output path, using output directory if relative path

    Args:
        output_path: Requested output path (string or Path)

    Returns:
        Path: Resolved absolute output path
    """
    output_path = Path(output_path)

    # If relative path, place in output directory
    if not output_path.is_absolute():
        output_path = OUTPUT_DIR / output_path

    # Ensure output directory exists
    ensure_output_dir(output_path)

    return output_path
