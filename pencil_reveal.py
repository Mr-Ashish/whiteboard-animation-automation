#!/usr/bin/env python3
"""
Diagonal zig-zag pencil drawing reveal animation
Creates a video where an image is revealed with a hand/pencil cursor moving in zig-zag pattern
from top-left to bottom-right at 30-degree angle
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Configuration
WIDTH = 1920
HEIGHT = 1080
FPS = 60
REVEAL_DURATION = 1.5  # seconds for the reveal animation
TOTAL_DURATION = 4.0   # total video duration (reveal + hold at end)
ZIG_ZAG_AMPLITUDE = 350  # how far perpendicular to the diagonal path (pixels)
PENCIL_SIZE = 350  # size of the pencil cursor if no image provided
DIAGONAL_ANGLE = 45  # degrees from horizontal (top-left to bottom-right)

def load_and_resize_image(image_path, target_width, target_height):
    """Load image and fit it to canvas with letterboxing"""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

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

def load_pencil_cursor(pencil_path, size):
    """Load hand/pencil cursor image with transparency"""
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
    """Create a simple pencil hand cursor fallback"""
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

def generate_diagonal_zigzag_path(width, height, amplitude, angle_deg, reveal_duration, fps):
    """Generate zig-zag path from top-left to bottom-right at specified angle"""
    total_frames = int(reveal_duration * fps)
    path = []

    # Convert angle to radians
    angle_rad = np.radians(angle_deg)

    # Calculate diagonal direction vector
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)

    # Calculate the diagonal distance we need to travel
    # To go from top-left to bottom-right at angle
    diagonal_length = np.sqrt(width**2 + height**2)

    # Start position (top-left)
    start_x = 0
    start_y = 0

    for frame in range(total_frames):
        progress = frame / total_frames

        # Position along the diagonal
        dist_along_diagonal = progress * diagonal_length
        base_x = start_x + dist_along_diagonal * dx
        base_y = start_y + dist_along_diagonal * dy

        # Add zig-zag perpendicular to the diagonal
        # Perpendicular vector (rotate 90 degrees)
        perp_x = -dy
        perp_y = dx

        # Zig-zag with multiple oscillations
        frequency = 3  # number of complete zig-zags
        zig_offset = amplitude * np.sin(frequency * progress * 2 * np.pi)

        # Final position
        x = int(base_x + zig_offset * perp_x)
        y = int(base_y + zig_offset * perp_y)

        # Clamp to image bounds
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))

        path.append((x, y))

    return path

def create_diagonal_reveal_mask(width, height, cursor_x, cursor_y, angle_deg):
    """Create a mask for revealing the image along a diagonal line"""
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

def create_reveal_video(image_path, output_path, pencil_cursor, pencil_cursor_size):
    """Create the diagonal zig-zag reveal animation video"""
    # Load and prepare image
    print(f"Loading image: {image_path}")
    main_image = load_and_resize_image(image_path, WIDTH, HEIGHT)

    # Generate zig-zag path
    print(f"Generating diagonal zig-zag path at {DIAGONAL_ANGLE}° angle...")
    reveal_frames = int(REVEAL_DURATION * FPS)
    hold_frames = int((TOTAL_DURATION - REVEAL_DURATION) * FPS)
    path = generate_diagonal_zigzag_path(WIDTH, HEIGHT, ZIG_ZAG_AMPLITUDE, DIAGONAL_ANGLE, REVEAL_DURATION, FPS)

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, FPS, (WIDTH, HEIGHT))

    if not out.isOpened():
        raise ValueError(f"Could not open video writer for: {output_path}")

    print(f"Creating video: {output_path}")
    print(f"Reveal duration: {REVEAL_DURATION}s, Total duration: {TOTAL_DURATION}s")

    # Create frames
    white_canvas = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255

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

        # Overlay pencil cursor with alpha blending
        cursor_half = pencil_cursor_size // 2
        y1 = max(0, cursor_y - cursor_half)
        y2 = min(HEIGHT, cursor_y + cursor_half)
        x1 = max(0, cursor_x - cursor_half)
        x2 = min(WIDTH, cursor_x + cursor_half)

        # Adjust cursor region to match frame region
        cy1 = cursor_half - (cursor_y - y1)
        cy2 = cursor_half + (y2 - cursor_y)
        cx1 = cursor_half - (cursor_x - x1)
        cx2 = cursor_half + (x2 - cursor_x)

        cursor_region = pencil_cursor[cy1:cy2, cx1:cx2]
        if cursor_region.shape[0] > 0 and cursor_region.shape[1] > 0:
            alpha = cursor_region[:, :, 3:] / 255.0
            for c in range(3):
                frame[y1:y2, x1:x2, c] = (
                    alpha[:, :, 0] * cursor_region[:, :, c] +
                    (1 - alpha[:, :, 0]) * frame[y1:y2, x1:x2, c]
                )

        out.write(frame)

        # Progress indicator
        if frame_idx % 30 == 0:
            print(f"Progress: {frame_idx}/{reveal_frames} frames ({frame_idx*100//reveal_frames}%)")

    # Hold the final fully revealed image
    print("Adding hold frames with full image...")
    for _ in range(hold_frames):
        out.write(main_image)

    out.release()
    print(f"✓ Video created successfully: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python pencil_reveal.py <input_image> [hand_pencil_image] [output_video.mp4]")
        print("Example: python pencil_reveal.py image_1.png hand_pencil.png output.mp4")
        print("         python pencil_reveal.py image_1.png output.mp4  (uses default cursor)")
        sys.exit(1)

    input_image = Path(sys.argv[1])

    # Determine arguments
    if len(sys.argv) >= 3 and Path(sys.argv[2]).suffix.lower() in ['.png', '.jpg', '.jpeg']:
        # Hand pencil image provided
        hand_pencil_path = Path(sys.argv[2])
        output_video = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("pencil_reveal.mp4")
        use_custom_cursor = True
    else:
        # No hand pencil image
        hand_pencil_path = None
        output_video = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("pencil_reveal.mp4")
        use_custom_cursor = False

    if not input_image.exists():
        print(f"Error: Input image not found: {input_image}")
        sys.exit(1)

    # Load or create pencil cursor
    if use_custom_cursor and hand_pencil_path and hand_pencil_path.exists():
        print(f"Loading custom pencil cursor: {hand_pencil_path}")
        pencil_cursor = load_pencil_cursor(hand_pencil_path, PENCIL_SIZE)
        cursor_size = PENCIL_SIZE
    else:
        print("Creating default pencil cursor...")
        pencil_cursor = create_simple_pencil_cursor(PENCIL_SIZE)
        cursor_size = PENCIL_SIZE

    # Generate video
    create_reveal_video(input_image, output_video, pencil_cursor, cursor_size)

    print("\nConverting to H.264 (if ffmpeg available)...")
    temp_output = output_video.with_suffix('.tmp.mp4')
    import subprocess
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', str(output_video),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-pix_fmt', 'yuv420p', str(temp_output)
        ], check=True, capture_output=True)

        # Replace original with converted
        output_video.unlink()
        temp_output.rename(output_video)
        print(f"✓ Converted to H.264: {output_video}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: ffmpeg not found or failed. Video saved as mp4v codec.")
        if temp_output.exists():
            temp_output.unlink()

if __name__ == "__main__":
    main()
