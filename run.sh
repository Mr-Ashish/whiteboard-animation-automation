#!/bin/bash

# Pencil Reveal Video Generator Script
# Usage: ./run.sh '{"images":[{"url":"...","seconds":5}],"audio":"https://...","ratio":"16:9","quality":"720p","captions":{...}}'
# Optional "captions": ElevenLabs timing-only payload with "text" and "alignment" (characters, character_start_times_seconds, character_end_times_seconds)

set -e

# Per-run temp dir: always removed on exit (success or failure)
TEMP_DIR=""
cleanup() {
    [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Remove any legacy temp files from previous runs (project root)
rm -f temp_config_*.json temp_captions_*.json 2>/dev/null || true

# Check if JSON input is provided
if [ -z "$1" ]; then
    echo "Error: Please provide JSON input"
    echo "Usage: ./run.sh '{\"images\":[{\"url\":\"...\",\"seconds\":5}],\"audio\":\"https://...\",\"ratio\":\"16:9\",\"quality\":\"720p\"}'"
    exit 1
fi

JSON_INPUT="$1"
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
echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); json.dump(data.get('images', []), sys.stdout)" > "$TEMP_CONFIG"

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

# Build command with default custom cursor
CMD="python pencil_reveal.py --multi $TEMP_CONFIG assets/hand_pencil.png"

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

# Run the pencil reveal script
echo "Generating video..."
eval $CMD

echo "Done! Video generated and uploaded"
