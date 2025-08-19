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


class ArUcoDetector:
    """Handles ArUco marker detection and management"""

    def __init__(self, required_marker_ids=None):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        self.required_marker_ids = required_marker_ids or set(range(9))  # Default: IDs 0-8
        self.stored_markers = {}
        self.collection_complete = False

    def detect_markers(self, frame):
        """Detect ArUco markers in frame and return their data"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)

        markers = {}
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id in self.required_marker_ids:
                    marker_corners = corners[i][0]
                    center_x = np.mean(marker_corners[:, 0])
                    center_y = np.mean(marker_corners[:, 1])
                    markers[marker_id] = {
                        'center': (center_x, center_y),
                        'corners': marker_corners,
                        'id': marker_id
                    }

        return markers

    def store_markers(self, detected_markers):
        """Store detected markers and return list of newly found markers"""
        new_markers = []
        for marker_id, marker_data in detected_markers.items():
            if marker_id not in self.stored_markers:
                self.stored_markers[marker_id] = marker_data
                new_markers.append(marker_id)

        # Update collection status
        self.collection_complete = len(self.stored_markers) >= len(self.required_marker_ids)

        return new_markers

    def get_stored_markers(self):
        """Return copy of stored markers"""
        return self.stored_markers.copy()

    def get_marker(self, marker_id):
        """Get specific marker by ID"""
        return self.stored_markers.get(marker_id, None)

    def has_marker(self, marker_id):
        """Check if specific marker is stored"""
        return marker_id in self.stored_markers

    def get_collection_status(self):
        """Get collection progress information"""
        stored_ids = set(self.stored_markers.keys())
        missing_ids = self.required_marker_ids - stored_ids

        return {
            'stored_count': len(stored_ids),
            'total_required': len(self.required_marker_ids),
            'stored_ids': sorted(list(stored_ids)),
            'missing_ids': sorted(list(missing_ids)),
            'complete': self.collection_complete,
            'center_marker_found': 4 in stored_ids
        }

    def reset(self):
        """Reset all stored markers"""
        self.stored_markers = {}
        self.collection_complete = False

    def draw_markers(self, frame, markers, highlight_center=True):
        """Draw markers on frame with optional center marker highlighting"""
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        for marker_id, marker_data in markers.items():
            corners = marker_data['corners']
            center = marker_data['center']
            center_point = (int(center[0]), int(center[1]))

            # Draw marker outline
            cv2.polylines(frame, [corners.astype(int)], True, (0, 255, 0), 2)

            # Draw marker center and ID
            if marker_id == 4 and highlight_center:
                # Special highlighting for center marker
                cv2.circle(frame, center_point, 12, (0, 0, 255), -1)
                cv2.circle(frame, center_point, 18, (0, 0, 255), 3)
                cv2.circle(frame, center_point, 24, (255, 255, 255), 2)

                # Add crosshair
                cv2.line(frame, (center_point[0] - 20, center_point[1]),
                         (center_point[0] + 20, center_point[1]), (0, 0, 255), 3)
                cv2.line(frame, (center_point[0], center_point[1] - 20),
                         (center_point[0], center_point[1] + 20), (0, 0, 255), 3)

                # Draw connection line to image center
                cv2.line(frame, (center_x, center_y), center_point, (255, 0, 255), 2)
            else:
                # Regular marker
                cv2.circle(frame, center_point, 8, (0, 255, 0), -1)
                cv2.circle(frame, center_point, 12, (0, 255, 0), 2)

            # Draw marker ID
            cv2.putText(frame, str(marker_id),
                        (center_point[0] - 10, center_point[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)