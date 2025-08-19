import sys
import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QGridLayout,
                             QGroupBox, QTextEdit, QSplitter)

from GlueDispensingApplication.robot.RobotConfig import *
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
from GlueDispensingApplication.settings.SettingsService import SettingsService
from VisionSystem.VisionSystem import VisionSystem


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
                self.msleep(33)
            except Exception as e:
                print(f"Camera thread error: {e}")
                self.msleep(100)

    def stop(self):
        """Stop the camera thread"""
        self.running = False
        self.wait()


class SimpleAlignmentGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Pattern Detection System")
        self.setGeometry(100, 100, 1000, 700)

        # Initialize systems
        self.system = VisionSystem()
        self.camera_thread = CameraThread(self.system)
        self.camera_thread.frame_ready.connect(self.on_new_frame)
        self.settingsService = SettingsService()
        self.robot = RobotWrapper(ROBOT_IP)
        self.robotService = RobotService(self.robot, self.settingsService, None)

        # Chessboard settings
        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.system.camera_settings.set_draw_contours(False)

        # ArUco detector setup
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        # Required ArUco marker IDs (0-8)
        self.required_marker_ids = set(range(9))

        # Detection storage
        self.current_frame = None
        self.stored_chessboard_corners = None
        self.stored_aruco_markers = {}
        self.chessboard_found = False
        self.aruco_collection_complete = False

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
        self.setup_camera_display(main_splitter)

        # Right side - Controls and info
        self.setup_control_panel(main_splitter)

        # Set splitter proportions
        main_splitter.setSizes([700, 300])

    def setup_camera_display(self, parent_splitter):
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

        parent_splitter.addWidget(camera_widget)

    def setup_control_panel(self, parent_splitter):
        control_widget = QWidget()
        control_widget.setMaximumWidth(300)
        control_layout = QVBoxLayout(control_widget)

        # Control buttons
        self.setup_control_buttons(control_layout)

        # Detection info
        self.setup_detection_info(control_layout)

        # Log display
        self.setup_log_display(control_layout)

        parent_splitter.addWidget(control_widget)

    def setup_control_buttons(self, parent_layout):
        button_group = QGroupBox("Controls")
        button_layout = QVBoxLayout(button_group)

        # Move to calibration position button
        self.move_to_calibration_button = QPushButton("🔄 Move to Calibration Position")
        self.move_to_calibration_button.setMinimumHeight(40)
        self.move_to_calibration_button.clicked.connect(self.move_to_calibration_position)
        self.move_to_calibration_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        button_layout.addWidget(self.move_to_calibration_button)

        # Find and store patterns button
        self.find_patterns_button = QPushButton("🎯 Find & Store Patterns")
        self.find_patterns_button.setMinimumHeight(40)
        self.find_patterns_button.clicked.connect(self.find_and_store_patterns)
        self.find_patterns_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        button_layout.addWidget(self.find_patterns_button)

        # Reset button
        self.reset_button = QPushButton("🔄 Reset Detection")
        self.reset_button.setMinimumHeight(30)
        self.reset_button.clicked.connect(self.reset_detection)
        self.reset_button.setStyleSheet("font-size: 11px;")
        button_layout.addWidget(self.reset_button)

        parent_layout.addWidget(button_group)

    def setup_detection_info(self, parent_layout):
        info_group = QGroupBox("Detection Status")
        info_layout = QGridLayout(info_group)

        # Detection status labels
        labels = [
            ("Chessboard Size:", "chessboard_size_label"),
            ("Chessboard Found:", "chessboard_status_label"),
            ("ArUco Markers:", "aruco_count_label"),
            ("Collection Status:", "collection_status_label"),
            ("Center Marker (ID=4):", "center_marker_label")
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
        self.log_message(f"System initialized. Chessboard: {self.chessboard_size}, ArUco markers: 0-8")

    def log_message(self, message):
        """Add message to log display"""
        self.log_text.append(f"[INFO] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def on_new_frame(self, frame):
        """Handle new frame from camera thread"""
        try:
            self.current_frame = frame.copy()
            # Process frame for display with overlays
            display_frame = self.process_frame_for_display(frame)
            self.display_frame(display_frame)
        except Exception as e:
            self.log_message(f"Camera display error: {str(e)}")

    def process_frame_for_display(self, frame):
        """Process frame with detection overlays"""
        display_frame = frame.copy()
        height, width = display_frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        # Draw image center crosshair
        cv2.line(display_frame, (center_x - 30, center_y), (center_x + 30, center_y), (0, 255, 255), 3)
        cv2.line(display_frame, (center_x, center_y - 30), (center_x, center_y + 30), (0, 255, 255), 3)
        cv2.circle(display_frame, (center_x, center_y), 8, (0, 255, 255), -1)

        # Detect and draw current ArUco markers
        current_aruco = self.detect_aruco_markers(frame)
        for marker_id, (marker_x, marker_y, corners) in current_aruco.items():
            # Draw marker outline
            cv2.polylines(display_frame, [corners.astype(int)], True, (0, 255, 0), 2)

            # Draw marker center and ID
            center_point = (int(marker_x), int(marker_y))

            if marker_id == 4:  # Highlight center marker
                cv2.circle(display_frame, center_point, 12, (0, 0, 255), -1)
                cv2.circle(display_frame, center_point, 18, (0, 0, 255), 3)
                # Draw line to image center
                cv2.line(display_frame, (center_x, center_y), center_point, (255, 0, 255), 2)
            else:
                cv2.circle(display_frame, center_point, 8, (0, 255, 0), -1)

            # Draw marker ID
            cv2.putText(display_frame, str(marker_id),
                        (center_point[0] - 10, center_point[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Draw stored chessboard corners if available
        if self.chessboard_found and self.stored_chessboard_corners is not None:
            cv2.drawChessboardCorners(display_frame, self.chessboard_size,
                                      self.stored_chessboard_corners, True)

        # Status text
        status_text = "Ready for detection"
        if self.chessboard_found and self.aruco_collection_complete:
            status_text = "All patterns detected and stored!"
        elif self.chessboard_found:
            status_text = f"Chessboard stored, ArUco: {len(self.stored_aruco_markers)}/9"
        elif self.aruco_collection_complete:
            status_text = "ArUco complete, need chessboard"
        elif len(current_aruco) > 0:
            status_text = f"Detecting ArUco markers: {len(current_aruco)} visible"

        cv2.putText(display_frame, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return display_frame

    def detect_aruco_markers(self, frame):
        """Detect ArUco markers in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)

        markers = {}
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id in self.required_marker_ids:
                    marker_corners = corners[i][0]
                    center_x = np.mean(marker_corners[:, 0])
                    center_y = np.mean(marker_corners[:, 1])
                    markers[marker_id] = (center_x, center_y, marker_corners)

        return markers

    def detect_chessboard(self, frame):
        """Detect chessboard in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            return True, corners_refined

        return False, None

    def display_frame(self, frame):
        """Convert OpenCV frame to Qt format and display"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # Scale to fit label
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)

    def move_to_calibration_position(self):
        """Move robot to calibration position"""
        try:
            self.log_message("Moving robot to calibration position...")
            self.move_to_calibration_button.setEnabled(False)
            self.move_to_calibration_button.setText("🔄 Moving...")

            # Process events to update UI
            QApplication.processEvents()

            # Move robot
            result = self.robotService.moveToCalibrationPosition()

            if result == 0:
                self.log_message("✅ Robot moved to calibration position successfully")
                self.move_to_calibration_button.setText("🔄 At Calibration Position ✓")
                self.move_to_calibration_button.setStyleSheet(
                    "font-size: 12px; font-weight: bold; background-color: #ccffcc;")
                self.status_label.setText("Robot at calibration position - Ready to detect patterns")
                self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            else:
                self.log_message(f"❌ Failed to move robot to calibration position. Error code: {result}")
                self.move_to_calibration_button.setText("🔄 Movement Failed")
                self.move_to_calibration_button.setStyleSheet(
                    "font-size: 12px; font-weight: bold; background-color: #ffcccc;")
                self.move_to_calibration_button.setEnabled(True)

        except Exception as e:
            self.log_message(f"Error moving robot: {str(e)}")
            self.move_to_calibration_button.setText("🔄 Error Occurred")
            self.move_to_calibration_button.setEnabled(True)

    def find_and_store_patterns(self):
        """Find and store both chessboard and ArUco patterns"""
        if self.current_frame is None:
            self.log_message("No camera frame available")
            return

        self.log_message("Starting pattern detection...")
        clean_frame = self.current_frame.copy()

        # Detect chessboard
        chessboard_found, corners = self.detect_chessboard(clean_frame)
        if chessboard_found:
            self.stored_chessboard_corners = corners.copy()
            self.chessboard_found = True
            self.log_message(f"✅ Chessboard detected and stored! {len(corners)} corners found")
            self.chessboard_status_label.setText("Found & Stored ✓")
            self.chessboard_status_label.setStyleSheet("color: green;")
        else:
            self.log_message("❌ Chessboard not found")
            self.chessboard_status_label.setText("Not Found")
            self.chessboard_status_label.setStyleSheet("color: red;")

        # Detect ArUco markers
        aruco_markers = self.detect_aruco_markers(clean_frame)
        if aruco_markers:
            # Store detected markers
            self.stored_aruco_markers.update(aruco_markers)
            detected_ids = sorted(list(aruco_markers.keys()))
            stored_ids = sorted(list(self.stored_aruco_markers.keys()))

            self.log_message(f"✅ ArUco markers detected: {detected_ids}")
            self.log_message(f"Total stored markers: {stored_ids}")

            # Check if collection is complete
            if len(self.stored_aruco_markers) >= len(self.required_marker_ids):
                self.aruco_collection_complete = True
                self.collection_status_label.setText("Complete ✅")
                self.collection_status_label.setStyleSheet("color: green;")
                self.log_message("✅ ArUco marker collection complete!")
            else:
                missing = self.required_marker_ids - set(self.stored_aruco_markers.keys())
                self.collection_status_label.setText(f"Need: {sorted(list(missing))}")
                self.collection_status_label.setStyleSheet("color: orange;")

            # Update UI
            self.aruco_count_label.setText(f"{len(self.stored_aruco_markers)}/9")

            # Check for center marker
            if 4 in self.stored_aruco_markers:
                self.center_marker_label.setText("Found ✓")
                self.center_marker_label.setStyleSheet("color: green;")
            else:
                self.center_marker_label.setText("Missing")
                self.center_marker_label.setStyleSheet("color: red;")
        else:
            self.log_message("❌ No ArUco markers detected")
            self.aruco_count_label.setText("None found")

        # Update overall status
        if self.chessboard_found and self.aruco_collection_complete:
            self.status_label.setText("All patterns detected and stored successfully!")
            self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            self.find_patterns_button.setText("🎯 All Patterns Stored ✓")
            self.find_patterns_button.setStyleSheet(
                "font-size: 12px; font-weight: bold; background-color: #ccffcc;")
            self.find_patterns_button.setEnabled(False)
        elif self.chessboard_found or len(self.stored_aruco_markers) > 0:
            self.status_label.setText("Partial detection - try again or adjust camera angle")
            self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold;")
        else:
            self.status_label.setText("No patterns detected - check lighting and positioning")
            self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")

    def reset_detection(self):
        """Reset all stored detection data"""
        self.stored_chessboard_corners = None
        self.stored_aruco_markers = {}
        self.chessboard_found = False
        self.aruco_collection_complete = False

        # Reset UI
        self.chessboard_status_label.setText("N/A")
        self.chessboard_status_label.setStyleSheet("color: blue;")
        self.aruco_count_label.setText("N/A")
        self.collection_status_label.setText("N/A")
        self.collection_status_label.setStyleSheet("color: blue;")
        self.center_marker_label.setText("N/A")
        self.center_marker_label.setStyleSheet("color: blue;")

        self.find_patterns_button.setText("🎯 Find & Store Patterns")
        self.find_patterns_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.find_patterns_button.setEnabled(True)

        self.status_label.setText("Detection reset - Ready to detect patterns")
        self.status_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold;")

        self.log_message("Detection data reset - ready for new detection")

    def get_stored_data(self):
        """Return stored detection data for external use"""
        return {
            'chessboard_corners': self.stored_chessboard_corners,
            'chessboard_found': self.chessboard_found,
            'aruco_markers': self.stored_aruco_markers.copy(),
            'aruco_complete': self.aruco_collection_complete,
            'chessboard_size': self.chessboard_size
        }

    def closeEvent(self, event):
        """Clean shutdown when application closes"""
        self.log_message("Shutting down camera thread...")
        self.camera_thread.stop()
        event.accept()


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

    window = SimpleAlignmentGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()