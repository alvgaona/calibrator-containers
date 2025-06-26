# Camera Calibration Service

A FastAPI-based service for computing camera intrinsic parameters from checkerboard pattern images. The service processes calibration requests and stores results in Cloudflare R2 storage.

## Features

- **Camera Calibration**: Compute intrinsic camera parameters (camera matrix and distortion coefficients) using OpenCV
- **Checkerboard Detection**: Automatic detection and sub-pixel refinement of checkerboard corners
- **RESTful API**: Standard HTTP endpoints with interactive documentation
- **Cloud Storage**: Integration with Cloudflare R2 for image input and result storage
- **Containerized**: Docker support for easy deployment
- **Type Safety**: Full type annotations with Pydantic models

## API Endpoints

### Health Check
- `GET /` - Root endpoint with service status
- `GET /health` - Health check endpoint

### Calibration
- `POST /calibrate` - Process camera calibration request

### Documentation
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - Alternative ReDoc documentation

## Quick Start

### Local Development

1. **Install dependencies** (requires [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync
   ```

2. **Set environment variables**:
   ```bash
   export R2_ENDPOINT_URL="https://your-account.r2.cloudflarestorage.com"
   export R2_ACCESS_KEY="your-access-key"
   export R2_SECRET_ACCESS_KEY="your-secret-key"
   export R2_BUCKET="your-bucket-name"
   ```

3. **Run the server**:
   ```bash
   uv run python -m calibrate.main
   ```

   Or with uvicorn directly:
   ```bash
   uv run uvicorn calibrate.main:app --reload
   ```

4. **Access the API**:
   - Service: http://localhost:8000
   - Documentation: http://localhost:8000/docs

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t calibrator-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 \
     -e R2_ENDPOINT_URL="https://your-account.r2.cloudflarestorage.com" \
     -e R2_ACCESS_KEY="your-access-key" \
     -e R2_SECRET_ACCESS_KEY="your-secret-key" \
     -e R2_BUCKET="your-bucket-name" \
     calibrator-api
   ```

## Usage Example

### Calibration Request

```bash
curl -X POST http://localhost:8000/calibrate \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "run_id": "calibration-2024-001",
      "dataset": "checkerboard-images",
      "checkerboard_size": [9, 6],
      "calibration_accuracy": 0.001,
      "iterations": 30
    },
    "images": [
      "image_001.jpg",
      "image_002.jpg",
      "image_003.jpg"
    ]
  }'
```

### Response

```json
{
  "status": "success",
  "message": "Calibration completed successfully",
  "run_id": "calibration-2024-001",
  "result": {
    "camera_matrix": [
      [1000.0, 0.0, 320.0],
      [0.0, 1000.0, 240.0],
      [0.0, 0.0, 1.0]
    ],
    "dist": [-0.2, 0.1, 0.0, 0.0, 0.0],
    "processed_images": 15,
    "total_images": 20
  }
}
```

## Configuration

The service is configured through environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `R2_ENDPOINT_URL` | Cloudflare R2 endpoint URL | Yes |
| `R2_ACCESS_KEY` | R2 access key | Yes |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key | Yes |
| `R2_BUCKET` | R2 bucket name for storage | Yes |

## Data Flow

1. **Input**: Calibration request with metadata and image filenames
2. **Processing**:
   - Download images from R2 storage
   - Detect checkerboard corners using OpenCV
   - Compute camera calibration parameters
3. **Output**:
   - Save results and metadata to R2 storage
   - Return calibration parameters in response

## Storage Structure

The service expects and creates the following R2 storage structure:

```
bucket/
├── {dataset}/                 # Input images
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
└── {run_id}/                  # Output results
    ├── metadata.json          # Original request metadata
    └── result.json            # Calibration results
```

## Development

### Requirements

- Python 3.11+
- uv package manager
- Docker (for containerized deployment)

### Code Quality

The project uses ruff for code formatting and linting:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

### Project Structure

```
calibrator-lambdas/
├── calibrate/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── models.py            # Pydantic models
├── Dockerfile               # Container configuration
├── pyproject.toml          # Project dependencies
├── uv.lock                 # Locked dependencies
└── README.md               # This file
```

## Dependencies

### Core
- **FastAPI**: Web framework for building APIs
- **uvicorn**: ASGI server for FastAPI
- **OpenCV**: Computer vision library for calibration
- **NumPy**: Numerical computing
- **Pydantic**: Data validation and settings

### Cloud Integration
- **boto3**: AWS SDK for R2 storage integration

### Development
- **ruff**: Code formatting and linting

## Algorithm Details

The service uses OpenCV's `calibrateCamera` function to compute:

- **Camera Matrix**: 3x3 intrinsic parameter matrix containing focal lengths and principal point
- **Distortion Coefficients**: Lens distortion parameters (radial and tangential)

The calibration process:

1. **Corner Detection**: Find checkerboard corners in each image
2. **Sub-pixel Refinement**: Improve corner accuracy using `cornerSubPix`
3. **3D-2D Correspondence**: Match world coordinates to image coordinates
4. **Optimization**: Minimize reprojection error to find optimal parameters

## License

See LICENSE files for licensing information.
