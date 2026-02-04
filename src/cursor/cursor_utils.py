"""Cursor and pencil creation utilities"""

import cv2
import numpy as np
from pathlib import Path


def load_pencil_cursor(pencil_path, size):
    """Load hand/pencil cursor image with transparency

    Args:
        pencil_path: Path to the cursor image file
        size: Desired size (width/height) of the square cursor

    Returns:
        numpy.ndarray: Cursor image with alpha channel (RGBA)
    """
    cursor = cv2.imread(str(pencil_path), cv2.IMREAD_UNCHANGED)

    if cursor is None:
        raise ValueError(f"Could not load pencil cursor image: {pencil_path}")

    # Add alpha channel if not present
    if cursor.shape[2] == 3:
        # Add fully opaque alpha channel
        alpha = np.ones((cursor.shape[0], cursor.shape[1], 1), dtype=np.uint8) * 255
        cursor = np.concatenate([cursor, alpha], axis=2)

    # Resize to desired size maintaining aspect ratio
    h, w = cursor.shape[:2]
    scale = size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)

    cursor = cv2.resize(cursor, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Pad to square if needed
    if new_w != new_h:
        padded = np.zeros((size, size, 4), dtype=np.uint8)
        y_offset = (size - new_h) // 2
        x_offset = (size - new_w) // 2
        padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = cursor
        cursor = padded

    return cursor


def create_simple_pencil_cursor(size):
    """Create a simple pencil hand cursor fallback

    Args:
        size: Desired size (width/height) of the square cursor

    Returns:
        numpy.ndarray: Cursor image with alpha channel (RGBA)
    """
    cursor = np.zeros((size, size, 4), dtype=np.uint8)
    center = size // 2

    # Draw a pencil-like shape pointing down-right
    # Wood part (hexagonal body)
    pts = np.array([
        [center-15, center-30],
        [center+15, center-30],
        [center+20, center+10],
        [center, center+40],
        [center-20, center+10]
    ], np.int32)
    cv2.fillPoly(cursor, [pts], (180, 140, 80, 255))

    # Tip (darker)
    tip_pts = np.array([
        [center-10, center+10],
        [center+10, center+10],
        [center, center+40]
    ], np.int32)
    cv2.fillPoly(cursor, [tip_pts], (40, 40, 40, 255))

    return cursor
