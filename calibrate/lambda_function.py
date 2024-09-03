import json
import os

import boto3
import cv2
import numpy as np
from aws_lambda_powertools import Logger

R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET")


s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
)

logger = Logger()


def run_calibration(metadata, images) -> None:
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

    for image_name in images:
        logger.info(f'{metadata["dataset"]}/{image_name}')
        response = s3.get_object(
            Bucket=R2_BUCKET, Key=f'{metadata["dataset"]}/{image_name}'
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
        gray.shape[::-1],  # type: ignore[reportPossiblyUnboundVariable]
        np.array([]),
        np.array([]),
    )

    result = {
        "camera_matrix": mtx.tolist(),
        "dist": dist.tolist(),
    }

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=f'{metadata["run_id"]}/metadata.json',
        Body=json.dumps(metadata, indent=4),
        ContentType="application/json",
    )

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=f'{metadata["run_id"]}/result.json',
        Body=json.dumps(result, indent=4),
        ContentType="application/json",
    )

    logger.info("Calibration finished")


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        metadata = message["metadata"]
        images = message["images"]

        logger.info(f"Number of images: {len(images)}")

        run_calibration(metadata, images)
