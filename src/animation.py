"""Animation creation utilities for reveal effects"""

import numpy as np
from .config import (
    WIDTH, HEIGHT, FPS, DIAGONAL_ANGLE,
    CURSOR_FADE_IN_FRAMES, CURSOR_FADE_OUT_FRAMES
)
from .path_generator import generate_diagonal_zigzag_path, create_diagonal_reveal_mask


def create_single_reveal_animation(main_image, pencil_cursor, pencil_cursor_size,
                                   reveal_duration, total_duration, zig_zag_amplitude):
    """Create frames for a single image reveal animation

    Args:
        main_image: The image to reveal (numpy.ndarray)
        pencil_cursor: Cursor image with alpha channel (numpy.ndarray, RGBA)
        pencil_cursor_size: Size of the cursor in pixels
        reveal_duration: Duration of the reveal animation in seconds
        total_duration: Total duration including hold time in seconds
        zig_zag_amplitude: Amplitude of the zig-zag motion

    Returns:
        list: List of frames (numpy.ndarray) for the animation
    """
    frames = []
    white_canvas = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255

    # Generate zig-zag path
    reveal_frames = int(reveal_duration * FPS)
    hold_frames = int((total_duration - reveal_duration) * FPS)
    path = generate_diagonal_zigzag_path(WIDTH, HEIGHT, zig_zag_amplitude,
                                        DIAGONAL_ANGLE, reveal_duration, FPS)

    # Create reveal frames
    for frame_idx in range(reveal_frames):
        # Start with white canvas
        frame = white_canvas.copy()

        # Get current cursor position
        cursor_x, cursor_y = path[frame_idx]

        # Create diagonal reveal mask
        reveal_mask = create_diagonal_reveal_mask(WIDTH, HEIGHT, cursor_x, cursor_y, DIAGONAL_ANGLE)

        # Apply mask to reveal image
        for c in range(3):
            frame[:, :, c] = np.where(reveal_mask > 0, main_image[:, :, c], white_canvas[:, :, c])

        # Overlay pencil cursor with alpha blending and fade-in/fade-out
        cursor_alpha_multiplier = _calculate_cursor_alpha(frame_idx, reveal_frames)

        # Draw cursor on frame
        _draw_cursor_on_frame(frame, pencil_cursor, cursor_x, cursor_y,
                            pencil_cursor_size, cursor_alpha_multiplier)

        frames.append(frame)

    # Hold the final fully revealed image
    for _ in range(hold_frames):
        frames.append(main_image.copy())

    return frames


def _calculate_cursor_alpha(frame_idx, total_frames):
    """Calculate cursor alpha multiplier for fade in/out effect

    Args:
        frame_idx: Current frame index
        total_frames: Total number of frames in animation

    Returns:
        float: Alpha multiplier (0.0 to 1.0)
    """
    if frame_idx < CURSOR_FADE_IN_FRAMES:
        # Fade in at the start
        return frame_idx / CURSOR_FADE_IN_FRAMES
    elif frame_idx > total_frames - CURSOR_FADE_OUT_FRAMES:
        # Fade out at the end
        frames_from_end = total_frames - frame_idx
        return frames_from_end / CURSOR_FADE_OUT_FRAMES
    else:
        # Full opacity in the middle
        return 1.0


def _draw_cursor_on_frame(frame, pencil_cursor, cursor_x, cursor_y,
                         pencil_cursor_size, alpha_multiplier):
    """Draw cursor on frame with alpha blending

    Args:
        frame: Frame to draw on (modified in place)
        pencil_cursor: Cursor image with alpha channel
        cursor_x: Cursor X position
        cursor_y: Cursor Y position
        pencil_cursor_size: Size of the cursor
        alpha_multiplier: Alpha multiplier for fade effects
    """
    cursor_half = pencil_cursor_size // 2

    # Calculate frame bounds
    y1 = max(0, cursor_y - cursor_half)
    y2 = min(HEIGHT, cursor_y + cursor_half)
    x1 = max(0, cursor_x - cursor_half)
    x2 = min(WIDTH, cursor_x + cursor_half)

    # Only draw cursor if it's at least partially visible
    if y2 > y1 and x2 > x1:
        # Calculate cursor region bounds
        cy1 = max(0, cursor_half - (cursor_y - y1))
        cy2 = min(pencil_cursor_size, cursor_half + (y2 - cursor_y))
        cx1 = max(0, cursor_half - (cursor_x - x1))
        cx2 = min(pencil_cursor_size, cursor_half + (x2 - cursor_x))

        # Ensure regions are valid
        if cy2 > cy1 and cx2 > cx1:
            cursor_region = pencil_cursor[cy1:cy2, cx1:cx2]
            frame_region_h = y2 - y1
            frame_region_w = x2 - x1

            # Double check dimensions match
            if cursor_region.shape[0] == frame_region_h and cursor_region.shape[1] == frame_region_w:
                alpha = (cursor_region[:, :, 3:] / 255.0) * alpha_multiplier
                for c in range(3):
                    frame[y1:y2, x1:x2, c] = (
                        alpha[:, :, 0] * cursor_region[:, :, c] +
                        (1 - alpha[:, :, 0]) * frame[y1:y2, x1:x2, c]
                    )
