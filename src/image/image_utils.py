"""Image loading and processing utilities"""

import cv2
import numpy as np
from pathlib import Path
# Relative import for grouped structure
from ..download.download_utils import resolve_image_path


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
