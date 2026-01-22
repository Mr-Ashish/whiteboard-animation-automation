#!/bin/bash

# Pan-Zoom Video Generator Script
# Usage: ./run_pan_zoom.sh '{"images":[{"image":"...","seconds":5}],"audio":"https://...","ratio":"16:9","quality":"720p"}'

set -e

# Check if JSON input is provided
if [ -z "$1" ]; then
    echo "Error: Please provide JSON input"
    echo "Usage: ./run_pan_zoom.sh '{\"images\":[{\"image\":\"...\",\"seconds\":5}],\"audio\":\"https://...\",\"ratio\":\"16:9\",\"quality\":\"720p\"}'"
    exit 1
fi

JSON_INPUT="$1"
TEMP_CONFIG="temp_pan_zoom_config_$$.json"
# Don't specify output file - let Python generate UUID
OUTPUT_FILE=""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import cv2" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Extract parameters from JSON
AUDIO_URL=$(echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('audio', ''))" 2>/dev/null || echo "")
RATIO=$(echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('ratio', ''))" 2>/dev/null || echo "")
QUALITY=$(echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('quality', ''))" 2>/dev/null || echo "")

# Create temporary config file with images array
# Support both 'image' and 'url' keys in the JSON
echo "$JSON_INPUT" | python -c "
import sys, json
data = json.load(sys.stdin)
images = data.get('images', [])
# Convert 'url' to 'image' if needed for compatibility
for img in images:
    if 'url' in img and 'image' not in img:
        img['image'] = img.pop('url')
json.dump(images, sys.stdout)
" > "$TEMP_CONFIG"

# Build command for pan-zoom script
CMD="python pan_zoom.py $TEMP_CONFIG"

if [ ! -z "$AUDIO_URL" ]; then
    CMD="$CMD --audio $AUDIO_URL"
fi

if [ ! -z "$RATIO" ]; then
    CMD="$CMD --ratio $RATIO"
fi

if [ ! -z "$QUALITY" ]; then
    CMD="$CMD --quality $QUALITY"
fi

CMD="$CMD --upload"

# Run the pan-zoom script
echo "Generating pan-zoom video..."
eval $CMD

# Cleanup temporary config
rm -f "$TEMP_CONFIG"

echo "Done! Pan-zoom video generated and uploaded"
