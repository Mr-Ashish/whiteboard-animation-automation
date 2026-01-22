"""Video writing and stitching utilities"""

import cv2
import subprocess
from pathlib import Path
from .config import (
    WIDTH, HEIGHT, FPS, DEFAULT_REVEAL_DURATION,
    DEFAULT_TOTAL_DURATION, ZIG_ZAG_AMPLITUDE, OUTPUT_DIR, TEMP_DIR,
    calculate_dimensions, calculate_cursor_size
)
from .image_utils import load_and_resize_image
from .animation import create_single_reveal_animation, create_static_hold_frames
from .pan_zoom_animation import create_pan_zoom_animation
from .cleanup_utils import ensure_output_dir
from .audio_utils import match_video_to_audio_length
from .aws_utils import upload_to_s3


def write_frames_to_video(frames, output_path, width=None, height=None, show_progress=True):
    """Write frames to a video file

    Args:
        frames: List of frames (numpy.ndarray)
        output_path: Path to output video file
        width: Video width (uses default WIDTH if None)
        height: Video height (uses default HEIGHT if None)
        show_progress: Whether to show progress updates

    Returns:
        Path: Path to the created video file
    """
    if width is None:
        width = WIDTH
    if height is None:
        height = HEIGHT

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, FPS, (width, height))

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
                       reveal_duration=None, total_duration=None, cleanup_manager=None,
                       audio_path=None, audio_volume=1.0, upload_to_aws=False,
                       aspect_ratio=None, quality=None):
    """Create the diagonal zig-zag reveal animation video for a single image

    Args:
        image_path: Path to the image file or URL
        output_path: Path to output video file
        pencil_cursor: Cursor image with alpha channel
        pencil_cursor_size: Size of cursor in pixels
        reveal_duration: Duration of reveal animation in seconds (optional)
        total_duration: Total duration including hold time in seconds (optional)
        cleanup_manager: Optional CleanupManager for temp file cleanup
        audio_path: Optional path to background music file (mp3, wav, etc.)
        audio_volume: Audio volume level (0.0 to 1.0, default 1.0)
        upload_to_aws: Whether to upload to AWS S3 (default False)
        aspect_ratio: Aspect ratio (e.g., '16:9', '9:16', default None uses config default)
        quality: Quality preset (e.g., '720p', '1080p', default None uses config default)

    Returns:
        tuple: (Path to video file, S3 URL if uploaded else None)
    """
    if reveal_duration is None:
        reveal_duration = DEFAULT_REVEAL_DURATION
    if total_duration is None:
        total_duration = DEFAULT_TOTAL_DURATION

    # Calculate dimensions (handles None values with defaults)
    width, height = calculate_dimensions(aspect_ratio, quality)
    if aspect_ratio or quality:
        print(f"Using dimensions: {width}x{height} ({aspect_ratio or 'default ratio'}, {quality or 'default quality'})")

    # Scale cursor size based on dimensions
    scaled_cursor_size = calculate_cursor_size(width, height)
    if scaled_cursor_size != pencil_cursor_size:
        print(f"Scaling cursor from {pencil_cursor_size}px to {scaled_cursor_size}px for {width}x{height}")
        # Re-scale the cursor if it was already loaded
        if pencil_cursor.shape[0] != scaled_cursor_size:
            pencil_cursor = cv2.resize(pencil_cursor, (scaled_cursor_size, scaled_cursor_size),
                                      interpolation=cv2.INTER_LANCZOS4)
        pencil_cursor_size = scaled_cursor_size

    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    # Load and prepare image
    print(f"Loading image: {image_path}")
    main_image = load_and_resize_image(image_path, width, height, cleanup_manager)

    print(f"Generating diagonal zig-zag animation...")
    print(f"Reveal duration: {reveal_duration}s, Total duration: {total_duration}s")

    # Create animation frames
    frames = create_single_reveal_animation(main_image, pencil_cursor, pencil_cursor_size,
                                           reveal_duration, total_duration, ZIG_ZAG_AMPLITUDE)

    print(f"Creating video: {output_path}")

    # Write frames to video
    write_frames_to_video(frames, output_path, width, height)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    # Add background music if provided
    if audio_path:
        output_path = _add_audio_to_video(output_path, audio_path, audio_volume, cleanup_manager)

    # Upload to S3 if requested
    s3_url = None
    if upload_to_aws:
        try:
            s3_url = upload_to_s3(output_path)
        except Exception as e:
            print(f"Warning: S3 upload failed: {e}")
            print("Video saved locally only.")

    return output_path, s3_url


def create_static_cover_video(image_path, output_path, cleanup_manager=None,
                              audio_path=None, audio_volume=1.0, upload_to_aws=False,
                              aspect_ratio=None, quality=None, duration_seconds=1.0):
    """Create a static cover video showing an image for a specified duration

    Args:
        image_path: Path to the image file or URL
        output_path: Path to output video file
        cleanup_manager: Optional CleanupManager for temp file cleanup
        audio_path: Optional path to background music file (mp3, wav, etc.)
        audio_volume: Audio volume level (0.0 to 1.0, default 1.0)
        upload_to_aws: Whether to upload to AWS S3 (default False)
        aspect_ratio: Aspect ratio (e.g., '16:9', '9:16', default None uses config default)
        quality: Quality preset (e.g., '720p', '1080p', default None uses config default)
        duration_seconds: Duration to show the image in seconds (default 1.0)

    Returns:
        tuple: (Path to video file, S3 URL if uploaded else None)
    """
    # Calculate dimensions (handles None values with defaults)
    width, height = calculate_dimensions(aspect_ratio, quality)
    if aspect_ratio or quality:
        print(f"Using dimensions: {width}x{height} ({aspect_ratio or 'default ratio'}, {quality or 'default quality'})")

    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    # Load and prepare image
    print(f"Loading cover image: {image_path}")
    main_image = load_and_resize_image(image_path, width, height, cleanup_manager)

    # Create static frames
    print(f"Creating static cover video ({duration_seconds} second)")
    frames = create_static_hold_frames(main_image, duration_seconds=duration_seconds)

    # Write frames to video
    write_frames_to_video(frames, output_path, width, height)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    # Add background music if provided
    if audio_path:
        output_path = _add_audio_to_video(output_path, audio_path, audio_volume, cleanup_manager)

    # Upload to S3 if requested
    s3_url = None
    if upload_to_aws:
        try:
            s3_url = upload_to_s3(output_path)
        except Exception as e:
            print(f"Warning: S3 upload failed: {e}")
            print("Video saved locally only.")

    return output_path, s3_url


def create_multi_reveal_video(image_configs, output_path, pencil_cursor, pencil_cursor_size,
                             cleanup_manager=None, audio_path=None, audio_volume=1.0, upload_to_aws=False,
                             aspect_ratio=None, quality=None):
    """Create a video with multiple image reveals stitched together

    Args:
        image_configs: List of dicts with 'image' (path/URL), 'type' ('scene'/'cover'), and 'seconds' (duration) keys
                      Example: [
                          {'image': 'path/to/img1.png', 'type': 'scene', 'seconds': 5},
                          {'image': 'https://example.com/img2.png', 'seconds': 3},
                          {'image': 'cover.jpg', 'type': 'cover'}
                      ]
                      type defaults to 'scene', cover images shown for 1s at end
        output_path: Path to output video file
        pencil_cursor: Cursor image with alpha channel
        pencil_cursor_size: Size of cursor in pixels
        cleanup_manager: Optional CleanupManager for temp file cleanup
        audio_path: Optional path to background music file (mp3, wav, etc.)
        audio_volume: Audio volume level (0.0 to 1.0, default 1.0)
        upload_to_aws: Whether to upload to AWS S3 (default False)
        aspect_ratio: Aspect ratio (e.g., '16:9', '9:16', default None uses config default)
        quality: Quality preset (e.g., '720p', '1080p', default None uses config default)

    Returns:
        tuple: (Path to video file, S3 URL if uploaded else None)
    """
    # Calculate dimensions (handles None values with defaults)
    width, height = calculate_dimensions(aspect_ratio, quality)
    if aspect_ratio or quality:
        print(f"Using dimensions: {width}x{height} ({aspect_ratio or 'default ratio'}, {quality or 'default quality'})")

    # Scale cursor size based on dimensions
    scaled_cursor_size = calculate_cursor_size(width, height)
    if scaled_cursor_size != pencil_cursor_size:
        print(f"Scaling cursor from {pencil_cursor_size}px to {scaled_cursor_size}px for {width}x{height}")
        # Re-scale the cursor if it was already loaded
        if pencil_cursor.shape[0] != scaled_cursor_size:
            pencil_cursor = cv2.resize(pencil_cursor, (scaled_cursor_size, scaled_cursor_size),
                                      interpolation=cv2.INTER_LANCZOS4)
        pencil_cursor_size = scaled_cursor_size

    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    all_frames = []
    cover_image = None  # Track first cover image

    for idx, config in enumerate(image_configs):
        # Support both 'image' and 'url' keys
        image_path = config.get('image') or config.get('url')
        image_type = config.get('type', 'scene')  # Default to 'scene'
        seconds = config.get('seconds', DEFAULT_TOTAL_DURATION)

        if not image_path:
            raise ValueError(f"Missing 'image' or 'url' key in config at index {idx}")

        # Validate image type
        if image_type not in ['scene', 'cover']:
            raise ValueError(f"Invalid type '{image_type}' at index {idx}. Must be 'scene' or 'cover'")

        # Load image
        main_image = load_and_resize_image(image_path, width, height, cleanup_manager)

        # Handle based on type
        if image_type == 'cover':
            # Save first cover, skip animation
            if cover_image is None:
                cover_image = main_image
                print(f"\n[{idx+1}/{len(image_configs)}] Cover image: {image_path}")
            else:
                print(f"\n[{idx+1}/{len(image_configs)}] Skipping duplicate cover: {image_path}")
            continue

        elif image_type == 'scene':
            # Normal reveal animation
            # Calculate reveal duration (half of total duration by default)
            reveal_duration = seconds * 0.5
            total_duration = seconds

            print(f"\n[{idx+1}/{len(image_configs)}] Processing scene: {image_path}")
            print(f"  Duration: {seconds}s (reveal: {reveal_duration}s)")

            # Generate frames for this image
            frames = create_single_reveal_animation(main_image, pencil_cursor, pencil_cursor_size,
                                                   reveal_duration, total_duration, ZIG_ZAG_AMPLITUDE)
            all_frames.extend(frames)
            print(f"  Generated {len(frames)} frames")

    # Append cover image at the end if found
    if cover_image is not None:
        print(f"\nAdding cover image buffer (1 second)")
        cover_frames = create_static_hold_frames(cover_image, duration_seconds=1.0)
        all_frames.extend(cover_frames)
        print(f"  Generated {len(cover_frames)} cover frames")

    # Write all frames to video
    print(f"\nWriting final video: {output_path}")
    print(f"Total frames: {len(all_frames)}, Duration: {len(all_frames)/FPS:.1f}s")

    write_frames_to_video(all_frames, output_path, width, height)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    # Add background music if provided
    if audio_path:
        output_path = _add_audio_to_video(output_path, audio_path, audio_volume, cleanup_manager)

    # Upload to S3 if requested
    s3_url = None
    if upload_to_aws:
        try:
            s3_url = upload_to_s3(output_path)
        except Exception as e:
            print(f"Warning: S3 upload failed: {e}")
            print("Video saved locally only.")

    return output_path, s3_url


def create_pan_zoom_video(image_configs, output_path, cleanup_manager=None,
                          audio_path=None, audio_volume=1.0, upload_to_aws=False,
                          aspect_ratio=None, quality=None, zoom_level=None,
                          pan_distance_ratio=None):
    """Create a video with pan-zoom animation for multiple images

    Images are zoomed in and pan vertically with alternating directions (up/down).

    Args:
        image_configs: List of dicts with 'image' (path/URL) and 'seconds' (duration) keys
                      Example: [
                          {'image': 'path/to/img1.png', 'seconds': 5},
                          {'image': 'https://example.com/img2.png', 'seconds': 4}
                      ]
        output_path: Path to output video file
        cleanup_manager: Optional CleanupManager for temp file cleanup
        audio_path: Optional path to background music file (mp3, wav, etc.)
        audio_volume: Audio volume level (0.0 to 1.0, default 1.0)
        upload_to_aws: Whether to upload to AWS S3 (default False)
        aspect_ratio: Aspect ratio (e.g., '16:9', '9:16', default None uses config default)
        quality: Quality preset (e.g., '720p', '1080p', default None uses config default)
        zoom_level: Zoom factor (1.0 = no zoom, 1.1 = 10% zoom in, default uses config)
        pan_distance_ratio: Pan distance as ratio of image height (0.0-1.0, default uses config)

    Returns:
        tuple: (Path to video file, S3 URL if uploaded else None)
    """
    from .config import DEFAULT_ZOOM_LEVEL, DEFAULT_PAN_DISTANCE_RATIO
    
    # Use defaults if not provided
    if zoom_level is None:
        zoom_level = DEFAULT_ZOOM_LEVEL
    if pan_distance_ratio is None:
        pan_distance_ratio = DEFAULT_PAN_DISTANCE_RATIO

    # Calculate dimensions (handles None values with defaults)
    width, height = calculate_dimensions(aspect_ratio, quality)
    if aspect_ratio or quality:
        print(f"Using dimensions: {width}x{height} ({aspect_ratio or 'default ratio'}, {quality or 'default quality'})")

    print(f"Pan-zoom settings: zoom={zoom_level}x, pan={pan_distance_ratio*100:.0f}% of height")

    # Ensure output directory and resolve path
    output_path = _resolve_output_path(output_path)

    all_frames = []

    for idx, config in enumerate(image_configs):
        # Support both 'image' and 'url' keys
        image_path = config.get('image') or config.get('url')
        seconds = config.get('seconds', 5.0)

        if not image_path:
            raise ValueError(f"Missing 'image' or 'url' key in config at index {idx}")

        # Alternate direction: even indices = up, odd indices = down
        direction = "up" if idx % 2 == 0 else "down"

        # Load image
        print(f"\n[{idx+1}/{len(image_configs)}] Loading: {image_path}")
        main_image = load_and_resize_image(image_path, width, height, cleanup_manager)

        print(f"  Direction: {direction}, Duration: {seconds}s")

        # Generate pan-zoom frames for this image
        frames = create_pan_zoom_animation(
            main_image, width, height, seconds, direction,
            zoom_level=zoom_level, pan_distance_ratio=pan_distance_ratio
        )
        all_frames.extend(frames)
        print(f"  Generated {len(frames)} frames")

    # Write all frames to video
    print(f"\nWriting final video: {output_path}")
    print(f"Total frames: {len(all_frames)}, Duration: {len(all_frames)/FPS:.1f}s")

    write_frames_to_video(all_frames, output_path, width, height)
    print(f"✓ Video created successfully: {output_path}")

    # Convert to H.264
    convert_to_h264(Path(output_path))

    # Add background music if provided
    if audio_path:
        output_path = _add_audio_to_video(output_path, audio_path, audio_volume, cleanup_manager)

    # Upload to S3 if requested
    s3_url = None
    if upload_to_aws:
        try:
            s3_url = upload_to_s3(output_path)
        except Exception as e:
            print(f"Warning: S3 upload failed: {e}")
            print("Video saved locally only.")

    return output_path, s3_url


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


def _add_audio_to_video(video_path, audio_path, volume, cleanup_manager):
    """Add background music to video and cleanup original

    Args:
        video_path: Path to video without audio
        audio_path: Path to audio file
        volume: Audio volume level
        cleanup_manager: CleanupManager for temp file cleanup

    Returns:
        Path: Path to video with audio
    """
    video_path = Path(video_path)

    # Create output path (replace original)
    temp_video = video_path.parent / f"{video_path.stem}_no_audio{video_path.suffix}"

    # Rename original video to temp
    video_path.rename(temp_video)

    # Register temp video for cleanup
    if cleanup_manager:
        cleanup_manager.register_temp_file(temp_video)

    try:
        # Add audio to create final video with original name
        # This will extend video if audio is longer
        final_video = match_video_to_audio_length(
            temp_video,
            audio_path,
            output_path=video_path,
            volume=volume
        )

        # Clean up the temp video without audio
        if temp_video.exists():
            temp_video.unlink()

        return final_video

    except Exception as e:
        # If audio addition fails, restore original video
        if temp_video.exists():
            temp_video.rename(video_path)
        raise e
