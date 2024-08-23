import glob
from typing import Tuple

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray

# Define square size in meters
SQUARE_SIZE: float = 0.30

# Define the dimensions of checkerboard
CHECKERBOARD: Tuple[int, int] = (11, 7)

# Termination criteria
criteria: Tuple[int, int, float] = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    30,
    0.001,
)

# Prepare object points
objp: NDArray[np.float32] = np.zeros(
    (CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32
)
objp[:, :2] = np.mgrid[0 : CHECKERBOARD[0], 0 : CHECKERBOARD[1]].T.reshape(
    -1, 2
)

# Arrays to store object points and image points from all images
objpoints: list[MatLike] = []  # 3d points in real world space
imgpoints: list[MatLike] = []  # 2d points in image plane

# Get list of calibration images
images = glob.glob("calibration_images/leftcamera/*.png")

if not images:
    print("No images have been found at given directory.")
    exit(1)

for fname in images:
    img = cv2.imread(fname)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
        cv2.imshow("img", img)
        cv2.waitKey(500)

# Calibration
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
    objpoints,
    imgpoints,
    gray.shape[::-1],  # type: ignore[reportPossiblyUnboundVariable]
    np.array([]),
    np.array([]),
)

# Print camera matrix and distortion coefficients
print("Camera matrix:")
print(mtx)
print("\nDistortion coefficients:")
print(dist)

# Save the camera calibration results
np.savez("camera_calibration.npz", mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)

print("Calibration completed. Results saved to 'camera_calibration.npz'")
