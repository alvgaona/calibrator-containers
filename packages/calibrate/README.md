# Calibrate Package

A camera calibration service for computing intrinsic parameters from checkerboard pattern images.

## Overview

The calibrate package provides a FastAPI-based web service that performs camera calibration using OpenCV. It processes images containing checkerboard patterns to compute camera intrinsic parameters such as focal length, principal point, and distortion coefficients.

## Features

- FastAPI web service for camera calibration
- Checkerboard pattern detection using OpenCV
- Camera intrinsic parameter computation
- RESTful API endpoints
- Docker containerization support
- AWS integration with boto3

## Dependencies

- Python >=3.11.13,<3.14
- FastAPI >=0.104.0,<1.0
- OpenCV >=4.10.0,<4.11
- NumPy >=2.1.0,<2.2
- Pydantic >=2.11.7,<3
- boto3 (for AWS integration)

## Development Setup

This package is part of a uv workspace. From the workspace root:

```bash
# Install all dependencies
uv sync

# Run the calibrate service
uv run --package calibrate uvicorn calibrate.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific Python version
uv run --package calibrate python -m uvicorn calibrate.main:app --reload
```

## API Endpoints

The service provides the following endpoints:

- `GET /`: Health check endpoint
- `POST /calibrate`: Camera calibration endpoint (accepts image data)

## Docker Usage

### Building the Image

Use the provided build script:

```bash
# From the calibrate package directory
./build.sh
```

Or build manually from the workspace root:

```bash
# From workspace root
docker build -f packages/calibrate/Dockerfile -t calibrate:latest .
```

### Running the Container

```bash
# Run the service on port 8000
docker run -p 8000:8000 calibrate:latest

# Run with environment variables
docker run -p 8000:8000 -e ENV_VAR=value calibrate:latest
```

## Project Structure

```
calibrate/
├── calibrate/           # Python package
│   ├── __init__.py
│   ├── main.py         # FastAPI application
│   └── models.py       # Pydantic models
├── pyproject.toml      # Package configuration
├── Dockerfile          # Container definition
├── build.sh           # Docker build script
└── README.md          # This file
```

## Usage Example

```python
import requests

# Send calibration request
response = requests.post(
    "http://localhost:8000/calibrate",
    files={"images": open("checkerboard.jpg", "rb")}
)

calibration_data = response.json()
print(f"Camera matrix: {calibration_data['camera_matrix']}")
```

## Development

### Running Tests

```bash
# From workspace root
uv run --package calibrate pytest
```

### Linting

```bash
# From workspace root
uv run --package calibrate ruff check .
uv run --package calibrate ruff format .
```

### Type Checking

```bash
# From workspace root
uv run --package calibrate pyright
```

## Environment Variables

The service can be configured using environment variables:

- `PORT`: Service port (default: 8000)
- `HOST`: Service host (default: 0.0.0.0)
- `AWS_REGION`: AWS region for boto3 client
- `LOG_LEVEL`: Logging level (default: INFO)

## License

This project is dual-licensed under AGPL-3.0 and GPL-3.0. See the LICENSE files in the workspace root for details.
