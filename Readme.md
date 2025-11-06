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
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Quick Start with Shell Script

For a quick one-command execution, use the provided shell script with JSON input:

```bash
# Basic usage
./run.sh '{"images":[{"url":"https://example.com/image1.jpg","seconds":5},{"url":"https://example.com/image2.jpg","seconds":3}],"audio":"https://example.com/music.mp3"}'

# Without audio
./run.sh '{"images":[{"url":"https://example.com/image1.jpg","seconds":5}]}'
```

The script will:
- Create and activate virtual environment automatically
- Install dependencies if needed
- Generate video from provided JSON
- Upload to S3 (requires `.env` configuration)
- Clean up temporary files

### AWS S3 Upload Setup (Optional)

If you want to upload videos to AWS S3:

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your AWS credentials:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
```

3. Ensure your S3 bucket exists and has appropriate permissions

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
- **Background Music**: Add looping background music to videos (mp3, wav, etc.)
- **AWS S3 Upload**: Automatically upload videos to S3 and get public URLs
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

### Basic Usage

```bash
# Basic single image (local file) - outputs to output/my_video.mp4
python pencil_reveal.py assets/image_3.png my_video.mp4

# Single image from URL - automatically downloads, generates video, cleans up
python pencil_reveal.py https://picsum.photos/1080/1920 my_video.mp4

# Single image with custom cursor from assets
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png my_video.mp4
```

### With Background Music

```bash
# Add background music from local file
python pencil_reveal.py assets/image_3.png --audio music.mp3 output.mp4

# Add background music from URL
python pencil_reveal.py assets/image_3.png --audio https://example.com/music.mp3 output.mp4

# Add background music with custom volume (50%)
python pencil_reveal.py assets/image_3.png --audio music.wav --volume 0.5 output.mp4

# Multi-image with background music from URL
python pencil_reveal.py --multi config.json --audio https://example.com/background.mp3 final.mp4

# Full example with all options (local audio)
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png --audio music.mp3 --volume 0.7 my_video.mp4

# Full example with audio URL
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png --audio https://example.com/music.mp3 --volume 0.7 my_video.mp4
```

### Multi-Image Mode

```bash
# Multiple images stitched together (mix of local and URLs)
python pencil_reveal.py --multi images_config.json final_video.mp4

# Multiple images with custom cursor and audio
python pencil_reveal.py --multi config.json assets/hand_pencil.png --audio music.mp3 final_video.mp4
```

### With AWS S3 Upload

```bash
# Upload video to S3 (requires .env configuration)
python pencil_reveal.py assets/image_3.png --upload my_video.mp4

# Upload with background music (local file)
python pencil_reveal.py assets/image_3.png --audio music.mp3 --upload output.mp4

# Upload with background music from URL
python pencil_reveal.py assets/image_3.png --audio https://example.com/music.mp3 --upload output.mp4

# Multi-image with audio URL and S3 upload
python pencil_reveal.py --multi config.json --audio https://example.com/music.mp3 --upload final.mp4

# All features combined with local audio
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png --audio music.mp3 --volume 0.7 --upload my_video.mp4

# All features combined with audio URL
python pencil_reveal.py assets/image_3.png assets/hand_pencil.png --audio https://example.com/music.mp3 --volume 0.7 --upload my_video.mp4
```

**With `--upload` flag:**
- Video is saved locally in `output/` directory
- Video is uploaded to your configured S3 bucket
- Public S3 URL is displayed:
  ```
  ============================================================
  S3 URL: https://your-bucket.s3.us-east-1.amazonaws.com/my_video.mp4
  ============================================================
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

## Terminal-Only Method (Using FFmpeg Directly)

If you prefer to add audio manually using terminal commands:

```bash
# First, generate video without audio
python pencil_reveal.py assets/image_3.png my_video.mp4

# Then add background music using ffmpeg
ffmpeg -i output/my_video.mp4 -stream_loop -1 -i music.mp3 \
  -c:v copy -filter:a 'volume=1.0' -shortest \
  -map 0:v:0 -map 1:a:0 output/my_video_with_music.mp4
```

**FFmpeg Options:**
- `-stream_loop -1`: Loop audio indefinitely
- `-c:v copy`: Copy video without re-encoding (fast)
- `-filter:a 'volume=0.5'`: Adjust volume (0.0 to 1.0)
- `-shortest`: Stop when video ends
- `-map 0:v:0 -map 1:a:0`: Map video from first input, audio from second

## Reference

For a more organic sketch maker, check out:
https://github.com/yogendra-yatnalkar/storyboard-ai/blob/main/generate-whiteboard-animated-videos/draw-whiteboard-animations.py
