import json
import logging
from functools import lru_cache
from typing import Any

import boto3
import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .models import Metadata, Settings, SQSMessageBody

# Initialize logger for tracking execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Camera Calibration API",
    description="API for performing camera calibration using checkerboard images",
    version="0.0.1",
)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get settings from environment variables (cached)."""
    return Settings()


@lru_cache(maxsize=1)
def get_s3_client():
    """Initialize S3 client with settings from environment variables (cached)."""
    settings = get_settings()
    # Create S3 client configured for Cloudflare R2 storage
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def run_calibration(metadata: Metadata, images: list[str]) -> dict[str, Any]:
    """
    Perform camera calibration using checkerboard images.

    This function processes a set of checkerboard images to compute camera intrinsic
    parameters (camera matrix and distortion coefficients) using OpenCV's calibration
    algorithms.

    Returns the calibration results as a dictionary.
    """
    s3 = get_s3_client()
    settings = get_settings()

    # Extract checkerboard dimensions from metadata
    width, height = metadata.checkerboard_size

    # Termination criteria for corner refinement algorithm
    # Stops when either accuracy (default 0.001) or max iterations (default 30) is reached
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        metadata.iterations,
        metadata.calibration_accuracy,
    )

    # Prepare object points - 3D coordinates of checkerboard corners in world space
    # Assumes checkerboard is in XY plane (Z=0) with unit square size
    objp = np.zeros((width * height, 3), np.float32)
    objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2)

    # Arrays to store object points and image points from all images
    objpoints = []  # 3d points in real world space
    imgpoints = []  # 2d points in image plane
    gray = None  # Initialize to avoid potential unbound variable

    # Process each calibration image
    for image_name in images:
        logger.info(f"Processing image: {metadata.dataset}/{image_name}")

        try:
            # Download image from S3/R2 storage
            response = s3.get_object(
                Bucket=settings.r2_bucket,
                Key=f"{metadata.dataset}/{image_name}",
            )

            # Convert downloaded bytes to numpy array
            image_array = np.frombuffer(response["Body"].read(), np.uint8)

            # Decode image array to OpenCV format
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if img is None:
                logger.warning(f"Could not decode image: {image_name}")
                continue

            # Convert to grayscale for corner detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(
                gray, (width, height), None
            )

            # If corners found successfully
            if ret:
                # Add corresponding 3D object points
                objpoints.append(objp)
                # Refine corner positions to sub-pixel accuracy
                corners2 = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1), criteria
                )
                # Add refined 2D image points
                imgpoints.append(corners2)
            else:
                logger.warning(
                    f"No checkerboard corners found in image: {image_name}"
                )

        except Exception as e:
            logger.error(f"Error processing image {image_name}: {str(e)}")
            continue

    if not objpoints or not imgpoints:
        raise ValueError("No valid checkerboard images found for calibration")

    if gray is None:
        raise ValueError("No images were successfully processed")

    # Perform camera calibration using collected point correspondences
    # Returns: success flag, camera matrix, distortion coefficients, rotation/translation vectors
    ret, mtx, dist, _, _ = cv2.calibrateCamera(
        objpoints,
        imgpoints,
        gray.shape[::-1],  # Image size (width, height)
        np.array([]),  # Initial camera matrix estimate (empty = auto)
        np.array([]),  # Initial distortion coefficients (empty = auto)
    )

    if not ret:
        raise ValueError("Camera calibration failed")

    # Prepare calibration results for storage
    result = {
        "camera_matrix": mtx.tolist(),  # 3x3 intrinsic camera matrix
        "dist": dist.tolist(),  # Distortion coefficients
        "processed_images": len(objpoints),
        "total_images": len(images),
    }

    # Save metadata to S3/R2 storage
    s3.put_object(
        Bucket=settings.r2_bucket,
        Key=f"{metadata.run_id}/metadata.json",
        Body=json.dumps(metadata.model_dump(), indent=4),
        ContentType="application/json",
    )

    # Save calibration results to S3/R2 storage
    s3.put_object(
        Bucket=settings.r2_bucket,
        Key=f"{metadata.run_id}/result.json",
        Body=json.dumps(result, indent=4),
        ContentType="application/json",
    )

    logger.info("Calibration finished")
    return result


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Camera Calibration API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/calibrate")
async def calibrate(request: SQSMessageBody):
    """
    Perform camera calibration using provided metadata and image list.

    Args:
        request: SQSMessageBody containing metadata and list of image names

    Returns:
        JSONResponse with calibration results
    """
    try:
        metadata = request.metadata
        images = request.images

        logger.info(f"Starting calibration for run_id: {metadata.run_id}")
        logger.info(f"Number of images: {len(images)}")
        logger.info(f"Dataset: {metadata.dataset}")
        logger.info(f"Checkerboard size: {metadata.checkerboard_size}")

        # Run the camera calibration process
        result = run_calibration(metadata, images)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Calibration completed successfully",
                "run_id": metadata.run_id,
                "result": result,
            },
        )

    except ValueError as e:
        logger.error(f"Calibration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during calibration: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during calibration"
        )


@app.get("/calibrate/{run_id}")
async def get_calibration_result(run_id: str):
    """
    Retrieve calibration results for a specific run ID.

    Args:
        run_id: The run ID to retrieve results for

    Returns:
        JSONResponse with calibration results
    """
    try:
        s3 = get_s3_client()
        settings = get_settings()

        # Try to get the result file from S3
        try:
            response = s3.get_object(
                Bucket=settings.r2_bucket, Key=f"{run_id}/result.json"
            )
            result = json.loads(response["Body"].read().decode())

            # Also get metadata if available
            try:
                metadata_response = s3.get_object(
                    Bucket=settings.r2_bucket, Key=f"{run_id}/metadata.json"
                )
                metadata = json.loads(metadata_response["Body"].read().decode())
            except:
                metadata = None

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "run_id": run_id,
                    "result": result,
                    "metadata": metadata,
                },
            )

        except s3.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail=f"Calibration results not found for run_id: {run_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving calibration results: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(
        "calibrate.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
