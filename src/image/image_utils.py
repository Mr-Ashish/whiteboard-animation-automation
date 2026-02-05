"""Image loading and processing utilities"""

import cv2
import numpy as np
from pathlib import Path
# Relative import for grouped structure
from ..download.download_utils import resolve_image_path, resolve_video_path


def load_and_resize_image(image_path_or_url, target_width, target_height, cleanup_manager=None):
    """Load image and fit it to canvas with letterboxing

    Args:
        image_path_or_url: Path to the image file or URL
        target_width: Target canvas width
        target_height: Target canvas height
        cleanup_manager: Optional CleanupManager for temp file cleanup

    Returns:
        numpy.ndarray: Resized image on white canvas
    """
    # Resolve URL or local path
    image_path = resolve_image_path(image_path_or_url, cleanup_manager)

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path_or_url}")

    # Create white canvas
    canvas = np.ones((target_height, target_width, 3), dtype=np.uint8) * 255

    # Calculate scaling to fit image
    img_h, img_w = img.shape[:2]
    scale = min(target_width / img_w, target_height / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    # Resize image
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Center on canvas
    x_offset = (target_width - new_w) // 2
    y_offset = (target_height - new_h) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas


def remove_green_screen(frame, lower_green=np.array([35, 40, 40]), upper_green=np.array([85, 255, 255])):
    """Remove green screen background from frame (for avatar videos)

    Uses HSV color range for green; returns foreground with black bg (for overlay).
    Tunable ranges for different green shades.

    Args:
        frame: BGR numpy frame from avatar video
        lower_green, upper_green: HSV bounds for green detection

    Returns:
        numpy.ndarray: Foreground frame with green removed (black bg)
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    # Morphology to clean mask (remove noise)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=1)
    # Foreground: keep non-green parts
    fg = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
    return fg


def load_avatar_video_frames(avatar_path, target_duration_seconds, target_width, target_height, cleanup_manager=None):
    """Load and process avatar video frames (green screen removed, resized, looped to duration)

    Args:
        avatar_path: Local path or URL to avatar video (green screen character)
        target_duration_seconds: Duration to fill (loop video if shorter)
        target_width, target_height: Target size for composite
        cleanup_manager: Optional

    Returns:
        list: List of processed BGR frames (green removed, ready for overlay)
    """
    # Resolve URL if needed
    avatar_path = resolve_video_path(avatar_path, cleanup_manager)
    cap = cv2.VideoCapture(str(avatar_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open avatar video: {avatar_path}")

    avatar_frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    orig_duration = frame_count / fps if fps > 0 else 1.0

    # Read all original frames, process
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Remove green
        fg = remove_green_screen(frame)
        # Resize to target (keep aspect? simple stretch for now)
        resized = cv2.resize(fg, (target_width // 3, target_height // 3), interpolation=cv2.INTER_LANCZOS4)  # small overlay size
        avatar_frames.append(resized)

    cap.release()

    # Loop to fill target duration
    total_target_frames = int(target_duration_seconds * 30)  # assume 30fps
    looped_frames = []
    if avatar_frames:
        for i in range(total_target_frames):
            looped_frames.append(avatar_frames[i % len(avatar_frames)])
    return looped_frames
