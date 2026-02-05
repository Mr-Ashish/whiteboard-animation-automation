"""Pan and zoom animation utilities"""

import numpy as np
import cv2
# Relative import for grouped structure
from ..config.config import FPS, DEFAULT_ZOOM_LEVEL, DEFAULT_PAN_DISTANCE_RATIO, DEFAULT_PAN_DIRECTION


def create_pan_zoom_animation(image, width, height, duration_seconds, direction=None, 
                              zoom_level=None, pan_distance_ratio=None):
    """Create frames for pan-zoom animation (vertical or horizontal)

    Args:
        image: The image to animate (numpy.ndarray, already fitted to canvas with letterboxing)
        width: Video width in pixels
        height: Video height in pixels
        duration_seconds: Duration of animation in seconds
        direction: "up", "down", "left", "right" (default from config). 
        zoom_level: Zoom factor (1.0 = no zoom, 1.1 = 10% zoom in). Default uses config.
        pan_distance_ratio: Pan distance as ratio of dimension (0.0-1.0). Default uses config.

    Returns:
        list: List of frames (numpy.ndarray) for the animation
    """
    if direction is None:
        direction = DEFAULT_PAN_DIRECTION
    if zoom_level is None:
        zoom_level = DEFAULT_ZOOM_LEVEL
    if pan_distance_ratio is None:
        pan_distance_ratio = DEFAULT_PAN_DISTANCE_RATIO

    frames = []
    img_height, img_width = image.shape[:2]
    
    # Calculate zoomed dimensions
    zoomed_width = int(img_width * zoom_level)
    zoomed_height = int(img_height * zoom_level)
    
    # Resize image with zoom
    zoomed_image = cv2.resize(image, (zoomed_width, zoomed_height), 
                              interpolation=cv2.INTER_LANCZOS4)
    
    # Center offsets
    center_x = (zoomed_width - width) // 2
    center_y = (zoomed_height - height) // 2
    
    # Available pan spaces for all directions
    avail_up = center_y
    avail_down = zoomed_height - height - center_y
    avail_left = center_x
    avail_right = zoomed_width - width - center_x
    
    # Requested distance: height for vert, width for horiz
    if direction in ("up", "down"):
        requested_pan_distance = int(height * pan_distance_ratio)
        max_available = min(avail_up, avail_down)
    else:  # left or right
        requested_pan_distance = int(width * pan_distance_ratio)
        max_available = min(avail_left, avail_right)
    
    pan_distance_pixels = min(requested_pan_distance, max_available)
    
    # Minimum movement if zero
    if pan_distance_pixels == 0:
        pan_distance_pixels = max(1, max_available)
    
    # Note if reduced
    if pan_distance_pixels < requested_pan_distance:
        print(f"  Note: Pan distance reduced from {requested_pan_distance}px to {pan_distance_pixels}px "
              f"(avail: {max_available}px)")
    
    # Generate frames
    total_frames = int(duration_seconds * FPS)
    
    for frame_idx in range(total_frames):
        # Calculate progress (0.0 to 1.0) - linear, no easing
        if total_frames == 1:
            progress = 0.0
        else:
            progress = frame_idx / (total_frames - 1)
        
        # Linear progress, calculate offset based on direction
        if direction == "up":
            offset_y = -pan_distance_pixels * (1 - progress)
            offset_x = 0
        elif direction == "down":
            offset_y = pan_distance_pixels * (1 - progress)
            offset_x = 0
        elif direction == "left":
            offset_x = -pan_distance_pixels * (1 - progress)
            offset_y = 0
        elif direction == "right":
            offset_x = pan_distance_pixels * (1 - progress)
            offset_y = 0
        else:
            offset_x = offset_y = 0
        
        # Crop region
        crop_x = center_x + int(offset_x)
        crop_y = center_y + int(offset_y)
        
        # Bounds check
        crop_x = max(0, min(crop_x, zoomed_width - width))
        crop_y = max(0, min(crop_y, zoomed_height - height))
        
        # Extract frame from zoomed image
        frame = zoomed_image[crop_y:crop_y+height, crop_x:crop_x+width].copy()
        
        # Ensure frame is exactly the right size (handle edge cases)
        if frame.shape[0] != height or frame.shape[1] != width:
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
        frames.append(frame)
    
    return frames
