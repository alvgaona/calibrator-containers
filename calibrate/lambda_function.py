import json
from functools import lru_cache
from typing import Any

import boto3
import cv2
import numpy as np
from aws_lambda_powertools import Logger

from .models import Metadata, Settings, SQSMessageBody

# Initialize logger for tracking execution
logger = Logger()


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


def run_calibration(metadata: Metadata, images: list[str]) -> None:
    """
    Perform camera calibration using checkerboard images.

    This function processes a set of checkerboard images to compute camera intrinsic
    parameters (camera matrix and distortion coefficients) using OpenCV's calibration
    algorithms.
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

        # Download image from S3/R2 storage
        response = s3.get_object(
            Bucket=settings.r2_bucket, Key=f"{metadata.dataset}/{image_name}"
        )

        # Convert downloaded bytes to numpy array
        image_array = np.frombuffer(response["Body"].read(), np.uint8)

        # Decode image array to OpenCV format
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Convert to grayscale for corner detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (width, height), None)

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

    # Perform camera calibration using collected point correspondences
    # Returns: success flag, camera matrix, distortion coefficients, rotation/translation vectors
    ret, mtx, dist, _, _ = cv2.calibrateCamera(
        objpoints,
        imgpoints,
        gray.shape[::-1]
        if gray is not None
        else (0, 0),  # Image size (width, height)
        np.array([]),  # Initial camera matrix estimate (empty = auto)
        np.array([]),  # Initial distortion coefficients (empty = auto)
    )

    # Prepare calibration results for storage
    result = {
        "camera_matrix": mtx.tolist(),  # 3x3 intrinsic camera matrix
        "dist": dist.tolist(),  # Distortion coefficients
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


def handler(event: dict[str, Any], context: Any) -> None:
    """
    AWS Lambda handler function for processing SQS messages containing calibration requests.

    Each SQS message contains metadata and a list of image names to process for calibration.
    """
    # Process each SQS record in the event
    for record in event["Records"]:
        # Parse the SQS message body into structured data
        msg: SQSMessageBody = SQSMessageBody.model_validate_json(record["body"])
        metadata: Metadata = msg.metadata
        images: list[str] = msg.images

        logger.info(f"Number of images: {len(images)}")

        # Run the camera calibration process
        run_calibration(metadata, images)
