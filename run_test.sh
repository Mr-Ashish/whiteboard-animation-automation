#!/bin/bash
# Run a test video using a payload JSON file (default: test_payload.json).
# Usage: ./run_test.sh
#        ./run_test.sh pan_zoom
#        ./run_test.sh sample.json
#        ./run_test.sh sample.json pan_zoom

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PAYLOAD_FILE="test_payload.json"
MODE="run"
if [ "$1" = "pan_zoom" ]; then
    MODE="pan_zoom"
elif [ -n "$1" ]; then
    PAYLOAD_FILE="$1"
    [ "$2" = "pan_zoom" ] && MODE="pan_zoom"
fi

if [ "$MODE" = "pan_zoom" ]; then
    echo "Running pan-zoom test with $PAYLOAD_FILE..."
    ./run_pan_zoom.sh "$PAYLOAD_FILE"
else
    echo "Running pencil reveal test with $PAYLOAD_FILE..."
    ./run.sh "$PAYLOAD_FILE"
fi

echo "Test complete. Check output/ for the generated video."
