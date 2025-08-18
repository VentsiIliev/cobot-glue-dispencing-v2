import json
import os
import time
import numpy as np

from API.MessageBroker import MessageBroker
from VisionSystem.calibration.cameraCalibration.CameraCalibrationService import CameraCalibrationService
from src.plvision.PLVision import Contouring
from src.plvision.PLVision import ImageProcessing
from src.plvision.PLVision.Camera import Camera
from src.plvision.PLVision.PID.BrightnessController import BrightnessController
from src.plvision.PLVision.arucoModule import *
from API.shared.settings.conreateSettings.CameraSettings import CameraSettings
from API.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
import logging
import platform
import cv2

# Paths to camera calibration data
CAMERA_DATA_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                'calibration_result', 'camera_calibration.npz')

PERSPECTIVE_MATRIX_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                       'calibration_result', 'perspectiveTransform.npy')
CAMERA_TO_ROBOT_MATRIX_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                           'calibration_result', 'cameraToRobotMatrix.npy')

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.json')


class VisionSystem:
    def __init__(self, configFilePath=None, camera_settings=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.calibrationImages = []
        self.broker = MessageBroker()
        self.calibrationImageCapturedTopic = "vision-system/calibration_image_captured"
        # Initialize camera settings
        if camera_settings is not None:
            self.camera_settings = camera_settings
        else:
            # Load from config file or use defaults
            if configFilePath is not None:
                config_data = self.__loadSettings(configFilePath)
                self.camera_settings = CameraSettings(config_data)
            else:
                self.camera_settings = CameraSettings()

        # Initialize camera with settings
        self.camera = Camera(
            self.camera_settings.get_camera_index(),
            self.camera_settings.get_camera_width(),
            self.camera_settings.get_camera_height()
        )

        # # Handle camera availability
        # if not self.camera.cap.isOpened():
        #     if platform.system().lower() == "linux":
        #         availableIds = self.find_first_available_camera()
        #     else:
        #         # On Windows, try indices 0-5
        #         availableIds = []
        #         for i in range(6):
        #             cap = cv2.VideoCapture(i)
        #             if cap.isOpened():
        #                 cap.release()
        #                 availableIds.append(i)
        #
        #     if len(availableIds) == 0:
        #         print("NO CAMERAS FOUND")
        #     else:
        #         for id in availableIds:
        #             self.camera = Camera(
        #                 id,
        #                 self.camera_settings.get_camera_width(),
        #                 self.camera_settings.get_camera_height()
        #             )
        #             if self.camera.cap.isOpened():
        #                 print("Camera found : ", id)
        #                 self.camera_settings.set_camera_index(id)
        #                 break

        # Load camera calibration data
        self.isSystemCalibrated = False
        self.__loadPerspectiveMatrix()
        self.__loadCameraCalibrationData()
        self.__loadCameraToRobotMatrix()

        if self.cameraData is None or self.perspectiveMatrix is None or self.cameraToRobotMatrix is None:
            self.isSystemCalibrated = False

        if self.cameraData is None or self.cameraToRobotMatrix is None:
            self.isSystemCalibrated = False

        # Extract camera matrix and distortion coefficients
        if self.isSystemCalibrated:
            self.cameraMatrix = self.cameraData['mtx']
            self.cameraDist = self.cameraData['dist']

        # Initialize image variables
        self.image = None
        self.rawImage = None
        self.correctedImage = None

        # Initialize brightness controller with settings
        self.brightnessController = BrightnessController(
            Kp=self.camera_settings.get_brightness_kp(),
            Ki=self.camera_settings.get_brightness_ki(),
            Kd=self.camera_settings.get_brightness_kd(),
            setPoint=self.camera_settings.get_target_brightness()
        )
        self.adjustment = 0

        self.rawMode = False
        self.brightnessAdjustment = 0

        # Initialize skip frames counter
        self.current_skip_frames = 0

    def captureCalibrationImage(self):
        if self.rawImage is None:
            self.logger.warning("No rawImage image captured for calibration")
            return False, "No rawImage image captured for calibration"

        self.calibrationImages.append(self.rawImage)
        self.broker.publish(self.calibrationImageCapturedTopic, self.calibrationImages)
        return True, "Calibration image captured successfully"

    def run(self):
        self.image = self.camera.capture()

        # Handle frame skipping
        if self.current_skip_frames < self.camera_settings.get_skip_frames():
            self.current_skip_frames += 1
            return None, None, None

        if self.image is None:
            return None, None, None

        self.rawImage = self.image.copy()

        # Handle brightness adjustment if enabled
        if self.camera_settings.get_brightness_auto():
            adjusted_frame = self.brightnessController.adjustBrightness(self.image, self.brightnessAdjustment)
            current_brightness = self.brightnessController.calculateBrightness(adjusted_frame)
            self.brightnessAdjustment = self.brightnessController.compute(current_brightness)
            adjusted_frame = self.brightnessController.adjustBrightness(self.image, self.brightnessAdjustment)
            self.image = adjusted_frame

        if self.rawMode:
            return None, self.rawImage, None
        if self.camera_settings.get_contour_detection():
            if self.isSystemCalibrated:
                self.correctedImage = self.correctImage(self.image.copy())
            else:
                cv2.putText(self.image, "System is not calibrated", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255),
                            2)
                self.correctedImage = self.image

            contours = self.findContours(self.correctedImage)
            approxContours = self.approxContours(contours)
            filteredContours = [cnt for cnt in approxContours if cv2.contourArea(cnt) > self.camera_settings.get_min_contour_area()]
            filteredContours = [cnt for cnt in filteredContours if cv2.contourArea(cnt) < self.camera_settings.get_max_contour_area()]
            # Cache centroids once
            contours_with_centroids = []
            for cnt in filteredContours:
                centroid = Contouring.calculateCentroid(cnt)
                if centroid is not None:
                    contours_with_centroids.append((cnt, centroid))

            if not contours_with_centroids:
                return None, self.correctedImage, None

            # Squared distance function
            def sq_dist(p1, p2):
                return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

            top_left = (0, 0)
            contours_sorted = []

            # Initialize with closest contour to top-left
            current_index, (current_contour, current_centroid) = min(
                enumerate(contours_with_centroids),
                key=lambda x: sq_dist(x[1][1], top_left)
            )
            contours_sorted.append(current_contour)

            # Track which contours remain
            remaining_indices = set(range(len(contours_with_centroids)))
            remaining_indices.remove(current_index)

            # Iteratively pick next closest contour
            while remaining_indices:
                next_index, (next_contour, next_centroid) = min(
                    ((i, contours_with_centroids[i]) for i in remaining_indices),
                    key=lambda x: sq_dist(x[1][1], current_centroid)
                )
                contours_sorted.append(next_contour)
                remaining_indices.remove(next_index)
                current_centroid = next_centroid

            if self.camera_settings.get_draw_contours():
                cv2.drawContours(self.correctedImage, contours_sorted, -1, (0, 255, 0), 1)

            return contours_sorted, self.correctedImage, None

        self.correctedImage = self.correctImage(self.image)
        return None, self.correctedImage, None

    def correctImage(self, imageParam):
        """
        Undistorts and applies perspective correction to the given image.
        """
        imageParam = ImageProcessing.undistortImage(
            imageParam,
            self.cameraMatrix,
            self.cameraDist,
            self.camera_settings.get_camera_width(),
            self.camera_settings.get_camera_height()
        )
        # imageParam = cv2.warpPerspective(
        #     imageParam,
        #     self.perspectiveMatrix,
        #     (self.camera_settings.get_camera_width(), self.camera_settings.get_camera_height())
        # )
        return imageParam

    def findContours(self, imageParam):
        """
        Converts an image to grayscale, applies thresholding, performs dilation and erosion, and finds contours.
        """
        gray = cv2.cvtColor(imageParam, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur if enabled
        if self.camera_settings.get_gaussian_blur():
            blur_kernel_size = self.camera_settings.get_blur_kernel_size()
            # Ensure kernel size is odd
            if blur_kernel_size % 2 == 0:
                blur_kernel_size += 1
            blur = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
        else:
            blur = gray

        # Apply threshold with configurable type
        threshold_type = self.camera_settings.get_threshold_type()
        threshold_types = {
            "binary": cv2.THRESH_BINARY,
            "binary_inv": cv2.THRESH_BINARY_INV,
            "trunc": cv2.THRESH_TRUNC,
            "tozero": cv2.THRESH_TOZERO,
            "tozero_inv": cv2.THRESH_TOZERO_INV
        }

        thresh_type = threshold_types.get(threshold_type, cv2.THRESH_BINARY_INV)
        _, thresh = cv2.threshold(blur, self.camera_settings.get_threshold(), 255, thresh_type)

        # Apply dilation if enabled
        if self.camera_settings.get_dilate_enabled():
            dilate_kernel_size = self.camera_settings.get_dilate_kernel_size()
            dilate_iterations = self.camera_settings.get_dilate_iterations()
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate_kernel_size, dilate_kernel_size))
            thresh = cv2.dilate(thresh, kernel, iterations=dilate_iterations)

        # Apply erosion if enabled
        if self.camera_settings.get_erode_enabled():
            erode_kernel_size = self.camera_settings.get_erode_kernel_size()
            erode_iterations = self.camera_settings.get_erode_iterations()
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (erode_kernel_size, erode_kernel_size))
            thresh = cv2.erode(thresh, kernel, iterations=erode_iterations)

        # Find contours on the processed image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def approxContours(self, contours):
        """
        Approximates contours using the Ramer-Douglas-Pucker algorithm.
        """
        approx = []
        for cnt in contours:
            epsilon = self.camera_settings.get_epsilon() * cv2.arcLength(cnt, True)
            approx_contour = cv2.approxPolyDP(cnt, epsilon, True)
            approx.append(approx_contour)
        return approx

    def calibrateCamera(self):
        """
        Calibrates the camera using the CameraCalibrationService.
        """
        enableContourDrawingAfterCalibration = self.camera_settings.get_draw_contours()
        if self.camera_settings.get_draw_contours():
            self.camera_settings.set_draw_contours(False)

        cameraCalibrationService = CameraCalibrationService(
            chessboardWidth=self.camera_settings.get_chessboard_width(),
            chessboardHeight=self.camera_settings.get_chessboard_height(),
            squareSizeMM=self.camera_settings.get_square_size_mm(),
            skipFrames=self.camera_settings.get_calibration_skip_frames()
        )


        cameraCalibrationService.calibrationImages = self.calibrationImages

        result, calibrationData, perspectiveMatrix, message = cameraCalibrationService.run(self.rawImage)
        if result:
            self.cameraMatrix = calibrationData[1]
            self.cameraDist = calibrationData[0]
            self.perspectiveMatrix = perspectiveMatrix
        else:
            self.logger.warning(f"[{self.__class__.__name__}] Calibration failed")

        if enableContourDrawingAfterCalibration:
            self.camera_settings.set_draw_contours(True)
        return result, message

    def adjustBrightness(self, frame):
        """
        Adjusts the brightness of a frame.
        """
        adjustedFrame = self.brightnessController.adjustBrightness(frame, self.adjustment)
        currentBrightness = self.brightnessController.calculateBrightness(adjustedFrame)
        self.adjustment = self.brightnessController.compute(currentBrightness)
        adjustedFrame = self.brightnessController.adjustBrightness(frame, self.adjustment)
        return adjustedFrame

    def captureImage(self):
        """
        Capture and return the corrected image.
        """
        return self.correctedImage

    def updateSettings(self, settings: dict):
        """
        Updates the camera settings using the CameraSettings object.
        """
        try:
            # Update the camera_settings object
            success, message = self.camera_settings.updateSettings(settings)

            if not success:
                return False, message

            # Update the brightness controller with new PID values
            self.brightnessController.Kp = self.camera_settings.get_brightness_kp()
            self.brightnessController.Ki = self.camera_settings.get_brightness_ki()
            self.brightnessController.Kd = self.camera_settings.get_brightness_kd()
            self.brightnessController.target = self.camera_settings.get_target_brightness()

            # Update camera resolution if changed
            if (CameraSettingKey.WIDTH.value in settings or
                    CameraSettingKey.HEIGHT.value in settings or
                    CameraSettingKey.INDEX.value in settings):
                # Reinitialize camera with new settings
                self.camera = Camera(
                    self.camera_settings.get_camera_index(),
                    self.camera_settings.get_camera_width(),
                    self.camera_settings.get_camera_height()
                )

            return True, "Settings updated successfully"

        except Exception as e:
            return False, f"Error updating settings: {str(e)}"

    def detectArucoMarkers(self, flip=False, image=None):
        """
        Detect ArUco markers in the image.
        """
        # Use settings value if flip not specified
        if flip is None:
            flip = self.camera_settings.get_aruco_flip_image()

        # Check if ArUco detection is enabled
        if not self.camera_settings.get_aruco_enabled():
            return None, None, None

        enableContourDrawingAfterDetection = self.camera_settings.get_draw_contours()
        if self.camera_settings.get_draw_contours():
            self.camera_settings.set_draw_contours(False)

        if image is None:
            skip = 30
            while skip > 0:
                image = self.correctedImage
                skip -= 1

        if flip is True:
            image = cv2.flip(image, 1)

        # Get ArUco dictionary from settings
        aruco_dict_name = self.camera_settings.get_aruco_dictionary()
        aruco_dict = getattr(ArucoDictionary, aruco_dict_name, ArucoDictionary.DICT_4X4_250)

        arucoDetector = ArucoDetector(arucoDict=aruco_dict)
        try:
            arucoCorners, arucoIds = arucoDetector.detectAll(image)
        except Exception as e:
            print(e)
            return None, None, None

        if enableContourDrawingAfterDetection:
            self.camera_settings.set_draw_contours(True)

        return arucoCorners, arucoIds, image

    def detectQrCode(self):
        """
        Detect and decode QR codes in the raw image.
        """
        from VisionSystem.QRcodeScanner import detect_and_decode_barcode
        data = detect_and_decode_barcode(self.rawImage)
        return data

    def find_first_available_camera(self, max_devices=10):
        """
        Find the first available camera on Linux systems.
        """
        import linuxUtils
        import re

        cams = linuxUtils.list_video_devices_v4l2()
        candidate_indices = []

        for name, paths in cams.items():
            if "integrated" in name.lower():
                continue  # Skip internal webcams

            for path in paths:
                if "/dev/video" in path:
                    match = re.search(r"/dev/video(\d+)", path)
                    if match:
                        candidate_indices.append(int(match.group(1)))

        available_cameras = []
        # Test each candidate index to see if it's available
        for cam_id in candidate_indices:
            self.logger.warning(f"[{self.__class__.__name__}] Checking camera id: {cam_id}")
            cap = cv2.VideoCapture(cam_id)
            if cap.isOpened():
                cap.release()
                available_cameras.append(cam_id)

        return available_cameras

    def get_camera_settings(self):
        """
        Get the current camera settings object.
        """
        return self.camera_settings

    def testCalibration(self):
        print("In testCalibration method")
        # find the required aruco markers
        required_ids = set(range(9))
        try:
            arucoCorners, arucoIds, image = self.detectArucoMarkers(flip=False, image=self.correctedImage)
        except:
            print("❌ Error during ArUco marker detection")
            return False, None, None

        if arucoIds is not None:
            found_ids = np.array(arucoIds).flatten().tolist()
            print("🆔 Detected marker IDs:", found_ids)
            cv2.aruco.drawDetectedMarkers(image, arucoCorners, np.array(arucoIds, dtype=np.int32))

            if len(found_ids) >= 9:
                id_to_corner = {int(id_): corner for id_, corner in zip(arucoIds.flatten(), arucoCorners)}

                if required_ids.issubset(id_to_corner.keys()):
                    # Extract top-left corners in order of IDs 0 through 8
                    ordered_camera_points = [id_to_corner[i][0] for i in sorted(required_ids)]
                    print("✅ All required markers found: ", ordered_camera_points)
                    print("📍 Top-left corners of required markers:")

                    # Transform the points to robot coordinates
                    points = [id_to_corner[i][0] for i in sorted(required_ids)]  # Use ordered points
                    src_pts = np.array(points, dtype=np.float32)
                    src_pts = src_pts.reshape(-1, 1, 2)  # (N, 1, 2) format for perspectiveTransform

                    # Transform to robot coordinate space
                    transformed_pts = cv2.perspectiveTransform(src_pts, self.cameraToRobotMatrix)
                    transformed_pts = transformed_pts.reshape(-1, 2)

                    print("\n📍 Transformed Robot Coordinates:")
                    for i, pt in enumerate(transformed_pts):
                        print(f"Marker {i}: X = {pt[0]:.2f}, Y = {pt[1]:.2f}")

                    # Continue with the rest of your calibration logic here...
                    return True, ordered_camera_points, image
                else:
                    print("❌ Not all required markers found")
                    return False, None, image
            else:
                print("❌ Not enough markers detected")
                return False, None, image
        else:
            print("❌ No markers detected")
            return False, None, None


    """PRIVATE METHODS SECTION"""

    def __loadCameraToRobotMatrix(self):
        try:
            self.cameraToRobotMatrix = np.load(CAMERA_TO_ROBOT_MATRIX_PATH)
        except FileNotFoundError:
            self.cameraToRobotMatrix = None
            self.isSystemCalibrated = True
            raise ValueError("File not found: " + CAMERA_TO_ROBOT_MATRIX_PATH)

    def __loadCameraCalibrationData(self):
        try:
            self.cameraData = np.load(CAMERA_DATA_PATH)
            self.isSystemCalibrated = True
        except FileNotFoundError:
            self.cameraData = None
            self.isSystemCalibrated = False
            self.logger.error(f"Camera calibration data file not found at {CAMERA_DATA_PATH}")

    def __loadPerspectiveMatrix(self):
        try:
            self.perspectiveMatrix = np.load(PERSPECTIVE_MATRIX_PATH)
            self.isSystemCalibrated = True
        except FileNotFoundError:
            self.perspectiveMatrix = None

    def __loadSettings(self, configFilePath):
        if configFilePath is None:
            configFilePath = CONFIG_FILE_PATH
        with open(configFilePath) as f:
            data = json.load(f)
        return data


if __name__ == "__main__":
    vision_system = VisionSystem()
    print("Available cameras: ", vision_system.find_first_available_camera())

    while True:
        contours, corrected_image, _ = vision_system.run()
        if contours is not None:
            print(f"Detected {len(contours)} contours")
        if corrected_image is None:
            continue

        cv2.imshow("Corrected Image", corrected_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()