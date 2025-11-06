"""Path generation utilities for cursor movement"""

import numpy as np


def generate_diagonal_zigzag_path(width, height, amplitude, angle_deg, reveal_duration, fps):
    """Generate zig-zag path from top-left to bottom-right at specified angle with human-like movement

    Args:
        width: Canvas width in pixels
        height: Canvas height in pixels
        amplitude: Zig-zag amplitude (how far perpendicular to diagonal)
        angle_deg: Diagonal angle in degrees from horizontal
        reveal_duration: Duration of the reveal animation in seconds
        fps: Frames per second

    Returns:
        list: List of (x, y) tuples representing cursor positions for each frame
    """
    total_frames = int(reveal_duration * fps)
    path = []

    # Convert angle to radians
    angle_rad = np.radians(angle_deg)

    # Calculate diagonal direction vector
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)

    # Calculate the distance needed to fully cover the canvas
    # Add extra distance to ensure full coverage (1.5x diagonal)
    diagonal_length = np.sqrt(width**2 + height**2) * 1.5

    # Start position (offset to left and up for smooth entry)
    start_x = -200
    start_y = -200

    # Pre-generate smooth amplitude variations
    np.random.seed(42)  # For reproducible smooth randomness
    amplitude_variations = np.random.uniform(0.8, 1.2, total_frames)
    # Smooth out variations with moving average
    window = 15
    amplitude_variations = np.convolve(amplitude_variations, np.ones(window)/window, mode='same')

    for frame in range(total_frames):
        # Linear progress
        linear_progress = frame / total_frames

        # Apply ease-in-out for natural acceleration/deceleration
        # Smooth S-curve (smoothstep function)
        progress = linear_progress * linear_progress * (3 - 2 * linear_progress)

        # Position along the diagonal
        dist_along_diagonal = progress * diagonal_length
        base_x = start_x + dist_along_diagonal * dx
        base_y = start_y + dist_along_diagonal * dy

        # Add zig-zag perpendicular to the diagonal
        # Perpendicular vector (rotate 90 degrees)
        perp_x = -dy
        perp_y = dx

        # Zig-zag with multiple oscillations and smooth variation
        frequency = 4  # number of complete zig-zags

        # Use pre-generated smooth amplitude variation
        amplitude_variation = amplitude * amplitude_variations[frame]
        zig_offset = amplitude_variation * np.sin(frequency * progress * 2 * np.pi)

        # Calculate base position with zig-zag
        pos_x = base_x + zig_offset * perp_x
        pos_y = base_y + zig_offset * perp_y

        # Final position (don't clamp - let cursor move off-screen naturally)
        x = int(pos_x)
        y = int(pos_y)

        path.append((x, y))

    return path


def create_diagonal_reveal_mask(width, height, cursor_x, cursor_y, angle_deg):
    """Create a mask for revealing the image along a diagonal line

    Args:
        width: Canvas width in pixels
        height: Canvas height in pixels
        cursor_x: Current cursor X position
        cursor_y: Current cursor Y position
        angle_deg: Diagonal angle in degrees from horizontal

    Returns:
        numpy.ndarray: Binary mask (255 = revealed, 0 = hidden)
    """
    # Convert angle to radians
    angle_rad = np.radians(angle_deg)

    # Create coordinate grids
    x_coords = np.arange(width)
    y_coords = np.arange(height)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # Vector from cursor to each point
    vx = xx - cursor_x
    vy = yy - cursor_y

    # Diagonal direction vector
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)

    # Project onto diagonal direction
    # If negative, point is behind the cursor (should be revealed)
    projection = vx * dx + vy * dy

    # Create mask
    mask = (projection <= 0).astype(np.uint8) * 255

    return mask
