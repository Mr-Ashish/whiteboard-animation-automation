# Pencil Reveal Animation

Create diagonal zig-zag pencil drawing reveal animations for images. Supports both single image and multi-image modes with local files or image URLs. Features automatic cleanup of temporary files with organized project structure.

## Project Structure

```
python-video/
├── src/                    # Source modules
│   ├── config.py          # Configuration constants
│   ├── cursor_utils.py    # Cursor/pencil creation
│   ├── download_utils.py  # URL download handling
│   ├── image_utils.py     # Image loading/processing
│   ├── path_generator.py  # Zig-zag path generation
│   ├── animation.py       # Reveal animation logic
│   ├── video_writer.py    # Video creation/stitching
│   └── cleanup_utils.py   # Temporary file cleanup
├── assets/                # Sample images and cursors
│   ├── hand_pencil.png    # Custom pencil cursor
│   └── image_3.png        # Sample image
├── output/                # Generated videos (auto-created)
├── temp/                  # Temporary files (auto-cleaned)
├── pencil_reveal.py       # Main entry point
└── requirements.txt       # Dependencies
```

## Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Single Image Mode

Create a reveal animation for a single image (local file or URL):

```bash
# Using local file with default pencil cursor
python pencil_reveal.py image.png output.mp4

# Using image URL with default pencil cursor
python pencil_reveal.py https://example.com/image.jpg output.mp4

# Using custom pencil cursor
python pencil_reveal.py image.png hand_pencil.png output.mp4
```

**Arguments:**
- `image.png` or `https://...` - Input image file path or URL
- `hand_pencil.png` - (Optional) Custom pencil cursor image
- `output.mp4` - (Optional) Output video filename (saved to `output/` directory, default: pencil_reveal.mp4)

**Note:** Videos are automatically saved to the `output/` directory. Temporary files (downloaded images) are automatically cleaned up after generation.

### Multi-Image Mode

Create a video with multiple image reveals stitched together:

```bash
# Using default pencil cursor
python pencil_reveal.py --multi config.json output.mp4

# Using custom pencil cursor
python pencil_reveal.py --multi config.json hand_pencil.png output.mp4
```

**Config JSON Format:**

Create a JSON file (e.g., `config.json`) with an array of image configurations. Mix local files and URLs as needed:

```json
[
  {"image": "image_1.png", "seconds": 5},
  {"image": "https://example.com/image_2.jpg", "seconds": 3},
  {"image": "image_3.png", "seconds": 4}
]
```

Each object requires:
- `image` - Path to the image file or image URL
- `seconds` - Total duration for this image (reveal + hold time)

**Arguments:**
- `config.json` - JSON config file with image array
- `hand_pencil.png` - (Optional) Custom pencil cursor image
- `output.mp4` - (Optional) Output video filename (saved to `output/` directory, default: multi_reveal.mp4)

## Features

- **URL Support**: Download images directly from URLs
- **Auto Cleanup**: Temporary files are automatically removed after video generation
- **Organized Output**: All videos saved to `output/` directory
- **Modular Structure**: Clean separation of concerns in `src/` folder
- **Mix Sources**: Combine local files and URLs in multi-image mode

## Configuration

Edit `src/config.py` to customize:
- Video dimensions (WIDTH, HEIGHT)
- Frame rate (FPS)
- Animation durations
- Zig-zag amplitude and angle
- Cursor size
- Output and temp directory paths

## Examples

```bash
# Basic single image (local file) - outputs to output/my_video.mp4
python pencil_reveal.py assets/image_3.png my_video.mp4

# Single image from URL - automatically downloads, generates video, cleans up
python pencil_reveal.py https://picsum.photos/1080/1920 my_video.mp4

# Single image with custom cursor from assets
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png my_video.mp4

# Multiple images stitched together (mix of local and URLs)
python pencil_reveal.py --multi images_config.json final_video.mp4

# Multiple images with custom cursor from assets
python pencil_reveal.py --multi images_config.json assets/hand_pencil.png final_video.mp4
```

**Output Location:** All videos are saved to `output/` directory. After generation, you'll see:
```
✓ Video created successfully: /path/to/output/my_video.mp4
✓ Cleanup complete - all temporary files removed
```

### Example config.json with URLs

```json
[
  {"image": "assets/image_3.png", "seconds": 5},
  {"image": "https://picsum.photos/id/237/1080/1920", "seconds": 4},
  {"image": "https://picsum.photos/id/238/1080/1920", "seconds": 3}
]
```

**Quick Test:** Try the included sample assets:
```bash
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png test.mp4
```

## Reference

For a more organic sketch maker, check out:
https://github.com/yogendra-yatnalkar/storyboard-ai/blob/main/generate-whiteboard-animated-videos/draw-whiteboard-animations.py
