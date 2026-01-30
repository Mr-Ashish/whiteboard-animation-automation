#!/bin/bash
# Run a test video using test_payload.json (pencil reveal with images, audio, captions).
# Usage: ./run_test.sh
#        ./run_test.sh pan_zoom   # use pan-zoom instead of pencil reveal

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PAYLOAD_FILE="${SCRIPT_DIR}/test_payload.json"
if [ ! -f "$PAYLOAD_FILE" ]; then
    echo "Error: test_payload.json not found at $PAYLOAD_FILE"
    exit 1
fi

# Read payload (single line for safe passing)
JSON_INPUT=$(cat "$PAYLOAD_FILE")

if [ "$1" = "pan_zoom" ]; then
    echo "Running pan-zoom test..."
    ./run_pan_zoom.sh "$JSON_INPUT"
else
    echo "Running pencil reveal test..."
    ./run.sh "$JSON_INPUT"
fi

echo "Test complete. Check output/ for the generated video."
