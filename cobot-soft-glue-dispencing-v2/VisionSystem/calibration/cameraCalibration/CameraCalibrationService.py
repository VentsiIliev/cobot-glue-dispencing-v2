import os
from API.MessageBroker import MessageBroker

import cv2
import numpy as np
from src.plvision.PLVision import ImageProcessing
from src.plvision.PLVision.Calibration import CameraCalibrator
import cv2.aruco as aruco


class CameraCalibrationService:
    STORAGE_PATH = "VisionSystem/calibration/cameraCalibration/storage/calibration_result"
    PERSPECTIVE_MATRIX_PATH = STORAGE_PATH + "/perspectiveTransform.npy"
    CAMERA_TO_ROBOT_MATRIX_PATH = STORAGE_PATH + "/cameraToRobotMatrix.npy"

    def __init__(self, chessboardWidth, chessboardHeight, squareSizeMM, skipFrames,onDetectionFailed=None, storagePath=None):
        if storagePath is not None:
            self.STORAGE_PATH = storagePath
        self.calibrationImages = []
        self.chessboardWidth = chessboardWidth
        self.chessboardHeight = chessboardHeight
        self.squareSizeMM = squareSizeMM
        self.skipFrames = skipFrames
        self.onDetectionFailed = onDetectionFailed
        self.cameraCalibrator = CameraCalibrator(self.chessboardWidth, self.chessboardHeight, self.squareSizeMM)
        self.topic = "vision-system/calibration-feedback"
        self.messageBroker = MessageBroker()

    def detectArucoMarkers(self, flip=False, image=None):
        """
        Detects ArUco markers in the provided image.
        Returns corners, ids, and the (possibly flipped) image.
        """
        if image is None:
            print("No image provided for ArUco detection.")
            return None, None, None

        if flip:
            image = cv2.flip(image, 1)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
        parameters = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(dictionary, parameters)

        try:
            corners, ids, _ = detector.detectMarkers(gray)
            if ids is not None:
                print(f"✅ Detected ArUco IDs: {ids.flatten()}")
            else:
                print("❌ No ArUco markers detected")
            return corners, ids, image
        except Exception as e:
            print(f"❌ ArUco Detection failed: {e}")
            return None, None, image

    def run(self, image, debug=True):
        """
        Main calibration workflow.
        Returns (success, calibrationData, perspectiveMatrix, message)
        """
        message = ""

        if not self.calibrationImages or len(self.calibrationImages) <=0:
            message = "No calibration images provided"
            self.messageBroker.publish(self.topic, message)
            print(message)
            return False, [], [], message

        # Prepare object points
        chessboard_size = (self.chessboardWidth, self.chessboardHeight)
        square_size = self.squareSizeMM
        objp = np.zeros((np.prod(chessboard_size), 3), np.float32)
        objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
        objp *= square_size

        objpoints = []  # 3d points in real world space
        imgpoints = []  # 2d points in image plane

        message = f"Processing {len(self.calibrationImages)} images for chessboard detection..."
        self.messageBroker.publish(self.topic, message)

        valid_images = 0
        for idx, img in enumerate(self.calibrationImages):
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Find the chessboard corners
            ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

            if ret:
                objpoints.append(objp)

                # Refine corner positions
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                imgpoints.append(corners2)

                # Draw and save the corners for visualization
                cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
                output_path = os.path.join(self.STORAGE_PATH, f'calib_result_{idx:03d}.png')
                cv2.imwrite(output_path, img)

                valid_images += 1
                print(f"✅ Chessboard detected in image {idx}")
                message = f"✅ Chessboard detected in image {idx} - saved to {output_path}"
                self.messageBroker.publish(self.topic,message)
            else:
                print(f"❌ No chessboard found in image {idx}")
                message = f"❌ No chessboard found in image {idx}"
                self.messageBroker.publish(self.topic, message)

        if valid_images < 3:  # Need at least 3 good images for calibration
            message = f"Insufficient valid images for calibration. Found {valid_images}, need at least 3."
            print(f"❌ {message}")
            self.messageBroker.publish(self.topic, message)
            return False, None, None, message

        # Perform camera calibration
        print(f"🔧 Performing calibration with {valid_images} valid images...")
        message = f"🔧 Performing calibration with {valid_images} valid images..."
        self.messageBroker.publish(self.topic, message)

        try:
            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpoints, gray.shape[::-1], None, None
            )

            if ret:
                # Save calibration results
                calibration_file = os.path.join(self.STORAGE_PATH, 'calibration_data.npz')
                np.savez(calibration_file,
                         camera_matrix=camera_matrix,
                         dist_coeffs=dist_coeffs,
                         rvecs=rvecs,
                         tvecs=tvecs)

                # Store in instance variables
                self.camera_matrix = camera_matrix
                self.dist_coeffs = dist_coeffs
                self.calibrated = True


                print("✅ Camera calibration completed successfully!")
                message = "✅ Camera calibration completed successfully!"
                self.messageBroker.publish(self.topic, message)

                print(f"📊 Calibration parameters saved to: {calibration_file}")
                message = f"📊 Calibration parameters saved to: {calibration_file}"
                self.messageBroker.publish(self.topic, message)

                message = f"Calibration successful with {valid_images} images"
                self.messageBroker.publish(self.topic, message)
                return True, [dist_coeffs,camera_matrix],None, message
            else:
                message = "Camera calibration failed during cv2.calibrateCamera"
                print(f"❌ {message}")
                self.messageBroker.publish(self.topic, message)
                return False, None, None, message

        except Exception as e:
            message = f"Exception during calibration: {str(e)}"
            self.messageBroker.publish(self.topic, message)
            print(f"❌ {message}")
            return False, None, None, message


    #
    # def getWorkAreaMatrix(self, dst_points, src_points):
    #     """
    #     Computes and saves the perspective transform matrix.
    #     """
    #     print("Computing perspective transform matrix...")
    #     perspectiveMatrix, _ = cv2.findHomography(src_points, dst_points)
    #     print("Perspective transform matrix computed.")
    #     print("Saving perspective matrix...")
    #     np.save(self.PERSPECTIVE_MATRIX_PATH, perspectiveMatrix)
    #     print("Saving perspective")
    #     return perspectiveMatrix
    #
    # def sortCorners(self, corners):
    #     """
    #     Sorts corners to identify bottomLeft, bottomRight, topLeft, topRight.
    #     """
    #     points = np.squeeze(corners)
    #     topLeft = min(points, key=lambda p: p[0] + p[1])
    #     topRight = max(points, key=lambda p: p[0] - p[1])
    #     bottomLeft = min(points, key=lambda p: p[0] - p[1])
    #     bottomRight = max(points, key=lambda p: p[0] + p[1])
    #     return bottomLeft, bottomRight, topLeft, topRight
    #
    # def computeCameraToRobotTransformationMatrix(self, camera_pts, robot_pts):
    #     """
    #     Computes the homography transformation matrix from camera coordinates to robot coordinates.
    #     """
    #     camera_pts = np.array(camera_pts, dtype=np.float32)
    #     robot_pts = np.array(robot_pts, dtype=np.float32)
    #     homography_matrix, _ = cv2.findHomography(camera_pts, robot_pts)
    #     return homography_matrix
    #
    # def __displayDebugImage(self, image):
    #     cv2.imshow("Debug", image)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()
