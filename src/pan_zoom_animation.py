"""Pan and zoom animation utilities"""

import numpy as np
import cv2
from .config import FPS, DEFAULT_ZOOM_LEVEL, DEFAULT_PAN_DISTANCE_RATIO


def create_pan_zoom_animation(image, width, height, duration_seconds, direction="up", 
                              zoom_level=None, pan_distance_ratio=None):
    """Create frames for pan-zoom animation with vertical movement

    Args:
        image: The image to animate (numpy.ndarray, already fitted to canvas with letterboxing)
        width: Video width in pixels
        height: Video height in pixels
        duration_seconds: Duration of animation in seconds
        direction: "up" or "down" - direction of pan movement
        zoom_level: Zoom factor (1.0 = no zoom, 1.1 = 10% zoom in). Default uses config.
        pan_distance_ratio: Pan distance as ratio of image height (0.0-1.0). Default uses config.

    Returns:
        list: List of frames (numpy.ndarray) for the animation
    """
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
    
    # Calculate center offsets for cropping (centered initially)
    center_x = (zoomed_width - width) // 2
    center_y = (zoomed_height - height) // 2
    
    # Calculate available pan space (how much we can actually pan)
    # Available space is the distance from center to the edge of the zoomed image
    available_pan_space_up = center_y  # How far we can pan upward (negative direction)
    available_pan_space_down = zoomed_height - height - center_y  # How far we can pan downward (positive direction)
    
    # Calculate requested pan distance
    requested_pan_distance = int(height * pan_distance_ratio)
    
    # Use the minimum of requested distance and available space to prevent clamping
    # For "up" direction, we can pan up to available_pan_space_up
    # For "down" direction, we can pan up to available_pan_space_down
    # We'll use the smaller of the two to ensure both directions work
    max_available_pan = min(available_pan_space_up, available_pan_space_down)
    pan_distance_pixels = min(requested_pan_distance, max_available_pan)
    
    # If pan distance is 0, set a minimum to ensure some movement
    if pan_distance_pixels == 0:
        pan_distance_pixels = max(1, max_available_pan)
    
    # Debug: warn if pan distance was reduced due to available space
    if pan_distance_pixels < requested_pan_distance:
        print(f"  Note: Pan distance reduced from {requested_pan_distance}px to {pan_distance_pixels}px "
              f"(available space: {max_available_pan}px)")
    
    # Generate frames
    total_frames = int(duration_seconds * FPS)
    
    for frame_idx in range(total_frames):
        # Calculate progress (0.0 to 1.0) - linear, no easing
        if total_frames == 1:
            progress = 0.0
        else:
            progress = frame_idx / (total_frames - 1)
        
        # Use linear progress directly (no easing for constant speed)
        # Calculate vertical offset based on direction
        if direction == "up":
            # Pan UP: start at top (negative offset), move down (toward 0)
            # This means we start showing the top of the zoomed image and pan downward
            offset_y = -pan_distance_pixels * (1 - progress)
        else:  # down
            # Pan DOWN: start at bottom (positive offset), move up (toward 0)
            # This means we start showing the bottom of the zoomed image and pan upward
            # Start at bottom (positive offset) and move to center (0)
            offset_y = pan_distance_pixels * (1 - progress)
        
        # Calculate crop region
        crop_x = center_x
        crop_y = center_y + int(offset_y)
        
        # Ensure crop region is within bounds
        crop_x = max(0, min(crop_x, zoomed_width - width))
        crop_y = max(0, min(crop_y, zoomed_height - height))
        
        # Extract frame from zoomed image
        frame = zoomed_image[crop_y:crop_y+height, crop_x:crop_x+width].copy()
        
        # Ensure frame is exactly the right size (handle edge cases)
        if frame.shape[0] != height or frame.shape[1] != width:
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
        frames.append(frame)
    
    return frames
