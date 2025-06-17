import json
from functools import lru_cache
from typing import Any

import boto3
import cv2
import numpy as np
from aws_lambda_powertools import Logger

from .models import Metadata, Settings, SQSMessageBody

logger = Logger()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get settings from environment variables (cached)."""
    return Settings()


@lru_cache(maxsize=1)
def get_s3_client():
    """Initialize S3 client with settings from environment variables (cached)."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def run_calibration(metadata: Metadata, images: list[str]) -> None:
    s3 = get_s3_client()
    settings = get_settings()

    checkboard = (11, 7)

    # Termination criteria
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )

    # Prepare object points
    objp = np.zeros((checkboard[0] * checkboard[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : checkboard[0], 0 : checkboard[1]].T.reshape(
        -1, 2
    )

    # Arrays to store object points and image points from all images
    objpoints = []  # 3d points in real world space
    imgpoints = []  # 2d points in image plane
    gray = None  # Initialize to avoid potential unbound variable

    for image_name in images:
        logger.info(f"{metadata.dataset}/{image_name}")
        response = s3.get_object(
            Bucket=settings.r2_bucket, Key=f"{metadata.dataset}/{image_name}"
        )

        image_array = np.frombuffer(response["Body"].read(), np.uint8)

        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, checkboard, None)

        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria
            )
            imgpoints.append(corners2)

    ret, mtx, dist, _, _ = cv2.calibrateCamera(
        objpoints,
        imgpoints,
        gray.shape[::-1] if gray is not None else (0, 0),
        np.array([]),
        np.array([]),
    )

    result = {
        "camera_matrix": mtx.tolist(),
        "dist": dist.tolist(),
    }

    s3.put_object(
        Bucket=settings.r2_bucket,
        Key=f"{metadata.run_id}/metadata.json",
        Body=json.dumps(metadata.model_dump(), indent=4),
        ContentType="application/json",
    )

    s3.put_object(
        Bucket=settings.r2_bucket,
        Key=f"{metadata.run_id}/result.json",
        Body=json.dumps(result, indent=4),
        ContentType="application/json",
    )

    logger.info("Calibration finished")


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        msg: SQSMessageBody = SQSMessageBody.parse_raw(record["body"])
        metadata: Metadata = msg.metadata
        images: list[str] = msg.images

        logger.info(f"Number of images: {len(images)}")

        run_calibration(metadata, images)
