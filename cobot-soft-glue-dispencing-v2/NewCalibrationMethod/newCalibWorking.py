import time

import cv2
import numpy as np
from VisionSystem.VisionSystem import VisionSystem
from GlueDispensingApplication.robot.RobotConfig import *
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.settings.SettingsService import SettingsService

class DebugDraw:
    def __init__(self):
        # drawing settings
        self.marker_color = (0, 255, 0)  # Green
        self.marker_radius = 6
        self.text_color = (0, 255, 0)  # Green
        self.text_scale = 0.7
        self.text_thickness = 2
        self.text_font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_offset = 10  # Offset for text position relative to marker center
        self.text_position = (self.marker_radius + self.text_offset, self.marker_radius + self.text_offset)
        self.image_center_color = (255, 0, 0)  # Blue
        self.image_center_radius = 4
        self.circle_thickness = -1

    def draw_marker_center(self, frame, marker_id,marker_centers):
        """Draw marker center on frame"""
        if marker_id in marker_centers:
            center_px = marker_centers[marker_id]
            cv2.circle(frame, center_px, self.marker_radius, self.marker_color, self.circle_thickness)
            cv2.putText(frame, f"ID {marker_id}", (center_px[0] + self.text_offset, center_px[1]),
                        self.text_font, self.text_scale, self.text_color, self.text_thickness)
            return True
        return False

    def draw_image_center(self, frame):
        """Draw image center on frame"""
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        image_center_px = (
            frame_width // 2,
            frame_height // 2
        )

        cv2.circle(frame, image_center_px, self.image_center_radius, self.image_center_color, self.circle_thickness)

class CalibrationPipeline:
    def __init__(self, required_ids=None,debug=True):
        # --- STATES ---
        self.debug = debug
        if self.debug:
            self.debug_draw = DebugDraw()

        self.states = {
            "INITIALIZING": 0,
            "LOOKING_FOR_CHESSBOARD": 1,
            "CHESSBOARD_FOUND": 2,
            "LOOKING_FOR_ARUCO_MARKERS": 3,
            "ALL_ARUCO_FOUND": 4,
            "COMPUTE_OFFSETS": 5,
            "ALIGN_ROBOT": 6,
            "DONE":7
        }
        self.current_state = self.states["INITIALIZING"]

        # --- Vision system ---
        self.system = VisionSystem()
        self.system.camera_settings.set_draw_contours(False)

        # --- Robot ---
        self.robot = RobotWrapper(ROBOT_IP)
        self.settings_service = SettingsService()
        self.robot_service = RobotService(self.robot, self.settings_service,None)
        self.robot_service.moveToCalibrationPosition()

        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.square_size_mm = self.system.camera_settings.get_square_size_mm()
        self.bottom_left_chessboard_corner_px = None

        # ArUco requirements
        self.required_ids = set(required_ids if required_ids is not None else [])
        self.detected_ids = set()
        self.marker_centers = {}
        self.markers_offsets_mm = {}
        self.current_marker_id = 0

        self.Z_current = self.robot_service.getCurrentPosition()[2]
        self.Z_target = 150  # desired height
        self.ppm_scale = self.Z_current / self.Z_target

        self.marker_centers_mm = {}
        self.robot_positions_for_calibration = {}

        self.PPM = None

        print(f"Looking for chessboard with size: {self.chessboard_size}")

    # --- Utils ---
    def compute_ppm_from_corners(self, corners_refined):
        """Compute pixels-per-mm from chessboard corners"""
        cols, rows = self.chessboard_size
        pts = corners_refined.reshape(-1, 2)  # (N,2)
        horiz, vert = [], []

        for r in range(rows):  # horizontal neighbors
            base = r * cols
            for c in range(cols - 1):
                i1 = base + c
                i2 = base + c + 1
                horiz.append(np.linalg.norm(pts[i1] - pts[i2]))

        for r in range(rows - 1):  # vertical neighbors
            for c in range(cols):
                i1 = r * cols + c
                i2 = (r + 1) * cols + c
                vert.append(np.linalg.norm(pts[i1] - pts[i2]))

        all_d = np.array(horiz + vert, dtype=np.float32)
        if all_d.size == 0:
            return None

        avg_square_px = float(np.mean(all_d))
        ppm = avg_square_px / float(self.square_size_mm)
        return ppm

    def find_chessboard_and_compute_ppm(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            print(f"Found chessboard! Detected {len(corners)} corners")
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria
            )

            # --- Store bottom-left corner of chessboard in pixels ---
            cols, rows = self.chessboard_size
            self.bottom_left_chessboard_corner_px = corners_refined[(rows - 1) * cols, 0]  # (x, y)
            print(f"Bottom-left chessboard corner (px): {self.bottom_left_chessboard_corner_px}")

            ppm = self.compute_ppm_from_corners(corners_refined)
            cv2.drawChessboardCorners(frame, self.chessboard_size, corners_refined, ret)
            return True, ppm
        else:
            cv2.putText(frame, "No chessboard detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.bottom_left_chessboard_corner_px = None
            return False, None

    def find_required_aruco_markers(self, frame):
        cv2.putText(frame, "Looking for ArUco markers...", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        arucoCorners, arucoIds, image = self.system.detectArucoMarkers(frame)

        if arucoIds is not None:
            print(f"Detected {len(arucoIds)} ArUco markers")
            print(f"Marker IDs: {arucoIds.flatten()}")

            for i, marker_id in enumerate(arucoIds.flatten()):
                if marker_id in self.required_ids:
                    self.detected_ids.add(marker_id)
                    center = tuple(np.mean(arucoCorners[i][0], axis=0).astype(int))
                    self.marker_centers[marker_id] = center

                    # Draw center on frame
                    cv2.circle(frame, center, 5, (0, 255, 0), -1)
                    cv2.putText(frame, f"ID {marker_id}", (center[0] + 10, center[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            print(f"Currently have: {self.detected_ids}")
            print(f"Still missing: {self.required_ids - self.detected_ids}")

            all_found = self.required_ids.issubset(self.detected_ids)
            if all_found:
                print("🎯 All required ArUco markers found!")
            return frame, all_found

        return frame, False

    def detect_specific_marker(self, marker_id, skip_frames_after_motion=True, skip_frames=5):
        marker_found = False
        arucoCorners = []
        arucoIds = []
        new_frame = None
        while not marker_found:
            _, new_frame, _ = self.system.run()

            if skip_frames_after_motion is True and skip_frames > 0:
                skip_frames -= 1
                continue

            arucoCorners, arucoIds, image = self.system.detectArucoMarkers(new_frame)
            print(f"Detection loop for specific marker {marker_id}")
            print(
                f"Detected {len(arucoIds)} ArUco markers at new pose ID: {arucoIds if arucoIds is not None else 'None'}")
            if arucoIds is not None and marker_id in arucoIds:
                marker_found = True

        return arucoCorners, arucoIds,new_frame

    def update_marker_centers(self, marker_id,corners,ids):
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id != marker_id:
                continue
            # update marker center in pixels
            center_px = tuple(np.mean(corners[i][0], axis=0).astype(int))
            self.marker_centers[marker_id] = center_px

            # Convert to mm relative to bottom-left of chessboard
            x_mm = (center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
            y_mm = (self.bottom_left_chessboard_corner_px[1] - center_px[1]) / self.PPM

            # update marker center in mm
            self.marker_centers_mm[marker_id] = (x_mm, y_mm)
            print(f"Updated marker {marker_id} position in mm: {self.marker_centers_mm[marker_id]}")

    # --- Main loop ---
    def run(self):
        while True:
            _, frame, _ = self.system.run()
            print("Current state:", self.current_state)
            if self.current_state == self.states["INITIALIZING"]:
                if frame is None:
                    continue
                else:
                    print("System initialized ✅")
                    self.current_state = self.states["LOOKING_FOR_CHESSBOARD"]

            elif self.current_state == self.states["LOOKING_FOR_CHESSBOARD"]:
                found, ppm = self.find_chessboard_and_compute_ppm(frame)
                if found:
                    self.PPM = ppm
                    print(f"✅ PPM computed: {self.PPM:.3f} px/mm")
                    self.current_state = self.states["CHESSBOARD_FOUND"]

            elif self.current_state == self.states["CHESSBOARD_FOUND"]:
                cv2.putText(frame, f"PPM calibrated: {self.PPM:.3f} px/mm",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                self.current_state = self.states["LOOKING_FOR_ARUCO_MARKERS"]

            elif self.current_state == self.states["LOOKING_FOR_ARUCO_MARKERS"]:
                frame, all_found = self.find_required_aruco_markers(frame)
                if all_found:
                    self.current_state = self.states["ALL_ARUCO_FOUND"]

            elif self.current_state == self.states["ALL_ARUCO_FOUND"]:
                cv2.putText(frame, "All required ArUco markers found !", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                self.marker_centers_mm = {}

                # Draw marker centers and convert to mm relative to bottom-left of chessboard

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    for marker_id, center_px in self.marker_centers.items():
                        # Draw in pixels

                        if self.debug_draw:
                            self.debug_draw.draw_marker_center(frame, marker_id,self.marker_centers)

                        # Convert to mm relative to bottom-left
                        x_mm = (center_px[0] - bottom_left_px[0]) / self.PPM
                        y_mm = (bottom_left_px[1] - center_px[1]) / self.PPM  # y relative to bottom-left

                        self.marker_centers_mm[marker_id] = (x_mm, y_mm)

                print("Marker centers in mm relative to bottom-left:")

                for marker_id, center_mm in self.marker_centers_mm.items():
                    print(f"ID {marker_id}: {center_mm}")

                self.current_state = self.states["COMPUTE_OFFSETS"]

            elif self.current_state == self.states["COMPUTE_OFFSETS"]:

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    # Image center in pixels
                    image_center_px = (self.system.camera_settings.get_camera_width() // 2, self.system.camera_settings.get_camera_height() // 2)
                    # Convert image center to mm relative to bottom-left of chessboard
                    center_x_mm = (image_center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
                    center_y_mm = (self.bottom_left_chessboard_corner_px[1] - image_center_px[1]) / self.PPM
                    print(f"Image center in mm relative to bottom-left: ({center_x_mm:.2f}, {center_y_mm:.2f})")

                    # Calculate offsets for all markers relative to image center
                    for marker_id, marker_mm in self.marker_centers_mm.items():
                        offset_x = marker_mm[0] - center_x_mm
                        offset_y = marker_mm[1] - center_y_mm
                        print(
                            f"Marker {marker_id}: position in mm = {marker_mm}, offset from image center = (X={offset_x:.2f}, Y={offset_y:.2f})")
                        self.markers_offsets_mm[marker_id] = (offset_x, offset_y)
                    self.current_state = self.states["ALIGN_ROBOT"]


            elif self.current_state == self.states["ALIGN_ROBOT"]:
                marker_id = self.current_marker_id

                # (1) Precomputed offset from calibration pose to marker
                calib_to_marker = self.markers_offsets_mm.get(marker_id, (0, 0))

                # (2) Current robot pose
                current_pose = self.robot_service.getCurrentPosition()
                x, y, z, rx, ry, rz = current_pose

                # (3) Calibration pose
                calib_pose = CALIBRATION_POS
                cx, cy, cz, crx, cry, crz = calib_pose

                # (4) Compute delta: calibration -> current
                calib_to_current = (x - cx, y - cy)

                # (5) Compute current -> marker
                current_to_marker = (
                    calib_to_marker[0] - calib_to_current[0],
                    calib_to_marker[1] - calib_to_current[1]
                )

                # (6) Apply correction at current pose
                x_new = x + current_to_marker[0]
                y_new = y + current_to_marker[1]
                z_new = self.Z_target
                new_position = [x_new, y_new, z_new, rx, ry, rz]

                print(f"Moving robot from current pose to marker {marker_id}: {new_position}")
                self.robot_service.moveToPosition(new_position, ROBOT_TOOL, ROBOT_USER, 20, 100, True)

                # --- Re-detect marker 4 at new height ---
                arucoCorners,arucoIds,_ = self.detect_specific_marker(marker_id)

                self.update_marker_centers(marker_id,arucoCorners,arucoIds)

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    # if self.debug_draw:
                    #     self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)


                if marker_id in self.marker_centers_mm:
                    new_marker_px = self.marker_centers[marker_id]
                    # Compute new offset relative to image center
                    image_center_px = (
                        self.system.camera_settings.get_camera_width() // 2,
                        self.system.camera_settings.get_camera_height() // 2
                    )

                    if self.debug:
                        self.debug_draw.draw_image_center(frame)

                    newPpm = self.PPM * self.ppm_scale
                    print(f"New PPM at Z={self.Z_target}mm: {newPpm:.3f} px/mm")

                    # Calculate new offsets in pixels
                    new_offset_X_px= new_marker_px[0] - image_center_px[0]
                    new_offset_Y_px= new_marker_px[1] - image_center_px[1]

                    # Convert offsets to mm
                    new_offset_x_mm = new_offset_X_px/newPpm
                    new_offset_y_mm = new_offset_Y_px/newPpm

                    # Update robot position with new offsets
                    new_current_pose = self.robot_service.getCurrentPosition()
                    x,y,z,rx,ry,rz = new_current_pose
                    x+= new_offset_x_mm
                    y+= -new_offset_y_mm
                    new_current_pose = [x,y,z,rx,ry,rz]
                    self.robot_service.moveToPosition(new_current_pose, ROBOT_TOOL, ROBOT_USER, 20, 100, True)

                    print(f"New marker {marker_id} offset from image center at Z={self.Z_target}mm: "
                          f"X={new_offset_x_mm:.2f}, Y={new_offset_y_mm:.2f}")

                    # Draw marker 4 on the frame
                    # if self.debug_draw:
                    #     self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)


                    self.current_state= self.states["DONE"]
                else:

                    print(f"Marker {marker_id} not detected at new pose.")
            elif self.current_state == self.states["DONE"]:
                marker_id = self.current_marker_id

                # FOR DEBUGGING AND VALIDATION ONLY REDETECT THE MARKER AND SHOW IT`S CENTER
                arucoCorners, arucoIds,frame = self.detect_specific_marker(marker_id,skip_frames_after_motion=False, skip_frames=0)

                self.update_marker_centers(marker_id, arucoCorners, arucoIds)

                if self.debug_draw:
                    self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)
                    self.debug_draw.draw_image_center(frame)

                cv2.imwrite(f"aligned_center_marker_{self.current_marker_id}.png", frame)

                cv2.putText(frame, "Calibration complete! Press 'q' to exit.", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Get robot position after alignment and store it for calibration
                current_robot_position = self.robot_service.getCurrentPosition()
                self.robot_positions_for_calibration[marker_id] = current_robot_position
                print(f"Robot position for marker {marker_id} after alignment: {current_robot_position}")

                if self.current_marker_id < len(self.required_ids) - 1:
                    self.current_marker_id += 1
                    self.current_state = self.states["ALIGN_ROBOT"]
                else:
                    print("All markers processed. Calibration complete!")
                    self.current_state = self.states["DONE"]
                    break

            if frame is not None:
                cv2.imshow("Calibration State Machine", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    pipeline = CalibrationPipeline(required_ids=[0, 1, 2, 3, 4, 5, 6])
    pipeline.run()
