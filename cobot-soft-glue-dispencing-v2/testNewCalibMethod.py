import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QGridLayout,
                             QGroupBox, QTextEdit, QSplitter)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QFont

from GlueDispensingApplication.robot.RobotConfig import *
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.settings.SettingsService import SettingsService
from VisionSystem.VisionSystem import VisionSystem

TARGET_WORKING_HEIGHT_MM = 250.0  # Target working height for robot alignment
import threading
from PyQt6.QtCore import QThread, pyqtSignal


class CameraThread(QThread):
    frame_ready = pyqtSignal(object)  # Signal to emit new frames

    def __init__(self, vision_system):
        super().__init__()
        self.vision_system = vision_system
        self.running = True

    def run(self):
        """Main camera loop running in separate thread"""
        while self.running:
            try:
                _, frame, _ = self.vision_system.run()
                if frame is not None:
                    self.frame_ready.emit(frame.copy())

                # Small delay to control frame rate (~30 FPS)
                self.msleep(33)  # 33ms = ~30 FPS

            except Exception as e:
                print(f"Camera thread error: {e}")
                self.msleep(100)  # Wait a bit before retrying

    def stop(self):
        """Stop the camera thread"""
        self.running = False
        self.wait()  # Wait for thread to finish

class ChessboardAlignmentGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.center_marker_label = None
        self.ppm_label = None
        self.x_offset_label = None
        self.y_offset_label = None
        self.distance_label = None
        self.corners_label = None
        self.aruco_collection_label = None
        self.alignment_status_label = None
        self.setWindowTitle("ArUco + Chessboard Robot Alignment System")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize systems
        self.system = VisionSystem()  # ← Move this BEFORE camera thread
        self.camera_thread = CameraThread(self.system)
        self.camera_thread.frame_ready.connect(self.on_new_frame)
        self.settingsService = SettingsService()
        self.robot = RobotWrapper(ROBOT_IP)
        self.robotService = RobotService(self.robot, self.settingsService, None)

        # Chessboard settings (for PPM calculation only)
        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.system.camera_settings.set_draw_contours(False)

        # ArUco detector setup
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        # Required ArUco marker IDs
        self.required_marker_ids = set(range(9))  # IDs 0-8
        self.collected_markers = {}  # Store markers as they're found across frames
        self.markers_collection_complete = False

        # Detection variables
        self.stored_corners = None  # Chessboard corners for PPM only
        self.corners_found = False
        self.aruco_markers = {}  # Final set of ArUco markers to use
        self.center_marker_found = False  # Whether ArUco marker ID=4 is found
        self.aligned = False
        self.verification_corners = None
        self.verification_found = False
        self.verification_aruco_markers = {}
        self.verification_center_found = False
        self.current_frame = None
        self.ppm = None
        self.offset_x_mm = 0.0
        self.offset_y_mm = 0.0
        self.ALIGNMENT_THRESHOLD_MM = 2.0

        # Setup UI
        self.setup_ui()

        self.camera_thread.start()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)

        # Left side - Camera feed
        camera_widget = QWidget()
        camera_layout = QVBoxLayout(camera_widget)

        # Camera display
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid gray; background-color: black;")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.camera_label)

        # Status label
        self.status_label = QLabel("System Starting...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        camera_layout.addWidget(self.status_label)

        main_splitter.addWidget(camera_widget)

        # Right side - Controls and info
        control_widget = QWidget()
        control_widget.setMaximumWidth(350)
        control_layout = QVBoxLayout(control_widget)

        # Control buttons group
        self.setup_control_buttons(control_layout)

        # Information display group
        self.setup_info_display(control_layout)

        # Log display
        self.setup_log_display(control_layout)

        main_splitter.addWidget(control_widget)

        # Set splitter proportions
        main_splitter.setSizes([800, 350])

    def setup_control_buttons(self, parent_layout):
        button_group = QGroupBox("Controls")
        button_layout = QVBoxLayout(button_group)

        # move to claibration position button
        self.move_to_calibration_position_button = QPushButton("Move to calibration position")
        self.move_to_calibration_position_button.setEnabled(True)
        self.move_to_calibration_position_button.setText("🔄 Move to Calibration Position")
        self.move_to_calibration_position_button.clicked.connect(self.robotService.moveToCalibrationPosition)
        button_layout.addWidget(self.move_to_calibration_position_button)


        # Find Patterns button
        self.find_button = QPushButton("🎯 Find Chessboard & ArUco")
        self.find_button.setMinimumHeight(40)
        self.find_button.clicked.connect(self.find_patterns)
        self.find_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        button_layout.addWidget(self.find_button)

        # Compute Offsets button
        self.compute_button = QPushButton("📐 Compute X/Y Offsets")
        self.compute_button.setMinimumHeight(40)
        self.compute_button.clicked.connect(self.compute_offsets)
        self.compute_button.setEnabled(False)
        self.compute_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        button_layout.addWidget(self.compute_button)

        # Align Robot button
        self.align_button = QPushButton("🤖 Align Robot")
        self.align_button.setMinimumHeight(40)
        self.align_button.clicked.connect(self.align_robot)
        self.align_button.setEnabled(False)
        self.align_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        button_layout.addWidget(self.align_button)

        # Reset button
        self.reset_button = QPushButton("🔄 Reset All")
        self.reset_button.setMinimumHeight(30)
        self.reset_button.clicked.connect(self.reset_all)
        self.reset_button.setStyleSheet("font-size: 11px;")
        button_layout.addWidget(self.reset_button)

        parent_layout.addWidget(button_group)

    def setup_info_display(self, parent_layout):
        info_group = QGroupBox("Detection Information")
        info_layout = QGridLayout(info_group)

        # Labels for information display
        labels = [
            ("Chessboard Size:", "chessboard_size_label"),
            ("Corners Found:", "corners_label"),
            ("ArUco Collection:", "aruco_collection_label"),
            ("Collected Markers:", "collected_markers_label"),
            ("Center Marker (ID=4):", "center_marker_label"),
            ("PPM:", "ppm_label"),
            ("X Offset:", "x_offset_label"),
            ("Y Offset:", "y_offset_label"),
            ("Distance:", "distance_label"),
            ("Alignment Status:", "alignment_status_label")
        ]

        for i, (text, attr_name) in enumerate(labels):
            label = QLabel(text)
            label.setStyleSheet("font-weight: bold;")
            value_label = QLabel("N/A")
            value_label.setStyleSheet("color: blue;")

            info_layout.addWidget(label, i, 0)
            info_layout.addWidget(value_label, i, 1)
            setattr(self, attr_name, value_label)

        # Initialize values
        self.chessboard_size_label.setText(f"{self.chessboard_size[0]}x{self.chessboard_size[1]}")

        parent_layout.addWidget(info_group)

    def setup_log_display(self, parent_layout):
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 9px;")
        log_layout.addWidget(self.log_text)

        parent_layout.addWidget(log_group)

        # Add initial log message
        self.log_message(f"System initialized. Looking for chessboard: {self.chessboard_size} and ArUco markers 0-8")

    def log_message(self, message):
        self.log_text.append(f"[INFO] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def on_new_frame(self, frame):
        """Handle new frame from camera thread (runs in main thread)"""
        try:
            self.current_frame = frame.copy()

            # Continuously collect ArUco markers if collection is not complete
            if not self.markers_collection_complete:
                self.collect_aruco_markers(frame)

            # Process frame for display
            display_frame = self.process_frame_for_display(frame)

            # Convert to Qt format and display
            self.display_frame(display_frame)

        except Exception as e:
            self.log_message(f"Camera display error: {str(e)}")

    def update_camera(self):
        """Remove this method since we're using threading now"""
        pass


    def detect_aruco_markers(self, frame):
        """Detect ArUco markers in the frame and return centers"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.aruco_detector.detectMarkers(gray)

        markers = {}
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id in self.required_marker_ids:  # Only process required markers (0-8)
                    # Calculate center of the marker
                    marker_corners = corners[i][0]
                    center_x = np.mean(marker_corners[:, 0])
                    center_y = np.mean(marker_corners[:, 1])
                    markers[marker_id] = (center_x, center_y, marker_corners)

        return markers

    def collect_aruco_markers(self, frame):
        """Continuously collect ArUco markers across multiple frames"""
        current_markers = self.detect_aruco_markers(frame)

        # Add any new markers to our collection
        new_markers_found = []
        for marker_id, marker_data in current_markers.items():
            if marker_id not in self.collected_markers:
                self.collected_markers[marker_id] = marker_data
                new_markers_found.append(marker_id)

        # Log new markers found
        if new_markers_found:
            self.log_message(f"New ArUco markers collected: {new_markers_found}")

        # Update UI with collection progress
        collected_ids = sorted(list(self.collected_markers.keys()))
        missing_ids = sorted(list(self.required_marker_ids - set(collected_ids)))

        self.aruco_collection_label.setText(f"{len(collected_ids)}/9 found")
        self.collected_markers_label.setText(f"IDs: {collected_ids}")

        # Check if collection is complete
        if len(collected_ids) == len(self.required_marker_ids):
            if not self.markers_collection_complete:
                self.markers_collection_complete = True
                self.log_message("✅ All ArUco markers (0-8) collected successfully!")
                self.log_message(f"Collected markers: {collected_ids}")

                # Check if marker ID=4 is available
                if 4 in self.collected_markers:
                    self.center_marker_found = True
                    self.center_marker_label.setText("Found ✓")
                    self.center_marker_label.setStyleSheet("color: green;")
                    self.log_message("Center marker (ID=4) is available in collection!")
                else:
                    self.center_marker_found = False
                    self.center_marker_label.setText("Missing ID=4")
                    self.center_marker_label.setStyleSheet("color: red;")

                # Update collection status
                self.aruco_collection_label.setText("Complete ✅")
                self.aruco_collection_label.setStyleSheet("color: green;")
        else:
            # Show progress
            progress_text = f"Collecting... {len(collected_ids)}/9"
            if missing_ids:
                progress_text += f" (need: {missing_ids[:3]}{'...' if len(missing_ids) > 3 else ''})"
            self.aruco_collection_label.setText(progress_text)
            self.aruco_collection_label.setStyleSheet("color: orange;")

    def process_frame_for_display(self, frame):
        """Process frame with overlays and information"""
        display_frame = frame.copy()

        # Get frame dimensions
        height, width = display_frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        # Draw IMAGE CENTER with enhanced visibility
        cv2.line(display_frame, (center_x - 30, center_y), (center_x + 30, center_y), (0, 255, 255), 3)
        cv2.line(display_frame, (center_x, center_y - 30), (center_x, center_y + 30), (0, 255, 255), 3)
        cv2.circle(display_frame, (center_x, center_y), 8, (0, 255, 255), -1)
        cv2.circle(display_frame, (center_x, center_y), 12, (0, 255, 255), 3)
        cv2.putText(display_frame, "IMAGE CENTER", (center_x - 60, center_y - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Detect ArUco markers in the CLEAN original frame
        current_aruco_markers = self.detect_aruco_markers(frame)

        # Use collected markers if collection is complete, otherwise show current detection
        if self.markers_collection_complete:
            display_aruco_markers = self.collected_markers
        else:
            display_aruco_markers = current_aruco_markers

        # Use verification markers if available and aligned
        if self.aligned and self.verification_aruco_markers:
            display_aruco_markers = self.verification_aruco_markers

        # Draw all ArUco markers
        for marker_id, (marker_x, marker_y, marker_corners) in display_aruco_markers.items():
            # Draw marker outline
            cv2.polylines(display_frame, [marker_corners.astype(int)], True, (0, 255, 0), 2)

            # Draw marker center
            center_point = (int(marker_x), int(marker_y))

            if marker_id == 4:  # Special highlighting for center marker (ID=4)
                # Draw the CENTER MARKER with enhanced visibility
                cv2.circle(display_frame, center_point, 12, (0, 0, 255), -1)  # Red filled circle
                cv2.circle(display_frame, center_point, 18, (0, 0, 255), 3)  # Red ring
                cv2.circle(display_frame, center_point, 24, (255, 255, 255), 2)  # White outer ring

                # Add crosshair at center marker
                cv2.line(display_frame, (center_point[0] - 20, center_point[1]),
                         (center_point[0] + 20, center_point[1]), (0, 0, 255), 3)
                cv2.line(display_frame, (center_point[0], center_point[1] - 20),
                         (center_point[0], center_point[1] + 20), (0, 0, 255), 3)

                cv2.putText(display_frame, "ARUCO CENTER (ID=4)", (center_point[0] - 80, center_point[1] - 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                # Draw connection line and arrow to ArUco center
                line_color = (0, 255, 0) if self.aligned and self.verification_center_found else (255, 0, 255)
                line_thickness = 3
                cv2.line(display_frame, (center_x, center_y), center_point, line_color, line_thickness)
                self.draw_arrow(display_frame, (center_x, center_y), center_point, line_color, line_thickness)

                # Calculate and display distance information
                distance_pixels = np.sqrt((center_point[0] - center_x) ** 2 + (center_point[1] - center_y) ** 2)
                if self.ppm is not None:
                    distance_mm = distance_pixels / self.ppm
                    mid_x = (center_x + center_point[0]) // 2
                    mid_y = (center_y + center_point[1]) // 2
                    cv2.putText(display_frame, f"{distance_mm:.1f}mm", (mid_x + 10, mid_y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"{distance_pixels:.1f}px", (mid_x + 10, mid_y + 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            else:
                # Draw other markers in green
                cv2.circle(display_frame, center_point, 8, (0, 255, 0), -1)  # Green filled circle
                cv2.circle(display_frame, center_point, 12, (0, 255, 0), 2)  # Green ring

            # Draw marker ID
            cv2.putText(display_frame, str(marker_id), (center_point[0] - 10, center_point[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Draw collection progress info
        if not self.markers_collection_complete:
            collected_count = len(self.collected_markers)
            progress_text = f"Collecting ArUco: {collected_count}/9"
            cv2.putText(display_frame, progress_text, (10, height - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Draw chessboard corners if found (for PPM calculation reference only)
        current_corners = self.verification_corners if self.verification_found else self.stored_corners
        current_found = self.verification_found if self.aligned else self.corners_found

        if current_found and current_corners is not None:
            # Draw chessboard corners in light gray (since they're only for PPM reference)
            cv2.drawChessboardCorners(display_frame, self.chessboard_size, current_corners, True)

            # Draw a small indicator that chessboard is for PPM only
            cv2.putText(display_frame, "CHESSBOARD (PPM ONLY)", (10, height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Update verification status after robot movement
        if self.aligned:
            if current_aruco_markers and 4 in current_aruco_markers:
                self.verification_aruco_markers = current_aruco_markers
                self.verification_center_found = True
            else:
                self.verification_center_found = False

        # Status text
        status_text = "Searching for patterns..."

        if not self.markers_collection_complete:
            collected_count = len(self.collected_markers)
            status_text = f"Collecting ArUco markers: {collected_count}/9 found"
        elif 4 in self.collected_markers:
            center_marker_found = True
            if self.aligned:
                if self.verification_center_found:
                    if self.ppm is not None:
                        marker_4_pos = display_aruco_markers[4]
                        marker_center_x, marker_center_y = int(marker_4_pos[0]), int(marker_4_pos[1])
                        distance_pixels = np.sqrt((marker_center_x - center_x) ** 2 + (marker_center_y - center_y) ** 2)
                        distance_mm = distance_pixels / self.ppm
                        if distance_mm <= self.ALIGNMENT_THRESHOLD_MM:
                            status_text = f"WELL ALIGNED! Distance: {distance_mm:.1f}mm"
                            cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                        (0, 255, 0), 2)
                        else:
                            status_text = f"NEEDS ADJUSTMENT: {distance_mm:.1f}mm"
                            cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                        (0, 165, 255), 2)
                    else:
                        status_text = "Robot moved - verifying alignment"
                else:
                    status_text = "Robot aligned - looking for ArUco verification"
            else:
                status_text = "All markers collected - ready to align"
        else:
            status_text = "All markers collected but missing ID=4"

        if not (
                self.markers_collection_complete and 4 in self.collected_markers and self.aligned and self.verification_center_found and self.ppm is not None):
            cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return display_frame

    def draw_arrow(self, img, start_point, end_point, color, thickness):
        """Draw an arrow from start_point to end_point"""
        arrow_length = 20
        arrow_angle = np.pi / 6  # 30 degrees

        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        length = np.sqrt(dx * dx + dy * dy)

        if length > 0:
            ux = dx / length
            uy = dy / length

            tip_x1 = end_point[0] - arrow_length * (ux * np.cos(arrow_angle) - uy * np.sin(arrow_angle))
            tip_y1 = end_point[1] - arrow_length * (uy * np.cos(arrow_angle) + ux * np.sin(arrow_angle))

            tip_x2 = end_point[0] - arrow_length * (ux * np.cos(-arrow_angle) - uy * np.sin(-arrow_angle))
            tip_y2 = end_point[1] - arrow_length * (uy * np.cos(-arrow_angle) + ux * np.sin(-arrow_angle))

            cv2.line(img, end_point, (int(tip_x1), int(tip_y1)), color, thickness)
            cv2.line(img, end_point, (int(tip_x2), int(tip_y2)), color, thickness)

    def display_frame(self, frame):
        """Convert OpenCV frame to Qt format and display"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Scale image to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.camera_label.setPixmap(scaled_pixmap)

    def find_patterns(self):
        """Find chessboard and verify ArUco collection is complete"""
        if self.current_frame is None:
            self.log_message("No camera frame available")
            return

        # Check if ArUco collection is complete
        if not self.markers_collection_complete:
            self.log_message("ArUco marker collection not complete yet. Please wait...")
            self.status_label.setText("Collecting ArUco Markers - Please Wait")
            self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold; padding: 5px;")
            return

        self.log_message("ArUco collection complete. Searching for chessboard...")

        # Use the CLEAN original frame for chessboard detection
        clean_frame = self.current_frame.copy()

        # Find chessboard for PPM calculation ONLY
        gray = cv2.cvtColor(clean_frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            self.stored_corners = corners_refined.copy()
            self.corners_found = True
            self.log_message(f"Chessboard found! {len(corners)} corners detected (for PPM calculation)")
            self.corners_label.setText(f"{len(corners)} corners")
        else:
            self.log_message("No chessboard detected - PPM calculation may not be accurate")
            self.corners_label.setText("Not found")

        # Use the collected ArUco markers
        self.aruco_markers = self.collected_markers

        collected_ids = list(self.aruco_markers.keys())
        self.log_message(f"Using collected ArUco markers: {sorted(collected_ids)}")

        # Update UI based on what was found
        if self.corners_found and self.center_marker_found:
            self.status_label.setText("Patterns Ready - Ready to Compute Offsets")
            self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold; padding: 5px;")
            self.compute_button.setEnabled(True)
            self.find_button.setText("🎯 Patterns Ready ✓")
            self.find_button.setEnabled(False)
        elif self.center_marker_found:
            self.status_label.setText("ArUco Complete - Need Chessboard for PPM")
            self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold; padding: 5px;")
        elif self.corners_found:
            self.status_label.setText("Chessboard Found - ArUco Missing ID=4")
            self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold; padding: 5px;")
        else:
            self.status_label.setText("Need Both Patterns")
            self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold; padding: 5px;")

    def compute_offsets(self):
        """Compute PPM from chessboard and offsets from ArUco marker ID=4"""
        if not self.corners_found or self.stored_corners is None:
            self.log_message("No chessboard corners available for PPM computation")
            return

        if not self.center_marker_found or 4 not in self.aruco_markers:
            self.log_message("No center marker (ID=4) available for offset computation")
            return

        # Calculate pixels per millimeter (PPM) from chessboard
        horizontal_distances = []
        for i in range(self.chessboard_size[1]):  # rows
            for j in range(self.chessboard_size[0] - 1):  # columns - 1
                corner1_idx = i * self.chessboard_size[0] + j
                corner2_idx = i * self.chessboard_size[0] + (j + 1)
                if corner1_idx < len(self.stored_corners) and corner2_idx < len(self.stored_corners):
                    dist = np.linalg.norm(self.stored_corners[corner1_idx] - self.stored_corners[corner2_idx])
                    horizontal_distances.append(dist)

        if not horizontal_distances:
            self.log_message("Could not calculate square distances")
            return

        avg_square_size_pixels = np.mean(horizontal_distances)
        square_size_mm = 25.0  # Each square is 25mm

        # Get current robot height for PPM adjustment
        current_robot_pos = self.robot.getCurrentPosition()
        current_height = current_robot_pos[2]  # Z coordinate
        target_height = TARGET_WORKING_HEIGHT_MM  # Target working height

        # Calculate PPM at current height
        ppm_current = avg_square_size_pixels / square_size_mm

        # Adjust PPM for target height
        self.ppm = ppm_current * (current_height / target_height)

        self.log_message(f"Current height: {current_height:.1f}mm, Target height: {target_height:.1f}mm")
        self.log_message(f"PPM at current height: {ppm_current:.2f}, PPM adjusted for target: {self.ppm:.2f}")

        # Calculate centers and offsets using ArUco marker ID=4 as the center
        height, width = self.current_frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        # Use ArUco marker ID=4 as the target center
        aruco_center_x, aruco_center_y = self.aruco_markers[4][0], self.aruco_markers[4][1]

        # Calculate offsets in pixels and mm
        offset_x_pixels = aruco_center_x - center_x
        offset_y_pixels = aruco_center_y - center_y

        self.offset_x_mm = offset_x_pixels / self.ppm
        self.offset_y_mm = offset_y_pixels / self.ppm

        distance_pixels = np.sqrt(offset_x_pixels ** 2 + offset_y_pixels ** 2)
        distance_mm = distance_pixels / self.ppm

        # Update UI
        self.ppm_label.setText(f"{self.ppm:.2f} px/mm")
        self.x_offset_label.setText(f"{self.offset_x_mm:.2f} mm")
        self.y_offset_label.setText(f"{self.offset_y_mm:.2f} mm")
        self.distance_label.setText(f"{distance_mm:.2f} mm")

        self.log_message(f"ArUco center offsets computed - X: {self.offset_x_mm:.2f}mm, Y: {self.offset_y_mm:.2f}mm")
        self.log_message(f"PPM: {self.ppm:.2f} pixels/mm (from chessboard)")
        self.log_message(f"Center: ArUco marker ID=4 at ({aruco_center_x:.1f}, {aruco_center_y:.1f})")

        self.status_label.setText("ArUco Center Offsets Computed - Ready to Align Robot")
        self.status_label.setStyleSheet("color: blue; font-size: 14px; font-weight: bold; padding: 5px;")

        # Enable alignment button
        self.align_button.setEnabled(True)
        self.compute_button.setText("📐 ArUco Offsets Computed ✓")
        self.compute_button.setEnabled(False)

    def align_robot(self):
        """Iteratively move robot to align with ArUco marker ID=4 center until < 1mm accuracy"""
        if self.ppm is None:
            self.log_message("No offset calculations available")
            return

        try:
            self.log_message("Starting iterative robot alignment...")

            iteration = 0
            max_iterations = 2  # Safety limit
            target_accuracy_mm = 1.0  # Target accuracy in mm

            while iteration < max_iterations:
                iteration += 1
                self.log_message(f"--- Alignment Iteration {iteration} ---")

                # Get current robot position
                robotPos = self.robot.getCurrentPosition()
                self.log_message(f"Current robot position: {robotPos}")

                # Wait for camera to stabilize after movement
                if iteration > 1:
                    import time
                    time.sleep(1.0)  # Increased wait time for stability

                # Process Qt events to ensure fresh frame
                QApplication.processEvents()

                # Get fresh frame
                if self.current_frame is None:
                    self.log_message("No camera frame available")
                    break

                clean_frame = self.current_frame.copy()
                current_markers = self.detect_aruco_markers(clean_frame)

                if 4 not in current_markers:
                    self.log_message(f"Iteration {iteration}: ArUco marker ID=4 not found!")
                    break

                # Get current frame dimensions (recalculate each time for accuracy)
                current_height, current_width = clean_frame.shape[:2]
                current_center_x, current_center_y = current_width // 2, current_height // 2

                # Get current position of marker ID=4
                aruco_center_x, aruco_center_y = current_markers[4][0], current_markers[4][1]

                # Calculate current offsets in pixels
                offset_x_pixels = aruco_center_x - current_center_x
                offset_y_pixels = aruco_center_y - current_center_y

                # CRITICAL FIX: Always use the ORIGINAL PPM for movement calculations
                # The original PPM was calculated at the target working height and should remain constant
                # for all movement calculations to maintain consistent scaling
                current_ppm = self.ppm  # Use original PPM, not recalculated

                self.log_message(
                    f"Iteration {iteration}: Using original PPM: {current_ppm:.3f} (calculated at target height)")

                # Convert to millimeters using ORIGINAL PPM
                # COORDINATE SYSTEM FIX: Determine correct Y direction
                offset_x_mm = offset_x_pixels / current_ppm
                offset_y_mm = offset_y_pixels / current_ppm  # Try without negation first

                distance_pixels = np.sqrt(offset_x_pixels ** 2 + offset_y_pixels ** 2)
                distance_mm = distance_pixels / current_ppm

                self.log_message(f"Iteration {iteration}: Frame size: {current_width}x{current_height}")
                self.log_message(f"Iteration {iteration}: Image center: ({current_center_x}, {current_center_y})")
                self.log_message(f"Iteration {iteration}: ArUco center: ({aruco_center_x:.1f}, {aruco_center_y:.1f})")
                self.log_message(
                    f"Iteration {iteration}: Offset pixels: X={offset_x_pixels:.1f}, Y={offset_y_pixels:.1f}")
                self.log_message(f"Iteration {iteration}: PPM: {current_ppm:.3f}")
                self.log_message(f"Iteration {iteration}: Offset mm: X={offset_x_mm:.2f}, Y={offset_y_mm:.2f}")
                self.log_message(f"Iteration {iteration}: Distance: {distance_mm:.2f}mm")

                # Update UI with current iteration values
                self.x_offset_label.setText(f"{offset_x_mm:.2f} mm")
                self.y_offset_label.setText(f"{offset_y_mm:.2f} mm")
                self.distance_label.setText(f"{distance_mm:.2f} mm")

                # Process Qt events to keep UI responsive
                QApplication.processEvents()

                # Check if we've reached target accuracy
                if distance_mm <= target_accuracy_mm:
                    self.log_message(f"🎯 TARGET ACHIEVED! Final distance: {distance_mm:.2f}mm")
                    self.log_message(f"✅ Alignment completed in {iteration} iterations")

                    # Final success state
                    self.aligned = True
                    self.status_label.setText(f"PERFECTLY ALIGNED! ({distance_mm:.2f}mm)")
                    self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold; padding: 5px;")
                    self.alignment_status_label.setText(f"Aligned ({distance_mm:.2f}mm)")
                    self.align_button.setText("🎯 Perfect Alignment ✓")
                    self.align_button.setEnabled(False)

                    # Store final verification data
                    self.verification_aruco_markers = current_markers
                    self.verification_center_found = True
                    return

                # MOVEMENT CALCULATION FIX
                # Use a damping factor to prevent oscillation
                damping_factor = 0.8  # Reduce movement by 20% to prevent overshoot

                # Calculate movement with damping
                move_x_mm = offset_x_mm * damping_factor
                move_y_mm = offset_y_mm * damping_factor

                # COORDINATE SYSTEM: You might need to adjust these signs based on your robot's coordinate system
                # Try different combinations if this doesn't work:
                # Option 1: No change
                new_x = robotPos[0] + move_x_mm
                new_y = robotPos[1] + move_y_mm

                # Option 2: If X movement is inverted
                # new_x = robotPos[0] - move_x_mm
                # new_y = robotPos[1] + move_y_mm

                # Option 3: If Y movement is inverted
                # new_x = robotPos[0] + move_x_mm
                # new_y = robotPos[1] - move_y_mm

                # Option 4: If both are inverted
                # new_x = robotPos[0] - move_x_mm
                # new_y = robotPos[1] - move_y_mm

                new_z = robotPos[2]  # Keep current height instead of target height
                new_rx = robotPos[3]
                new_ry = robotPos[4]
                new_rz = robotPos[5]
                newPos = [new_x, new_y, new_z, new_rx, new_ry, new_rz]

                self.log_message(
                    f"Iteration {iteration}: Planned movement: X={move_x_mm:.2f}mm, Y={move_y_mm:.2f}mm (damped)")
                self.log_message(f"Iteration {iteration}: New position: {newPos}")

                # Update status for this iteration
                self.status_label.setText(f"Iteration {iteration}: Moving {distance_mm:.2f}mm...")
                self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold; padding: 5px;")
                self.alignment_status_label.setText(f"Iter {iteration}: {distance_mm:.2f}mm")

                # Process Qt events before robot movement
                QApplication.processEvents()

                # Move robot with slower velocity for precision
                ret = self.robotService.moveToPosition(newPos, tool=ROBOT_TOOL, workpiece=ROBOT_USER,
                                                       velocity=5, acceleration=50, waitToReachPosition=True)

                if ret != 0:
                    self.log_message(f"Iteration {iteration}: Robot movement failed! Return code: {ret}")
                    self.status_label.setText("Robot Movement Failed!")
                    self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold; padding: 5px;")
                    return

                # Store current offsets for next iteration
                self.offset_x_mm = offset_x_mm
                self.offset_y_mm = offset_y_mm

            # If we reach here, max iterations exceeded
            self.log_message(f"⚠️ Maximum iterations ({max_iterations}) reached")
            self.log_message(f"Final distance: {distance_mm:.2f}mm")

            if distance_mm <= 5.0:  # Accept if reasonably close
                self.aligned = True
                self.status_label.setText(f"Alignment Acceptable ({distance_mm:.2f}mm)")
                self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold; padding: 5px;")
                self.verification_aruco_markers = current_markers
                self.verification_center_found = True
            else:
                self.status_label.setText(f"Alignment Failed ({distance_mm:.2f}mm)")
                self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold; padding: 5px;")

        except Exception as e:
            self.log_message(f"Robot alignment error: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
            self.status_label.setText("Alignment Error!")
            self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold; padding: 5px;")

    def closeEvent(self, event):
        """Clean shutdown when application closes"""
        self.log_message("Shutting down camera thread...")
        self.camera_thread.stop()
        event.accept()

    def reset_all(self):
        """Reset all detection variables and UI state"""
        self.stored_corners = None
        self.corners_found = False
        self.aruco_markers = {}
        self.center_marker_found = False
        self.aligned = False
        self.verification_corners = None
        self.verification_found = False
        self.verification_aruco_markers = {}
        self.verification_center_found = False
        self.ppm = None
        self.offset_x_mm = 0.0
        self.offset_y_mm = 0.0

        # Reset ArUco collection
        self.collected_markers = {}
        self.markers_collection_complete = False

        # Reset UI


        self.find_button.setText("🎯 Find Chessboard & ArUco")
        self.find_button.setEnabled(True)
        self.compute_button.setText("📐 Compute X/Y Offsets")
        self.compute_button.setEnabled(False)
        self.align_button.setText("🤖 Align Robot")
        self.align_button.setEnabled(False)

        self.corners_label.setText("N/A")
        self.aruco_collection_label.setText("N/A")
        self.aruco_collection_label.setStyleSheet("color: blue;")
        self.collected_markers_label.setText("N/A")
        self.center_marker_label.setText("N/A")
        self.center_marker_label.setStyleSheet("color: blue;")
        self.ppm_label.setText("N/A")
        self.x_offset_label.setText("N/A")
        self.y_offset_label.setText("N/A")
        self.distance_label.setText("N/A")
        self.alignment_status_label.setText("N/A")

        self.status_label.setText("System Reset - Ready to Start")
        self.status_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; padding: 5px;")

        self.log_message("System reset completed. Ready for new alignment.")


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            border: 2px solid #8f8f91;
            border-radius: 6px;
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #f6f7fa, stop: 1 #dadbde);
            min-height: 20px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #e7e8eb, stop: 1 #cbccce);
        }
        QPushButton:pressed {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #dadbde, stop: 1 #f6f7fa);
        }
        QPushButton:disabled {
            background-color: #e0e0e0;
            color: #888888;
        }
    """)

    window = ChessboardAlignmentGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()