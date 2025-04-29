#!/bin/bash
set -e

# This script serves as the entrypoint for the telert Docker image.
# It supports two modes of operation:
# 1. CLI mode - runs telert commands directly (default)
# 2. Server mode - starts a FastAPI server for receiving notification requests

# If the first argument is "serve", run in server mode
if [ "$1" = "serve" ]; then
  echo "Starting Telert Server on port 8000..."
  exec uvicorn server:app --host 0.0.0.0 --port 8000
else
  # Otherwise, run telert with the provided arguments
  exec telert "$@"
fi