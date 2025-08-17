import threading
import cv2
import numpy as np
import traceback
import time

from API import Constants
from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey

from GlueDispensingApplication.robot.RobotConfig import *

from GlueDispensingApplication.settings.SettingsService import SettingsService

from src.plvision.PLVision import Contouring
from API.MessageBroker import MessageBroker
from API.shared.workpiece.WorkpieceService import WorkpieceService
from GlueDispensingApplication import CompareContours
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.tools.enums.Program import Program
from GlueDispensingApplication.tools.enums.ToolID import ToolID
from GlueDispensingApplication import Initializations
from GlueDispensingApplication.vision.VisionService import VisionServiceSingleton
from GlueDispensingApplication.utils import utils
from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
from GlueDispensingApplication.robot.RobotCalibrationService import RobotCalibrationService
from GlueDispensingApplication.robot.Plane import Plane
from GlueDispensingApplication.tools.GlueCell import GlueCellsManagerSingleton
"""
ENDPOINTS
- start
- measureHeight
- calibrateRobot
- calibrateCamera
- createWorkpiece

"""


class GlueSprayingApplication:
    """
    ActionManager is responsible for connecting actions to functions.
    The MainWindow will just emit signals, and ActionManager handles them.
    """

    glueCellsManager = GlueCellsManagerSingleton.get_instance()
    # MAX_QUEUE_SIZE = 1  # Define the maximum number of frames to keep in the queue
    # WORK_AREA_WIDTH = 750  # Width of the work area in mm
    # WORK_AREA_HEIGHT = 500  # Height of the work area in mm

    def __init__(self, callbackFunction, visionService: VisionServiceSingleton, settingsManager: SettingsService,
                 glueNozzleService: GlueNozzleService, workpieceService: WorkpieceService,
                 robotService: RobotService, robotCalibrationService: RobotCalibrationService):
        super().__init__()

        self.settingsManager = settingsManager
        self.visionService = visionService
        self.glueNozzleService = glueNozzleService
        self.workpieceService = workpieceService
        self.robotService = robotService
        # self.robotService.moveToLoginPosition()

        # self.robotService.startExecutionThreads()

        self.robotCalibService = robotCalibrationService

        # Start the camera feed in a separate thread
        self.cameraThread = threading.Thread(target=self.visionService.run, daemon=True)
        self.cameraThread.start()

        self.callbackFunction = callbackFunction

        # self.ppmX = self.visionService.getFrameWidth() / self.WORK_AREA_WIDTH  # Pixels per millimeter in x direction
        # self.ppmY = self.visionService.getFrameHeight() / self.WORK_AREA_HEIGHT  # Pixels per millimeter in

    # Action functions
    def start(self, contourMatching=True):
        """
        Main method to start the robotic operation, either performing contour matching and nesting of workpieces
        or directly tracing contours. If contourMatching is False, only contour tracing is performed.
        """
        if contourMatching:
            workpieces = self.workpieceService.loadAllWorkpieces()

            self.robotService.moveToCalibrationPosition()
            self.robotService._waitForRobotToReachPosition(self.robotService.calibrationPosition, 2, 0.1)
            time.sleep(2)

            result, newContours = self.visionService.processContours()
            if not result:
                return False, "No contours found"
    #         newContours = [np.array([
    # [1149, 72], [1145, 72], [1144, 73], [1137, 73], [1136, 74],
    # [1130, 74], [1129, 75], [1124, 75], [1123, 76], [1119, 76],
    # [1118, 77], [1112, 77], [1111, 78], [1105, 78], [1104, 79],
    # [1099, 79], [1098, 80], [1091, 80], [1090, 81], [1083, 81],
    # [1082, 82], [1076, 82], [1075, 83], [1070, 83], [1069, 84],
    # [1063, 84], [1062, 85], [1056, 85], [1055, 86], [1049, 86],
    # [1048, 87], [1042, 87], [1041, 88], [1036, 88], [1035, 89],
    # [1030, 89], [1029, 90], [1023, 90], [1022, 91], [1016, 91],
    # [1015, 92], [1009, 92], [1008, 93], [1001, 93], [1000, 94],
    # [994, 94], [993, 95], [988, 95], [987, 96], [981, 96],
    # [980, 97], [975, 97], [974, 98], [967, 98], [966, 99],
    # [959, 99], [958, 100], [953, 100], [952, 101], [946, 101],
    # [945, 102], [939, 102], [938, 103], [934, 103], [933, 104],
    # [926, 104], [925, 105], [919, 105], [918, 106], [909, 106],
    # [908, 107], [902, 107], [901, 108], [896, 108], [895, 109],
    # [889, 109], [888, 110], [881, 110], [880, 111], [875, 111],
    # [874, 112], [868, 112], [867, 113], [863, 113], [862, 114],
    # [856, 114], [855, 115], [855, 119], [856, 120], [856, 125],
    # [857, 126], [857, 130], [858, 131], [858, 136], [859, 137],
    # [859, 141], [860, 142], [860, 146], [861, 147], [861, 152],
    # [862, 153], [862, 157], [863, 158], [863, 162], [864, 163],
    # [864, 167], [865, 168], [865, 172], [866, 173], [866, 178],
    # [867, 179], [867, 183], [868, 184], [868, 188], [869, 189],
    # [869, 194], [870, 195], [870, 199], [871, 200], [871, 204],
    # [872, 205], [872, 210], [873, 211], [873, 215], [874, 216],
    # [874, 220], [875, 221], [875, 225], [876, 226], [876, 231],
    # [877, 232], [877, 236], [878, 237], [878, 241], [879, 242],
    # [879, 246], [880, 247], [880, 252], [881, 253], [881, 257],
    # [882, 258], [882, 262], [883, 263], [883, 268], [884, 269],
    # [884, 272], [885, 273], [885, 278], [886, 279], [886, 283],
    # [887, 284], [887, 288], [888, 289], [888, 293], [889, 294],
    # [889, 299], [890, 300], [890, 304], [891, 305], [891, 309],
    # [892, 310], [892, 314], [893, 315], [893, 320], [894, 321],
    # [894, 324], [895, 325], [895, 329], [896, 330], [896, 334],
    # [897, 335], [897, 340], [898, 341], [898, 345], [899, 346],
    # [899, 350], [900, 351], [900, 355], [901, 356], [901, 360],
    # [902, 361], [902, 365], [903, 366], [903, 370], [904, 371],
    # [904, 375], [905, 376], [905, 380], [906, 381], [906, 385],
    # [907, 386], [907, 390], [908, 391], [908, 395], [909, 396],
    # [909, 400], [910, 401], [910, 405], [911, 406], [911, 410],
    # [912, 411], [912, 415], [913, 416], [913, 420], [914, 421],
    # [914, 425], [915, 426], [915, 430], [916, 431], [916, 435],
    # [917, 436], [917, 440], [918, 441], [918, 445], [919, 446],
    # [919, 449], [920, 450], [920, 454], [921, 455], [921, 459],
    # [922, 460], [922, 463], [923, 464], [927, 464], [928, 463],
    # [935, 463], [936, 462], [942, 462], [943, 461], [949, 461],
    # [950, 460], [957, 460], [958, 459], [965, 459], [966, 458],
    # [972, 458], [973, 457], [978, 457], [979, 456], [985, 456],
    # [986, 455], [993, 455], [994, 454], [1001, 454], [1002, 453],
    # [1007, 453], [1008, 452], [1014, 452], [1015, 451], [1021, 451],
    # [1022, 450], [1028, 450], [1029, 449], [1036, 449], [1037, 448],
    # [1043, 448], [1044, 447], [1050, 447], [1051, 446], [1058, 446],
    # [1059, 445], [1066, 445], [1067, 444], [1072, 444], [1073, 443],
    # [1079, 443], [1080, 442], [1086, 442], [1087, 441], [1094, 441],
    # [1095, 440], [1102, 440], [1103, 439], [1109, 439], [1110, 438],
    # [1117, 438], [1118, 437], [1123, 437], [1124, 436], [1131, 436],
    # [1132, 435], [1138, 435], [1139, 434], [1145, 434], [1146, 433],
    # [1152, 433], [1153, 432], [1159, 432], [1160, 431], [1167, 431],
    # [1168, 430], [1174, 430], [1175, 429], [1181, 429], [1182, 428],
    # [1188, 428], [1189, 427], [1196, 427], [1197, 426], [1204, 426],
    # [1205, 425], [1210, 425], [1211, 424], [1216, 424], [1217, 423],
    # [1218, 423], [1217, 422], [1217, 418], [1216, 417], [1216, 413],
    # [1215, 412], [1215, 408], [1214, 407], [1214, 403], [1213, 402],
    # [1213, 397], [1212, 396], [1212, 392], [1211, 391], [1211, 387],
    # [1210, 386], [1210, 382], [1209, 381], [1209, 377], [1208, 376],
    # [1208, 372], [1207, 371], [1207, 367], [1206, 366], [1206, 362],
    # [1205, 361], [1205, 357], [1204, 356], [1204, 352], [1203, 351],
    # [1203, 348], [1202, 347], [1202, 343], [1201, 342], [1201, 337],
    # [1200, 336], [1200, 333], [1199, 332], [1199, 328], [1198, 327],
    # [1198, 322], [1197, 321], [1197, 317], [1196, 316], [1196, 312],
    # [1195, 311], [1195, 307], [1194, 306], [1194, 301], [1193, 300],
    # [1193, 296], [1192, 295], [1192, 292], [1191, 291], [1191, 286],
    # [1190, 285], [1190, 281], [1189, 280], [1189, 276], [1188, 275],
    # [1188, 271], [1187, 270], [1187, 266], [1186, 265], [1186, 261],
    # [1185, 260], [1185, 256], [1184, 255], [1184, 251], [1183, 250],
    # [1183, 245], [1182, 244], [1182, 240], [1181, 239], [1181, 235],
    # [1180, 234], [1180, 229], [1179, 228], [1179, 224], [1178, 223],
    # [1178, 219], [1177, 218], [1177, 214], [1176, 213], [1176, 209],
    # [1175, 208], [1175, 203], [1174, 202], [1174, 199], [1173, 198],
    # [1173, 193], [1172, 192], [1172, 188], [1171, 187], [1171, 183],
    # [1170, 182], [1170, 178], [1169, 177], [1169, 173], [1168, 172],
    # [1168, 167], [1167, 166], [1167, 162], [1166, 161], [1166, 156],
    # [1165, 155], [1165, 151], [1164, 150], [1164, 146], [1163, 145],
    # [1163, 141], [1162, 140], [1162, 136], [1161, 135], [1161, 130],
    # [1160, 129], [1160, 125], [1159, 124], [1159, 120], [1158, 119],
    # [1158, 114], [1157, 113], [1157, 108], [1156, 107], [1156, 104],
    # [1155, 103], [1155, 99], [1154, 98], [1154, 94], [1153, 93],
    # [1153, 89], [1152, 88], [1152, 84], [1151, 83], [1151, 79],
    # [1150, 78], [1150, 74], [1149, 73]
# ], dtype=np.float32)]
            matches_data, noMatches, _ = CompareContours.findMatchingWorkpieces(workpieces, newContours)
            print("Matches:", matches_data)
            print("No Matches:", noMatches)

            orientations = matches_data["orientations"]
            matches = matches_data["workpieces"]

            if not matches:
                return False, "No matching workpieces found!"

            finalPaths = []

            for match_i, match in enumerate(matches):
                sprayPatternContour = match.get_spray_pattern_contours()
                sprayPatternFill = match.get_spray_pattern_fills()
                print("sprayPatternContour ", sprayPatternContour)
                print("sprayPatternFill ", sprayPatternFill)

                orientation = orientations[match_i]
                program = match.program
                glueType = match.glueType

                broker = MessageBroker()
                broker.publish("glueType", glueType)

                # ✅ Check if spray pattern exists and has data
                has_spray_contours = sprayPatternContour and len(sprayPatternContour) > 0
                has_spray_fills = sprayPatternFill and len(sprayPatternFill) > 0

                # --- CASE 1: No spray pattern, fall back to outer contour ---
                if not has_spray_contours and not has_spray_fills:
                    print("No spray pattern found, using main contour")

                    # Get main contour data
                    if isinstance(match.contour, dict) and "contour" in match.contour:
                        contour_data = match.contour["contour"]
                        main_settings = match.contour.get("settings", {})
                    else:
                        contour_data = match.contour
                        main_settings = {}

                    # Convert to list format if numpy array
                    if isinstance(contour_data, np.ndarray):
                        contour_points = contour_data.reshape(-1, 2).tolist()
                    else:
                        contour_points = self._flatten_and_convert(contour_data)

                    # Close contour if not already closed
                    if contour_points and contour_points[0] != contour_points[-1]:
                        contour_points.append(contour_points[0])

                    # Transform to robot coordinates
                    # robot_points = self._transform_to_robot_coordinates(contour_points)
                    robot_points = contour_points
                    # Convert to robot path format with Z, RX, RY, RZ
                    robot_path = self._convert_to_robot_path(robot_points, main_settings)

                    finalPaths.append((robot_path, main_settings))
                    continue

                # --- CASE 2: Process spray contours ---
                for entry in sprayPatternContour:
                    if "contour" in entry and entry["contour"] is not None and len(entry["contour"]) > 0:
                        contour_data = entry["contour"]
                        settings = entry.get("settings", {})

                        # Convert to proper format
                        pts = self._flatten_and_convert(contour_data)

                        # Transform to robot coordinates
                        robot_points = self._transform_to_robot_coordinates(pts)
                        # robot_points = pts

                        # Convert to robot path format
                        robot_path = self._convert_to_robot_path(robot_points, settings)

                        finalPaths.append((robot_path, settings))

                # --- CASE 3: Process spray fills (with zigzag pattern) ---
                for entry in sprayPatternFill:
                    if "contour" in entry and entry["contour"] is not None and len(entry["contour"]) >= 3:
                        contour_data = entry["contour"]
                        settings = entry.get("settings", {})

                        # Convert to proper format
                        flat_pts = self._flatten_and_convert(contour_data)

                        # Transform to robot coordinates first
                        # robot_points = self._transform_to_robot_coordinates(flat_pts)
                        robot_points = flat_pts
                        # Convert to OpenCV format for zigzag function
                        if len(robot_points) >= 3:
                            # Convert to OpenCV contour format (N, 1, 2)
                            opencv_contour = np.array(robot_points, dtype=np.float32).reshape(-1, 1, 2)

                            # Apply zigzag pattern
                            zigzag_contour = self.robotService.zigZag(opencv_contour, 25)

                            # Convert zigzag result back to 2D points
                            zigzag_points = zigzag_contour.reshape(-1, 2).tolist()

                            # Convert to robot path format
                            robot_path = self._convert_to_robot_path(zigzag_points, settings)

                            finalPaths.append((robot_path, settings))

            # ✅ Send all paths to robot
            if finalPaths:
                broker = MessageBroker()
                frame = self.visionService.getLatestFrame()
                # resize to (image_width=640, image_height=360)
                frame = cv2.resize(frame, (640, 360))
                broker.publish("robot/trajectory/updateImage", {"image": frame})
                self.robotService.traceContours(finalPaths)
            else:
                print("No valid paths generated")

        else:
            # ✅ Direct contour tracing without matching
            result, newContours = self.visionService.processContours()
            if not result:
                return False, "No contours found"

            # Transform contours to robot coordinates and convert to proper format
            finalPaths = []
            default_settings = {
                "spraying_height": 4,
                "velocity": 30,
                "acceleration": 100,
                "rz_angle": 0
            }

            for contour in newContours:
                # Flatten and convert contour
                pts = self._flatten_and_convert(contour)

                # Transform to robot coordinates
                robot_points = self._transform_to_robot_coordinates(pts)

                # Convert to robot path format
                robot_path = self._convert_to_robot_path(robot_points, default_settings)

                finalPaths.append((robot_path, default_settings))

            if finalPaths:
                self.robotService.traceContours(finalPaths)

        self.robotService.moveToCalibrationPosition()
        self.robotService.moveToStartPosition()
        return True, "Success"

    def _transform_to_robot_coordinates(self, points):
        """Transform 2D points from camera coordinates to robot coordinates"""
        if not points:
            return []

        # Convert to numpy array for transformation
        np_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
        print("Points before transformation: ", np_points)
        # Apply camera to robot transformation
        transformed = utils.applyTransformation(self.visionService.cameraToRobotMatrix, np_points)
        print("Transformed points: ", transformed)
        # Convert back to list format
        result = []
        for point in transformed:
            # Flatten nested point structure
            while isinstance(point, (list, tuple, np.ndarray)) and len(point) == 1:
                point = point[0]
            if len(point) >= 2:
                result.append([float(point[0]), float(point[1])])

        return result

    def _convert_to_robot_path(self, points_2d, settings):
        """Convert 2D points to robot path format [x, y, z, rx, ry, rz]"""
        robot_path = []

        # Extract settings with defaults
        z_height = float(settings.get(GlueSettingKey.SPRAYING_HEIGHT,125))
        rz_angle = float(settings.get(GlueSettingKey.RZ_ANGLE, 0))

        for point in points_2d:
            if len(point) >= 2:
                robot_point = [
                    float(point[0]),  # x
                    float(point[1]),  # y
                    z_height,  # z
                    180.0,  # rx (standard orientation)
                    0.0,  # ry
                    rz_angle  # rz
                ]
                robot_path.append(robot_point)

        return robot_path

    def _flatten_and_convert(self, contour_array):
        """Ensure contour array is Nx2 list of floats."""
        arr = np.array(contour_array, dtype=float).reshape(-1, 2)  # Flatten to Nx2
        return arr.tolist()
    def transformContoursToHomePositionPlane(self, newContours):
        def transform_point_2d(p, R, T):
            p = np.array(p, dtype=np.float32)  # ensure it's a NumPy array
            return R @ p + T

        if newContours is None:
            raise Exception("[transformContoursToHomePositionPlane] contours can not be none")

        newContours = utils.applyTransformation(self.visionService.cameraToRobotMatrix, newContours)

        # print("New: ", newContours)
        # Extract 2D translation (X, Y) and yaw (rotation around Z)
        pos_calib = np.array(CALIBRATION_POS[:2])  # [x, y]
        pos_home = np.array(HOME_POS[:2])  # [x, y]
        yaw_calib = np.deg2rad(CALIBRATION_POS[5])  # Rz in degrees → radians
        yaw_home = np.deg2rad(HOME_POS[5])
        relative_yaw = yaw_home - yaw_calib  # ΔRz
        # 2D rotation matrix
        cos_a = np.cos(relative_yaw)
        sin_a = np.sin(relative_yaw)
        R = np.array([[cos_a, -sin_a],
                      [sin_a, cos_a]])
        # Apply rotation to calibration frame origin to find translation
        T = pos_home - R @ pos_calib
        # Fixed version - handle the extra nesting level
        # Calculate position offset
        for cnt_idx, cnt in enumerate(newContours):
            for point_idx, point in enumerate(cnt):
                # Extract the actual coordinate pair from the nested list
                actual_point = point[0] if isinstance(point, list) and len(point) > 0 else point
                # rotated_point = utils.rotate_point(actual_point, 90, [0, 0])
                transformed_point = transform_point_2d(actual_point, R, T)
                newContours[cnt_idx][point_idx] = [transformed_point.tolist()]  # Keep the same nesting structure
        return newContours

    def measureHeight(self, frame, maxAttempts=1, debug=False):
        """
          Measures the height of an object in the frame using a laser tracker.
          This process involves capturing a frame, running the laser tracker, and then iterating
          until a valid height estimate is obtained or the maximum number of attempts is reached.

          Parameters:
          - frame: The image frame captured by the vision system.
          - maxAttempts (default=1): The maximum number of attempts to estimate the height.
          - debug (default=False): If True, debug information will be overlayed on the image.

          Returns:
          - estimatedHeight: The estimated height of the object in millimeters (mm), or None if it couldn't be estimated.
          """
        attempts = 0
        estimatedHeight = None
        laserTracker = Initializations.initLaserTracker()
        while estimatedHeight is None and attempts < maxAttempts:
            estimatedHeight = laserTracker.run(frame)
            frame = self.visionService.captureImage()
            attempts += 1

        if debug:
            if estimatedHeight is not None:
                cv2.putText(frame, f"Estimated height: {estimatedHeight:.2f} mm", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Height estimation failed", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 2)

        return estimatedHeight

    def calibrateRobot(self):
        self.visionService.drawControus = False
        ARUCO_MARKER_0 = 0
        ARUCO_MARKER_1 = 1
        ARUCO_MARKER_2 = 2
        ARUCO_MARKER_3 = 3
        ARUCO_MARKER_4 = 4
        ARUCO_MARKER_5 = 5
        ARUCO_MARKER_6 = 6
        ARUCO_MARKER_7 = 7
        ARUCO_MARKER_8 = 8
        required_ids = {ARUCO_MARKER_0, ARUCO_MARKER_1, ARUCO_MARKER_2, ARUCO_MARKER_3, ARUCO_MARKER_4, ARUCO_MARKER_5,
                        ARUCO_MARKER_6, ARUCO_MARKER_7, ARUCO_MARKER_8}
        """
           Calibrates the robot using ArUco markers. It attempts to detect a set of ArUco markers
           in the camera feed, verify that the required markers are found, and send their positions
           to the robot calibration service to adjust the robot's positioning.

           Returns:
               tuple: A tuple containing:
                   - success (bool): True if calibration was successful, False otherwise.
                   - message (str): A message indicating the result of the calibration.
                   - image (ndarray): The image captured during the calibration process.
           """
        print("Calibrating robot") # Print to indicate the start of the calibration process
        message = "" # Initialize an empty message to return at the end of the function
        maxAttempts = 30 # Set a maximum number of attempts to detect ArUco markers
        # Step 1: Attempt to detect ArUco markers multiple times
        while maxAttempts > 0:
            print("Aruco Attempt: ", maxAttempts) # Show the number of remaining attempts

            # Step 2: Detect ArUco markers in the current camera frame
            arucoCorners, arucoIds, image = self.visionService.detectArucoMarkers()
            print("ids: ", arucoIds) # Print the detected ArUco marker IDs for debugging
            import cv2
            cv2.imwrite("robotaruco.png",image)
            # Step 3: If enough markers are detected (at least 9), stop retrying
            if arucoIds is not None and len(arucoIds) >= 9 and required_ids.issubset(set(arucoIds.flatten())):
                break  # Exit the loop once enough markers and required IDs have been detected
            maxAttempts -= 1 # Decrease the attempt counter if detection was not successful

        # Step 4: Convert the image from BGR to RGB format for proper visualization
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Step 5: Check if any ArUco markers were detected
        if arucoIds is None or len(arucoIds) == 0:
            print("No ArUco markers found")  # Print an error message if no markers were found
            message = "No ArUco markers found"  # Set the error message
            return False, message, image  # Return failure and the image

        # Step 6: Create a dictionary to store the corners of detected markers, indexed by their IDs
        id_to_corners = {}

        # Step 7: Store the corner coordinates of each detected marker in the dictionary
        for i, aruco_id in enumerate(arucoIds.flatten()):
            id_to_corners[aruco_id] = arucoCorners[i][0]  # Store all 4 corners of the marker

        # Step 8: Ensure that all required markers (IDs 0 through 8) are detected

        if not required_ids.issubset(id_to_corners.keys()):
            message = "Missing ArUco markers"
            return False, message, image # Return failure and the image

        # Step 9: Assign the detected marker corners to variables for easier access
        marker0 = id_to_corners[ARUCO_MARKER_0][0]  # First corner of ID 0
        marker1 = id_to_corners[ARUCO_MARKER_1][0]  # First corner of ID 1
        marker2 = id_to_corners[ARUCO_MARKER_2][0]  # First corner of ID 2
        marker3 = id_to_corners[ARUCO_MARKER_3][0]  # First corner of ID 3
        marker4 = id_to_corners[ARUCO_MARKER_4][0]  # First corner of ID 4
        marker5 = id_to_corners[ARUCO_MARKER_5][0]  # First corner of ID 5
        marker6 = id_to_corners[ARUCO_MARKER_6][0]  # First corner of ID 6
        marker7 = id_to_corners[ARUCO_MARKER_7][0]  # First corner of ID 7
        marker8 = id_to_corners[ARUCO_MARKER_8][0]  # First corner of ID 8


        # Step 10: Order the marker corners for visualization and further processing
        orderedMarkers = [marker0, marker1, marker2, marker3, marker4, marker5, marker6, marker7, marker8]

        # # Step 11: Optionally, define colors and labels for each marker to visualize them (for debugging)
        # colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]  # Red, Green, Blue, Yellow
        # labels = [4, 5, 6, 7]  # Labels for the markers (optional)

        # Step 12: Draw the markers on the image for visual verification (currently commented out)
        # Draw markers on the image with different colors
        # for i, (point, color, label) in enumerate(zip(orderedMarkers, colors, labels)):
        #     cv2.circle(image, (int(point[0]), int(point[1])), 8, color, -1)  # Larger circle for visibility

        print(f"Assigned corners: {orderedMarkers}") # Print the corners for debugging

        # Step 13: Send the detected marker positions to the robot calibration service
        self.robotCalibService.setCameraPoints(orderedMarkers)

        # Step 14: Retrieve the corresponding robot points (positions) for the calibration
        if self.robotCalibService.getRobotPoints() is not None and len(self.robotCalibService.getRobotPoints()) == 9:
            # Retrieve the robot positions (in 3D space) for the corresponding markers
            x, y, z = self.robotCalibService.getRobotPoints()[0]
            position = [x, y, z, 180, 0, 0]
            self.robotService.moveToPosition(position, 0, 0, 100, 30)
            position = [x, y, z, 180, 0, 0]
            self.robotService.moveToPosition(position, 0, 0, 100, 30)

        # Step 16: If calibration was successful, return success message and image
        message = "Robot Calibration Successful"
        return True, message, image

    def calibrateCamera(self):
        self.robotService.moveToCalibrationPosition()
        self.robotService._waitForRobotToReachPosition(self.robotService.calibrationPosition,1,delay=0)
        self.visionService.setRawMode(True)
        result = self.visionService.calibrateCamera()
        self.visionService.setRawMode(False)
        return result

    def createWorkpiece(self):
        """Creates a workpiece by processing contours and capturing images.

        Returns:
            tuple: (success: bool, data: tuple or error_message: str)
                   If successful, data contains (estimatedHeight, contourArea, contour,
                   scaleFactor, createWpImage, message, originalContours)
        """
        # Move robot to calibration position and wait
        self.robotService.moveToCalibrationPosition()
        try:
            self.robotService._waitForRobotToReachPosition(
                self.robotService.calibrationPosition, 1, 0.1
            )
            time.sleep(2)
        except Exception as e:
            import traceback
            traceback.print_exc()

        # Store original contours for later use
        originalContours = self.visionService.contours
        # write the points into debugCreateWp.txt
        print("originalcnt: ",originalContours)

        # Process contours from vision service
        result = False
        contours = None
        try:
            ret, contours = self.visionService.processContours()
            # not append contours to the file
            result = ret
        except Exception as e:
            import traceback
            traceback.print_exc()

        # Process contours if valid, otherwise set defaults
        if result and contours is not None and len(contours) > 0 and not isinstance(contours, str):
            contour = contours[0]

            # Ensure contour is a list before appending, then convert to numpy array
            if isinstance(contour, np.ndarray):
                contour = contour.tolist()

            contour.append(contour[0])  # Close the contour
            contour = np.array(contour, dtype=np.float32)
            centroid = Contouring.calculateCentroid(contour)
            contourArea = cv2.contourArea(contour)
        else:
            # No contours found - set defaults and prepare for manual editing
            originalContours = []
            contour = []
            centroid = [0, 0]
            contourArea = 0

        # Capture image for workpiece creation
        createWpImage = self.visionService.captureImage()
        print("createWpImage shape: ", createWpImage.shape)

        """
        HEIGHT MEASUREMENT SECTION (DISABLED)

        The commented-out section below was used for height measuring using the laser line.

        This code snippet was designed to:
        1. Turn on the laser
        2. Capture the current position of the robot
        3. Use the camera to get the current image and calculate the TCP to image center offsets
        4. Move the robot to a specific position for height measurement
        5. Capture a new image at the height measurement point
        6. Estimate the height by measuring the captured image
        7. Turn off the laser
        8. Return the robot to its start position after height measurement

        # laserController = Laser()
        # laserController.turnOn()
        #
        # initialX = self.robotService.startPosition[0]
        # initialY = self.robotService.startPosition[1]
        # image = self.visionService.captureImage()
        #
        # cameraToRobotMatrix = self.visionService.getCameraToRobotMatrix()
        # imageCenter = (image.shape[1] // 2, image.shape[0] // 2)
        # offsets = Teaching.calculateTcpToImageCenterOffsets(
        #     imageCenter, initialX, initialY, cameraToRobotMatrix
        # )
        #
        # position = [centroid[0], centroid[1] + offsets[1], 300, 180, 0, 0]
        # self.robotService.moveToPosition(
        #     position, 0, 0, 100, 30, waitToReachPosition=True
        # )
        #
        # time.sleep(1)
        #
        # # Capture new frame from the height measurement point
        # newFrame = self.visionService.captureImage()
        # estimatedHeight = self.measureHeight(newFrame, maxAttempts=10, debug=False)
        # laserController.turnOff()
        # self.robotService.moveToStartPosition()
        """

        # Set default values (height measurement is currently disabled)
        scaleFactor = 1
        estimatedHeight = 4  # Default height value

        # Set message based on whether contours were found automatically
        if result and contours is not None and len(contours) > 0:
            message = "Workpiece created successfully"
        else:
            message = "No contours found - opening contour editor for manual setup"

        # Prepare return data
        print("originalcnt sent: ", originalContours)
        data = (
            estimatedHeight,
            contourArea,
            contour,
            scaleFactor,
            createWpImage,
            message,
            originalContours
        )

        # Always return True to allow contour editor to open, even if no contours found
        return True, data

    def updateToolChangerStation(self):
        """
           Updates the tool changer station by detecting ArUco markers, validating tool-slot alignment, and
           ensuring the correct tool is placed under each slot.
           This process includes image processing, tool-slot mapping, and robot motion.

           Steps involved:
           1. **Get Tool Changer Info**:
              Retrieve the current tool changer information, including slot and tool mappings.

           2. **ArUco Marker Detection**:
              Detect ArUco markers in the workspace to identify the positions of slots and tools.

           3. **Validate Marker Presence**:
              Check if any ArUco markers are detected. If no markers are found, return an error.

           4. **Filter and Process Valid Markers**:
              Filter the detected markers to only include those corresponding to valid slot and tool IDs.

           5. **Sort Slots and Tools by Y-coordinate**:
              Sort the detected slots and tools vertically (from top to bottom) to simplify tool-slot pairing.

           6. **Map Slots to Tools**:
              For each detected slot, find the nearest tool that is correctly aligned and positioned below the slot.

           7. **Update Slot Availability**:
              If no tool is detected under a slot, mark the slot as available. If a tool is detected, mark the slot as unavailable.

           8. **Validate Slot-Tool Pairing**:
              Compare the detected tool to the expected tool for each slot. If an incorrect tool is detected, it is flagged as misplaced.

           9. **Draw Marker Information**:
              Annotate the image with the detected slots, tools, and any misplaced tools for visual inspection.

           10. **Move Robot for Tool Check**:
               Move the robot to a predefined position to perform a final tool check.

           11. **Final Tool Check**:
               After the robot has moved, detect markers again to confirm the tool present at the tool changer.
           """
        toolChanger = self.robotService.toolChanger

        slotToolMap = toolChanger.getSlotToolMap()

        X_TOLERANCE = 150  # Allowable X-offset between slot and tool
        slotIds = toolChanger.getSlotIds()  # Slot markers
        toolIds = toolChanger.getReservedForIds()  # Tool markers
        validIds = set(slotIds + toolIds)  # Combine slot & tool IDs into a valid set
        expected_mapping = dict(zip(slotIds, toolIds))  # Expected slot-to-tool mapping

        time.sleep(1)

        arucoCorners, arucoIds, image = self.visionService.detectArucoMarkers()

        if arucoIds is None or len(arucoIds) == 0:
            print("No ArUco markers detected!")
            return False, "No ArUco markers detected!"

        arucoIds = arucoIds.flatten()  # Convert to a flat list

        #Strict filtering: Only process markers in slotIds or toolIds
        validMarkers = [(id, corners) for id, corners in zip(arucoIds, arucoCorners) if id in validIds]
        filteredIds = [id for id, _ in validMarkers]  # Only valid IDs

        if not validMarkers:
            print("No valid markers detected!")
            return False, "No valid markers detected!"

        detected_slots = []
        detected_tools = []
        marker_positions = {}  # Store marker bounding boxes

        # Process only valid markers
        for marker_id, corners in validMarkers:
            center_x = np.mean(corners[0][:, 0])  # Get center X
            center_y = np.mean(corners[0][:, 1])  # Get center Y
            marker_positions[marker_id] = corners[0]  # Store full bounding box

            if marker_id in slotIds:
                detected_slots.append((marker_id, center_x, center_y))  # Store slot marker
            elif marker_id in toolIds:
                detected_tools.append((marker_id, center_x, center_y))  # Store tool marker

        # Print detected slots and tools
        print("Detected Slots:", detected_slots)
        print("Detected Tools:", detected_tools)

        # Sort by Y-coordinate (top-to-bottom)
        detected_slots.sort(key=lambda x: x[2])  # Sort slots by Y
        detected_tools.sort(key=lambda x: x[2])  # Sort tools by Y

        correct_placement = True
        detected_mapping = {}
        misplaced_tools = []  # Store misplaced tools for red bounding box

        print("\nDEBUG: Detected Slot-Tool Mapping:")
        for slot_id, slot_x, slot_y in detected_slots:
            # Find the nearest tool below the slot
            matching_tool = -1  # Default if no tool is found
            if len(detected_tools) > 0:
                tool_id = detected_tools[0][0]

            for tool_id, tool_x, tool_y in detected_tools:
                if abs(slot_x - tool_x) < X_TOLERANCE and tool_y > slot_y:  # X alignment + tool below slot
                    matching_tool = tool_id
                    break  # Stop after finding the first valid tool

            detected_mapping[slot_id] = matching_tool  # Store detected slot-tool pairs

            print(f"   - Slot {slot_id} в†’ Detected Tool: {matching_tool} (Expected: {expected_mapping[slot_id]})")

            # Call tool changer functions
            if matching_tool == -1:
                print(f"Setting {slot_id} as available!")
                self.robotService.toolChanger.setSlotAvailable(slot_id)
            else:
                self.robotService.toolChanger.setSlotNotAvailable(slot_id)

            print("ToolChanger: ", self.robotService.toolChanger.slots)

            # Validate slot-tool match (allowing -1 but NOT incorrect tools)
            expected_tool = expected_mapping.get(slot_id)
            if matching_tool != -1 and expected_tool != matching_tool:
                correct_placement = False
                print(f"ERROR: Wrong tool under slot {slot_id}: Expected {expected_tool}, Found {matching_tool}")
                misplaced_tools.append(matching_tool)  # Store misplaced tool for red box contour_editor

        if correct_placement:
            print("All tools are correctly placed (or missing but allowed)!")
        else:
            print(f"Incorrect placement detected! Mapping: {detected_mapping}")

        # Draw only valid ArUco markers on the frame
        filteredCorners = [corners for id, corners in validMarkers]  # Filtered corners for valid markers
        cv2.aruco.drawDetectedMarkers(image, filteredCorners, np.array(filteredIds, dtype=np.int32))

        # Draw red rectangles around misplaced tools
        for tool_id in misplaced_tools:
            if tool_id in marker_positions:
                corners = marker_positions[tool_id].astype(int)
                cv2.polylines(image, [corners], isClosed=True, color=(0, 0, 255), thickness=3)  # Red bounding box

        toolCheckPos = [-350, 650, 200, 180, 0, 90]
        self.robotService.moveToPosition(toolCheckPos, 0, 0, 100, 30)

        maxAttempts = 30

        filteredIds = []
        while maxAttempts > 0:
            arucoCorners, arucoIds, image = self.visionService.detectArucoMarkers(flip=True)
            if arucoIds is not None:
                image_height = image.shape[0]
                # рџ”№ Strict filtering: Only process markers in slotIds or toolIds and in the lower half of the image
                validMarkers = [(id, corners) for id, corners in zip(arucoIds, arucoCorners)
                                if id.item() in validIds and np.mean(corners[0][:, 1]) > image_height / 2]

                filteredIds = [id for id, _ in validMarkers]  # Only valid IDs

                if validMarkers:
                    break
            maxAttempts -= 1

        if len(filteredIds) != 0:
            currentTool = int(arucoIds[0])
            print("Current tool in tool check: ", currentTool)
            self.robotService.currentGripper = currentTool
        else:
            print("No tool detected in tool check")

    def handleBelt(self):

        from archive.belts.BeltControl import BeltControl

        beltControl = BeltControl()

        pos = [-166.598,467.614,521.953,-180,0,90]
        pos2 = [-166.598,467.614,485,-180,0,90]
        pos3 = [25,467.614,485,-180,0,90]
        pos4 = [25,467.614,490,-180,0,90]
        pos5 = [25,467.614,550,-180,0,90]

        pos6 = [382,416,500,-180,0,90] # Spray pos 1
        pos7 = [146.637,416.091,500,-180,0,90] # Spray pos 2
        self.robotService.moveToPosition(pos,0,0,30,30)

        self.robotService.pump.turnOn(self.robotService.robot)
        import time
        time.sleep(5)

        #FEED BELT
        self.robotService.robot.moveL(pos2,0,0,100,30,1)
        self.robotService.robot.moveL(pos3,0,0,100,30,0)
        self.robotService._waitForRobotToReachPosition(pos3,1,0.1)

        self.robotService.pump.turnOff(self.robotService.robot)
        beltControl.shouldRun = True
        threading.Thread(target=beltControl.run, daemon=True).start()

        self.robotService.robot.moveL(pos4,0,0,100,30,1)
        self.robotService.robot.moveL(pos2, 0, 0, 100, 30, 1)
        self.robotService.robot.moveL(pos, 0, 0, 100, 30, 1)
        self.robotService.robot.moveL(pos5, 0, 0, 100, 30, 1)

        iterations = 4
        while iterations > 0:
            self.robotService.robot.moveL(pos6, 0, 0, 100, 30, 1)
            self.robotService._waitForRobotToReachPosition(pos6, 1, 0.1)

            while beltControl.isRunning:
                print("Belt is running")

            self.glueNozzleService.startGlueDotsDispensing()
            self.robotService.robot.moveL(pos7,0,0,100,30,1)
            self.robotService._waitForRobotToReachPosition(pos7, 1, 0.1)
            self.glueNozzleService.stopGlueDispensing()

            #beltControl.run()
            beltControl.shouldRun = True
            threading.Thread(target=beltControl.run, daemon=True).start()

            iterations -=1

        pos8 = [146.637,416.091,550,-180,0,90] # Spray pos 2
        self.robotService.robot.moveL(pos8, 0, 0, 100, 30, 1)
        self.robotService.robot.moveL(pos, 0, 0, 100, 30, 1)



        print("Running belt")

    def testRun(self):
        from GlueDispensingApplication.tools.GlueSprayService import GlueSprayService
        service = GlueSprayService()

        glueSettings = self.settingsManager.glue_settings
        print("Glue Settings: ", glueSettings)
        """ EXTRACT SETTINGS"""
        sprayWidth = glueSettings.get_spray_width()
        sprayingHeight = glueSettings.get_spraying_height()
        fanSpeed = glueSettings.get_fan_speed()
        delay = glueSettings.get_time_between_generator_and_glue()
        motorSpeed=glueSettings.get_motor_speed()
        stepsReverse = glueSettings.get_steps_reverse()
        speedReverse = glueSettings.get_speed_reverse()
        rzAngle = glueSettings.get_rz_angle()
        glueType = glueSettings.get_glue_type()
        time_before_spray = glueSettings.get_time_before_motion()
        reach_position_threshold = glueSettings.get_reach_position_threshold()

        glueType_normalized = glueType.strip()
        if glueType_normalized == "Type A":
            glue_addresses = service.glueA_addresses
        elif glueType_normalized == "Type B":
            glue_addresses = service.glueB_addresses
        elif glueType_normalized == "Type C":
            glue_addresses = service.glueC_addresses
        elif glueType_normalized == "Type D":
            glue_addresses = service.glueD_addresses
        else:
            raise ValueError(f"Unknown glue type: {glueType}")



        # # # """ ROBOT PROGRAM """

        # point = [-400,350,sprayingHeight,180,0,rzAngle]
        # point2 = [100,350,sprayingHeight,180,0,rzAngle]
        # points = [point, point2]
        #
        # self.robotService.moveToPosition(point, 0, 0, 60, 100)
        # self.robotService._waitForRobotToReachPosition(point, 1, 0.1)
        #
        # service.startGlueDispensing(glue_addresses,speed=motorSpeed,stepsReverse=stepsReverse,speedReverse=speedReverse,delay=delay,fanSpeed=fanSpeed)
        #
        # time.sleep(time_before_spray)
        #
        # self.robotService.robot.moveL(point2, 0, 0, 30, 100, 1)
        # self.robotService._waitForRobotToReachPosition(point2, reach_position_threshold, 0.1)
        #
        # service.stopGlueDispensing(glue_addresses)

        rzAngle = 0
        """ ROBOT PROGRAM """
        y = 350
        startPos = [-300,350,sprayingHeight,180,0,rzAngle]
        endPos = [300,350,sprayingHeight,180,0,rzAngle]
        points = [startPos, endPos, startPos]
        self.robotService.robot.moveL(startPos, ROBOT_TOOL, ROBOT_USER, 100, 30, 1)
        self.robotService._waitForRobotToReachPosition(startPos, 1, 0.1)

        service.startGlueDispensing(glue_addresses, speed=motorSpeed, stepsReverse=stepsReverse,
                                    speedReverse=speedReverse, delay=delay, fanSpeed=fanSpeed)
        time.sleep(time_before_spray)

        direction = -300  # Start with left
        while y < 650:
            pos1 = [direction, y, sprayingHeight, 180, 0, rzAngle]
            rzAngle +=4
            pos2 = [direction * -1, y, sprayingHeight, 180, 0, rzAngle]  # Alternate direction
            rzAngle += 4
            pos3 = [direction * -1, y + 25, sprayingHeight, 180, 0, rzAngle]  # Alternate direction
            points = [pos1, pos2, pos3]
            print("Points: ", points)

            self.robotService.robot.moveL(pos1, ROBOT_TOOL, ROBOT_USER, vel=30, acc=100, blendR=1)
            self.robotService.robot.moveL(pos2, ROBOT_TOOL, ROBOT_USER, vel=30, acc=100, blendR=1)
            self.robotService.robot.moveL(pos3, ROBOT_TOOL, ROBOT_USER, vel=30, acc=100, blendR=1)

            y = y + 25
            direction *= -1  # Switch direction

        posEnd = [-299.984, 650, sprayingHeight, 180, 0, rzAngle]
        self.robotService._waitForRobotToReachPosition(posEnd, 10, 0.1)
        service.stopGlueDispensing(glue_addresses)

        posEnd = [-299.987, 650, sprayingHeight+150, 180, 0, rzAngle]
        self.robotService.robot.moveCart(posEnd, ROBOT_TOOL, ROBOT_USER, vel=30, acc=100)


    def handleExecuteFromGallery(self, workpiece):

        def flatten_point(p):
            """Flattens nested point lists like [[[x, y]]] -> [x, y]"""
            while isinstance(p, (list, tuple)) and len(p) == 1:
                p = p[0]
            return p

        # print("Handling execute from gallery: ", workpiece)
        sprayPatternsList = workpiece.sprayPattern.get("Contour", [])
        robotPaths = []

        for pattern in sprayPatternsList:
            contour_arr = pattern.get("contour", [])
            settings = pattern.get("settings", {})

            # Sanitize and convert points to float
            points = []

            for p in contour_arr:
                coords = p[0] if isinstance(p[0], (list, tuple, np.ndarray)) else p
                # Ensure coords[0] and coords[1] are scalars
                x = float(coords[0])
                y = float(coords[1])

                points.append([x, y])

            if points:
                # Prepare points for OpenCV: shape (N, 1, 2)
                np_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)

                # Transform to robot coordinates
                transformed = utils.applyTransformation(self.visionService.cameraToRobotMatrix, np_points)
                finalContour = []
                for point in transformed:
                    print("Point: ", point)
                    point = flatten_point(point)
                    x = float(point[0])
                    y = float(point[1])

                    z_str = str(settings.get(GlueSettingKey.SPRAYING_HEIGHT.value, 150)).replace(",", "")
                    z = float(z_str)
                    rx = 180
                    ry = 0
                    rz = float(settings.get(GlueSettingKey.RZ_ANGLE.value, 0))

                    newPoint = [x, y, z, rx, ry, rz]
                    finalContour.append(newPoint)

                robotPaths.append([finalContour, settings])

        self.robotService.moveToCalibrationPosition()
        # self.robotService._waitForRobotToReachPosition(self.robotService.calibrationPosition, 1, delay=0)
        self.robotService.traceContours(robotPaths)
        print("Paths to trace: ", robotPaths)


