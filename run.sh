#!/bin/bash

# Pencil Reveal Video Generator Script
# Usage: ./run.sh '{"images":[{"url":"...","seconds":5}],"audio":"https://..."}'

set -e

# Check if JSON input is provided
if [ -z "$1" ]; then
    echo "Error: Please provide JSON input"
    echo "Usage: ./run.sh '{\"images\":[{\"url\":\"...\",\"seconds\":5}],\"audio\":\"https://...\"}'"
    exit 1
fi

JSON_INPUT="$1"
TEMP_CONFIG="temp_config_$$.json"
OUTPUT_FILE="output.mp4"

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

# Extract audio URL if present
AUDIO_URL=$(echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('audio', ''))" 2>/dev/null || echo "")

# Create temporary config file with images array
echo "$JSON_INPUT" | python -c "import sys, json; data=json.load(sys.stdin); json.dump(data.get('images', []), sys.stdout)" > "$TEMP_CONFIG"

# Build command
CMD="python pencil_reveal.py --multi $TEMP_CONFIG"

if [ ! -z "$AUDIO_URL" ]; then
    CMD="$CMD --audio $AUDIO_URL"
fi

CMD="$CMD --upload $OUTPUT_FILE"

# Run the pencil reveal script
echo "Generating video..."
eval $CMD

# Cleanup temporary config
rm -f "$TEMP_CONFIG"

echo "Done! Video generated and uploaded"
