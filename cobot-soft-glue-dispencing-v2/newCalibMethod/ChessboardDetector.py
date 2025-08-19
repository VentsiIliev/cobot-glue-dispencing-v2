class ChessboardDetector:
    """Handles chessboard detection and corner management"""

    def __init__(self, chessboard_size):
        self.chessboard_size = chessboard_size  # (width, height) in squares
        self.stored_corners = None
        self.corners_found = False

    def detect_chessboard(self, frame):
        """Detect chessboard in frame and return success status and corners"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            return True, corners_refined

        return False, None

    def store_corners(self, corners):
        """Store detected corners"""
        self.stored_corners = corners.copy()
        self.corners_found = True

    def get_stored_corners(self):
        """Get stored corners"""
        return self.stored_corners

    def has_corners(self):
        """Check if corners are stored"""
        return self.corners_found and self.stored_corners is not None

    def get_corner_count(self):
        """Get number of stored corners"""
        if self.has_corners():
            return len(self.stored_corners)
        return 0

    def reset(self):
        """Reset stored corners"""
        self.stored_corners = None
        self.corners_found = False

    def draw_corners(self, frame):
        """Draw stored chessboard corners on frame"""
        if self.has_corners():
            cv2.drawChessboardCorners(frame, self.chessboard_size,
                                      self.stored_corners, True)


class PPMCalculator:
    """Handles Pixels Per Millimeter calculations"""

    def __init__(self, square_size_mm=25.0):
        self.square_size_mm = square_size_mm  # Physical size of chessboard squares
        self.ppm = None
        self.calculation_method = None

    def calculate_ppm(self):
        """Calculate PPM using stored patterns"""
        try:
            self.log_message("Starting PPM calculation...")

            # Try chessboard method first if available
            if self.chessboard_detector.has_corners():
                corners = self.chessboard_detector.get_stored_corners()
                ppm = self.ppm_calculator.calculate_ppm_from_chessboard(
                    corners, self.chessboard_detector.chessboard_size
                )

                if ppm is not None:
                    self.log_message(f"✅ PPM calculated from chessboard: {ppm:.2f} px/mm")
                    self.update_ppm_ui()
                    return

            # Try ArUco distance method if we have stored markers
            aruco_status = self.aruco_detector.get_collection_status()
            if aruco_status['stored_count'] >= 2:
                # Define known distances between markers (you need to measure these!)
                known_distances = self.get_known_marker_distances()
                stored_markers = self.aruco_detector.get_stored_markers()

                ppm, measurements = self.ppm_calculator.calculate_ppm_from_aruco_distances(
                    stored_markers, known_distances
                )

                if ppm is not None:
                    self.log_message(f"✅ PPM calculated from ArUco distances: {ppm:.2f} px/mm")
                    self.log_message(f"Individual measurements: {[f'{m:.2f}' for m in measurements]}")
                    self.update_ppm_ui()
                    return

            # Fallback: try marker size method
            if aruco_status['stored_count'] > 0:
                marker_size_mm = 20.0  # Adjust this to your actual marker size
                stored_markers = self.aruco_detector.get_stored_markers()

                ppm, measurements = self.ppm_calculator.calculate_ppm_from_marker_size(
                    stored_markers, marker_size_mm
                )

                if ppm is not None:
                    self.log_message(f"✅ PPM calculated from marker size: {ppm:.2f} px/mm")
                    self.log_message(f"Individual measurements: {[f'{m:.2f}' for m in measurements]}")
                    self.update_ppm_ui()
                    return

            self.log_message("❌ PPM calculation failed - insufficient data")

        except Exception as e:
            self.log_message(f"PPM calculation error: {str(e)}")

    def get_known_marker_distances(self):
        """Define known physical distances between ArUco markers"""
        # YOU NEED TO MEASURE THESE DISTANCES IN YOUR ACTUAL SETUP!
        # Example distances - REPLACE WITH YOUR ACTUAL MEASUREMENTS
        return {
            (0, 1): 50.0,  # Distance between marker 0 and 1 in mm
            (1, 2): 50.0,  # Distance between marker 1 and 2 in mm
            (0, 2): 70.71,  # Distance between marker 0 and 2 (diagonal) in mm
            (3, 4): 50.0,  # Distance between marker 3 and 4 in mm
            (4, 5): 50.0,  # Distance between marker 4 and 5 in mm
            (6, 7): 50.0,  # Distance between marker 6 and 7 in mm
            (7, 8): 50.0,  # Distance between marker 7 and 8 in mm
            (0, 4): 100.0,  # Distance between marker 0 and center (4) in mm
            (2, 4): 100.0,  # Distance between marker 2 and center (4) in mm
            (4, 6): 100.0,  # Distance between marker 4 and 6 in mm
            (4, 8): 100.0,  # Distance between marker 4 and 8 in mm
        }

    def update_ppm_ui(self):
        """Update PPM information in UI"""
        ppm_info = self.ppm_calculator.get_calculation_info()

        if ppm_info['ppm'] is not None:
            self.ppm_value_label.setText(f"{ppm_info['ppm']:.2f} px/mm")
            self.ppm_method_label.setText(ppm_info['method'])

            self.calculate_ppm_button.setText("📏 PPM Calculated ✓")
            self.calculate_ppm_button.setStyleSheet(
                "font-size: 11px; font-weight: bold; background-color: #ccffcc;")
            self.calculate_ppm_button.setEnabled(False)

            self.status_label.setText("PPM calculated - System ready")
            self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")

    def reset_all(self):
        """Reset all detection data and UI"""
        self.aruco_detector.reset()
        self.chessboard_detector.reset()
        self.ppm_calculator.reset()

        # Reset UI labels
        self.chessboard_status_label.setText("N/A")
        self.chessboard_status_label.setStyleSheet("color: blue;")
        self.aruco_count_label.setText("N/A")
        self.collection_status_label.setText("N/A")
        self.collection_status_label.setStyleSheet("color: blue;")
        self.center_marker_label.setText("N/A")
        self.center_marker_label.setStyleSheet("color: blue;")

        self.ppm_value_label.setText("N/A")
        self.ppm_method_label.setText("N/A")

        # Reset buttons
        self.find_patterns_button.setText("🎯 Find & Store Patterns")
        self.find_patterns_button.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.find_patterns_button.setEnabled(True)

        self.calculate_ppm_button.setText("📏 Calculate PPM")
        self.calculate_ppm_button.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.calculate_ppm_button.setEnabled(False)

        self.status_label.setText("System reset - Ready to start")
        self.status_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold;")

        self.log_message("All systems reset - ready for new detection")

    def get_detection_data(self):
        """Get all detection data for external use"""
        return {
            'chessboard': {
                'corners': self.chessboard_detector.get_stored_corners(),
                'found': self.chessboard_detector.has_corners(),
                'size': self.chessboard_detector.chessboard_size,
                'corner_count': self.chessboard_detector.get_corner_count()
            },
            'aruco': {
                'markers': self.aruco_detector.get_stored_markers(),
                'status': self.aruco_detector.get_collection_status(),
                'center_marker': self.aruco_detector.get_marker(4)
            },
            'ppm': {
                'value': self.ppm_calculator.get_ppm(),
                'info': self.ppm_calculator.get_calculation_info()
            }
        }

    def closeEvent(self, event):
        """Clean shutdown when application closes"""
        self.log_message("Shutting down camera thread...")
        self.camera_thread.stop()
        event.accept()