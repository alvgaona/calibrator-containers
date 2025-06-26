#!/bin/bash

# Build script for calibrate service Docker image
# This script should be run from the calibrate package directory

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to workspace root (two levels up from packages/calibrate/)
WORKSPACE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Building calibrate Docker image from workspace root: $WORKSPACE_ROOT"

# Change to workspace root directory
cd "$WORKSPACE_ROOT"

# Build the Docker image using the Dockerfile in packages/calibrate/
docker build \
    -f packages/calibrate/Dockerfile \
    -t calibrate:latest \
    .

echo "Docker image 'calibrate:latest' built successfully!"
echo "To run the container:"
echo "  docker run -p 8000:8000 calibrate:latest"
