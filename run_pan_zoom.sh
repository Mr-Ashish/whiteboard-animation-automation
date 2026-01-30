#!/bin/bash

# Pan-Zoom Video Generator Script
# Usage: ./run_pan_zoom.sh <payload.json>
# Example: ./run_pan_zoom.sh test_payload.json
# Payload file (in project root) must contain: images, optional audio, ratio, quality, captions.

set -e

# Per-run temp dir: always removed on exit (success or failure)
TEMP_DIR=""
cleanup() {
    [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove any legacy temp files from previous runs (project root)
rm -f temp_pan_zoom_config_*.json temp_captions_pan_*.json 2>/dev/null || true

# First argument is payload JSON filename (in project root)
if [ -z "$1" ]; then
    echo "Error: Please provide payload file path"
    echo "Usage: ./run_pan_zoom.sh <payload.json>"
    echo "Example: ./run_pan_zoom.sh test_payload.json"
    exit 1
fi

PAYLOAD_FILE="$1"
[ "${PAYLOAD_FILE#/}" = "$PAYLOAD_FILE" ] && PAYLOAD_FILE="${SCRIPT_DIR}/${PAYLOAD_FILE}"
if [ ! -f "$PAYLOAD_FILE" ]; then
    echo "Error: Payload file not found: $1"
    exit 1
fi

JSON_INPUT=$(cat "$PAYLOAD_FILE")
TEMP_DIR="temp/run_$$"
mkdir -p "$TEMP_DIR"
TEMP_CONFIG="$TEMP_DIR/config.json"
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

# Extract captions (text + alignment / timing-only payload) if present
TEMP_CAPTIONS="$TEMP_DIR/captions.json"
CAPTIONS_FILE=""
if echo "$JSON_INPUT" | python -c "
import sys, json
d = json.load(sys.stdin)
c = d.get('captions')
if c is not None:
    json.dump(c, sys.stdout)
else:
    sys.exit(1)
" > "$TEMP_CAPTIONS" 2>/dev/null; then
    CAPTIONS_FILE="$TEMP_CAPTIONS"
fi

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

if [ -n "$CAPTIONS_FILE" ]; then
    CMD="$CMD --captions $CAPTIONS_FILE"
fi

CMD="$CMD --upload"

# Run the pan-zoom script
echo "Generating pan-zoom video..."
eval $CMD

echo "Done! Pan-zoom video generated and uploaded"
