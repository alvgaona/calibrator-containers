from typing import List

import logging
import json
import httpx
import cv2
import numpy as np


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_calibration(blobs) -> None:
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

    for blob in blobs:
        response = httpx.get(blob["download_url"])
        response.raise_for_status()

        image_array = np.frombuffer(response.content, np.uint8)

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

    logger.info(f"mtx={mtx.tolist()}")
    logger.info(f"mtx={dist.tolist()}")


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        blobs = message["blobs"]

        context.log(f"Number of received blobs: {len(blobs)}")

        run_calibration(blobs)
