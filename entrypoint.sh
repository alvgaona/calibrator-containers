#!/bin/bash

# Activate the uv virtual environment
export PATH="/app/.venv/bin:$PATH"

# Start the FastAPI server with uvicorn
exec uvicorn calibrate.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
