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
        self.chessboardWidth = chessboardWidth
        self.chessboardHeight = chessboardHeight
        self.squareSizeMM = squareSizeMM
        self.skipFrames = skipFrames
        self.onDetectionFailed = onDetectionFailed
        self.cameraCalibrator = CameraCalibrator(self.chessboardWidth, self.chessboardHeight, self.squareSizeMM)

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

    def run(self, image, debug=False):
        """
        Main calibration workflow.
        Returns (success, calibrationData, perspectiveMatrix, message)
        """
        print("Calibration Started with image", image)
        message = ""

        if debug:
            self.__displayDebugImage(image)

        imageHeight, imageWidth = image.shape[:2]

        required_ids = {30, 31, 32, 33}
        maxAttempts = 60

        arucoCorners, arucoIds = None, None
        for attempt in range(maxAttempts, 0, -1):
            print(f"Aruco Attempt: {attempt}")
            arucoCorners, arucoIds, _ = self.detectArucoMarkers(image=image.copy())
            if arucoIds is not None:
                id_to_corners = {aruco_id: arucoCorners[i][0] for i, aruco_id in enumerate(arucoIds.flatten())}
                if required_ids.issubset(id_to_corners.keys()):
                    break
            else:
                id_to_corners = {}
        else:
            message = "No ArUco markers found"
            print(message)
            return False, None, None, message

        if not required_ids.issubset(id_to_corners.keys()):
            message = "Missing aruco markers during calibration"
            print(message)
            print("Markers found during calibration:", arucoIds)
            return False, None, None, message

        # Assign corners based on IDs
        topLeft = id_to_corners[30][0]
        topRight = id_to_corners[31][0]
        bottomRight = id_to_corners[32][0]
        bottomLeft = id_to_corners[33][0]

        src_points = np.array([topLeft, topRight, bottomRight, bottomLeft], dtype='float32')
        dst_points = np.array([
            [0, 0],
            [imageWidth, 0],
            [imageWidth, imageHeight],
            [0, imageHeight]
        ], dtype='float32')

        perspectiveMatrix = self.getWorkAreaMatrix(dst_points, src_points)
        croppedImage = cv2.warpPerspective(image, perspectiveMatrix, (imageWidth, imageHeight))

        if not cv2.imwrite("ArucoCrop.png", croppedImage):
            print("❌ Failed to save the image.")
        else:
            print("✅ Image saved successfully: ArucoCrop.png")

        if debug:
            self.__displayDebugImage(croppedImage)

        result, calibrationData, imageCopy, corners = self.cameraCalibrator.performCameraCalibration(
            croppedImage, self.STORAGE_PATH
        )

        if not result:
            print("Calibration failed")
            print("corners:", corners)
            if debug:
                cv2.imwrite("calibration_failed.png", croppedImage)
                cv2.imshow("Calibration Failed Image", croppedImage)
                cv2.imshow("Calibration Failed Image", imageCopy)
                cv2.waitKey(1)
            if corners is not None and len(corners) != self.chessboardWidth * self.chessboardHeight:
                message = f"Corners not equal to {self.chessboardWidth * self.chessboardHeight}"
            else:
                message = "Corners not found"
            print(message)
            return False, [], [], message

        print("Calibration successful")
        print("corners len:", len(corners))

        if debug:
            self.__displayDebugImage(imageCopy)

        message = "Calibration successful"
        return True, calibrationData, perspectiveMatrix, message

    def getWorkAreaMatrix(self, dst_points, src_points):
        """
        Computes and saves the perspective transform matrix.
        """
        print("Computing perspective transform matrix...")
        perspectiveMatrix, _ = cv2.findHomography(src_points, dst_points)
        print("Perspective transform matrix computed.")
        print("Saving perspective matrix...")
        np.save(self.PERSPECTIVE_MATRIX_PATH, perspectiveMatrix)
        print("Saving perspective")
        return perspectiveMatrix

    def sortCorners(self, corners):
        """
        Sorts corners to identify bottomLeft, bottomRight, topLeft, topRight.
        """
        points = np.squeeze(corners)
        topLeft = min(points, key=lambda p: p[0] + p[1])
        topRight = max(points, key=lambda p: p[0] - p[1])
        bottomLeft = min(points, key=lambda p: p[0] - p[1])
        bottomRight = max(points, key=lambda p: p[0] + p[1])
        return bottomLeft, bottomRight, topLeft, topRight

    def computeCameraToRobotTransformationMatrix(self, camera_pts, robot_pts):
        """
        Computes the homography transformation matrix from camera coordinates to robot coordinates.
        """
        camera_pts = np.array(camera_pts, dtype=np.float32)
        robot_pts = np.array(robot_pts, dtype=np.float32)
        homography_matrix, _ = cv2.findHomography(camera_pts, robot_pts)
        return homography_matrix

    def __displayDebugImage(self, image):
        cv2.imshow("Debug", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
