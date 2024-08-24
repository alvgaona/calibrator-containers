from typing import Any, Dict, List, TypedDict

import cv2
import numpy as np
import requests
from cv2.typing import MatLike
from flask import Flask, jsonify, request

app = Flask(__name__)


class Blob(TypedDict):
    url: str
    downloadUrl: str
    pathName: str
    size: float
    uploadedAt: str


@app.route("/calibrate", methods=["POST"])
async def calibrate():
    data: Dict[str, Any] | None = request.json

    if not data:
        raise RuntimeError("NONONONO")

    blobs: List[Blob] = data.get("blobs", [])

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
    objpoints: list[MatLike] = []  # 3d points in real world space
    imgpoints: list[MatLike] = []  # 2d points in image plane

    for blob in blobs:
        response = requests.get(blob["downloadUrl"])
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

    return jsonify({"camera_matrix": mtx.tolist(), "dist": dist.tolist()})
