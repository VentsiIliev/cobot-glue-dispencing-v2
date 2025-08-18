import sys
from enum import Enum

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGroupBox, QGridLayout, QPushButton,
                             QTextEdit, QProgressBar)

from pl_gui.ToastWidget import ToastWidget
from pl_gui.customWidgets.SwitchButton import QToggle
from pl_gui.settings_view.BaseSettingsTabLayout import BaseSettingsTabLayout
from pl_gui.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox, FocusSpinBox
from PyQt6.QtWidgets import QScroller
from PyQt6.QtCore import Qt


class CalibrationServiceTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Calibration signals
    start_calibration_requested = QtCore.pyqtSignal()
    stop_calibration_requested = QtCore.pyqtSignal()
    save_calibration_requested = QtCore.pyqtSignal()
    load_calibration_requested = QtCore.pyqtSignal()
    reset_calibration_requested = QtCore.pyqtSignal()

    # ArUco detection signals
    test_aruco_detection_requested = QtCore.pyqtSignal()
    detect_workspace_markers_requested = QtCore.pyqtSignal()

    # Perspective transform signals
    compute_perspective_matrix_requested = QtCore.pyqtSignal()
    save_perspective_matrix_requested = QtCore.pyqtSignal()
    load_perspective_matrix_requested = QtCore.pyqtSignal()

    # Camera-to-robot transform signals
    compute_camera_robot_transform_requested = QtCore.pyqtSignal()
    save_camera_robot_transform_requested = QtCore.pyqtSignal()
    load_camera_robot_transform_requested = QtCore.pyqtSignal()

    # Debug and testing signals
    test_transformation_requested = QtCore.pyqtSignal()
    capture_calibration_image_requested = QtCore.pyqtSignal()
    show_debug_view_requested = QtCore.pyqtSignal(bool)

    def __init__(self, parent_widget=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.parent_widget = parent_widget
        self.debug_mode_active = False
        self.calibration_in_progress = False

        # Create main content with new layout
        self.create_main_content()

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

    def create_calibration_preview_section(self):
        """Create the calibration preview section with preview and controls"""
        preview_widget = QWidget()
        preview_widget.setFixedWidth(500)
        preview_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)

        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(15)

        # Status label
        self.calibration_status_label = QLabel("Calibration Status: Ready")
        self.calibration_status_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        preview_layout.addWidget(self.calibration_status_label)

        # Calibration preview area
        self.calibration_preview_label = QLabel("Calibration Preview")
        self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_preview_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: white;
                font-size: 16px;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.calibration_preview_label.setFixedSize(460, 259)
        self.calibration_preview_label.setScaledContents(False)
        preview_layout.addWidget(self.calibration_preview_label)

        # Progress bar for calibration
        self.calibration_progress = QProgressBar()
        self.calibration_progress.setVisible(False)
        self.calibration_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        preview_layout.addWidget(self.calibration_progress)

        # Control buttons grid
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Main calibration buttons
        self.start_calibration_button = QPushButton("Start Calibration")
        self.stop_calibration_button = QPushButton("Stop Calibration")
        self.stop_calibration_button.setEnabled(False)

        main_buttons = [self.start_calibration_button, self.stop_calibration_button]
        for i, btn in enumerate(main_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Save/Load calibration
        self.save_calibration_button = QPushButton("Save Calibration")
        self.load_calibration_button = QPushButton("Load Calibration")

        save_load_buttons = [self.save_calibration_button, self.load_calibration_button]
        for i, btn in enumerate(save_load_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 1, i)

        # Row 2: ArUco detection
        self.test_aruco_button = QPushButton("Test ArUco")
        self.detect_workspace_button = QPushButton("Detect Workspace")

        aruco_buttons = [self.test_aruco_button, self.detect_workspace_button]
        for i, btn in enumerate(aruco_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 2, i)

        # Row 3: Perspective transform
        self.compute_perspective_button = QPushButton("Compute Perspective")
        self.save_perspective_button = QPushButton("Save Perspective")

        perspective_buttons = [self.compute_perspective_button, self.save_perspective_button]
        for i, btn in enumerate(perspective_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 3, i)

        # Row 4: Camera-Robot transform
        self.compute_transform_button = QPushButton("Compute Transform")
        self.save_transform_button = QPushButton("Save Transform")

        transform_buttons = [self.compute_transform_button, self.save_transform_button]
        for i, btn in enumerate(transform_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 4, i)

        # Row 5: Debug and testing
        self.capture_image_button = QPushButton("Capture Image")
        self.test_transformation_button = QPushButton("Test Transform")

        debug_buttons = [self.capture_image_button, self.test_transformation_button]
        for i, btn in enumerate(debug_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 5, i)

        # Row 6: Debug mode toggle and reset
        self.debug_mode_button = QPushButton("Debug Mode")
        self.debug_mode_button.setCheckable(True)
        self.debug_mode_button.setChecked(self.debug_mode_active)

        self.reset_calibration_button = QPushButton("Reset All")

        utility_buttons = [self.debug_mode_button, self.reset_calibration_button]
        for i, btn in enumerate(utility_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 6, i)

        preview_layout.addLayout(button_grid)

        # Log output area
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(120)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        self.log_output.setPlaceholderText("Calibration logs will appear here...")
        preview_layout.addWidget(self.log_output)

        preview_layout.addStretch()

        self.connect_default_callbacks()
        return preview_widget

    def update_calibration_preview(self, pixmap):
        """Update the calibration preview with a new frame, maintaining aspect ratio"""
        if hasattr(self, 'calibration_preview_label'):
            label_size = self.calibration_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.calibration_preview_label.setPixmap(scaled_pixmap)
            self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_calibration_preview_from_cv2(self, cv2_image):
        """Update preview from OpenCV image"""
        if hasattr(self, 'calibration_preview_label'):
            rgb_image = cv2_image[:, :, ::-1] if len(cv2_image.shape) == 3 else cv2_image
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

            img_bytes = rgb_image.tobytes()

            if len(rgb_image.shape) == 3:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_calibration_preview(pixmap)

    def update_calibration_status(self, status, status_type="info"):
        """Update the calibration status label"""
        if hasattr(self, 'calibration_status_label'):
            color_map = {
                "success": "#4caf50",
                "error": "#d32f2f",
                "warning": "#ff9800",
                "info": "#2196f3",
                "ready": "#2e7d32"
            }
            color = color_map.get(status_type, "#2e7d32")
            self.calibration_status_label.setText(f"Calibration Status: {status}")
            self.calibration_status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def update_progress(self, value, visible=True):
        """Update calibration progress bar"""
        if hasattr(self, 'calibration_progress'):
            self.calibration_progress.setValue(value)
            self.calibration_progress.setVisible(visible)

    def add_log_message(self, message, message_type="info"):
        """Add message to log output"""
        if hasattr(self, 'log_output'):
            color_map = {
                "success": "#4caf50",
                "error": "#f44336",
                "warning": "#ff9800",
                "info": "#2196f3"
            }
            color = color_map.get(message_type, "#ffffff")
            formatted_message = f'<span style="color: {color};">[{message_type.upper()}] {message}</span>'
            self.log_output.append(formatted_message)
            # Auto-scroll to bottom
            scrollbar = self.log_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """Clear the log output"""
        if hasattr(self, 'log_output'):
            self.log_output.clear()

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        self.clear_layout()
        self.create_main_content()

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def create_main_content(self):
        """Create the main content with settings on left and preview on right"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # Create settings scroll area (left side)
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(20)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        self.add_settings_to_layout(settings_content_layout)
        settings_content_layout.addStretch()

        settings_scroll_area.setWidget(settings_content_widget)

        # Create calibration preview section (right side)
        preview_widget = self.create_calibration_preview_section()

        # Add both sections to main horizontal layout
        main_horizontal_layout.addWidget(preview_widget, 2)
        main_horizontal_layout.addWidget(settings_scroll_area, 1)

        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)
        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout in vertical arrangement"""
        # First row of settings
        first_row = QHBoxLayout()
        first_row.setSpacing(15)

        self.chessboard_group = self.create_chessboard_settings_group()
        self.aruco_group = self.create_aruco_settings_group()

        first_row.addWidget(self.chessboard_group)
        first_row.addWidget(self.aruco_group)

        parent_layout.addLayout(first_row)

        # Second row of settings
        second_row = QHBoxLayout()
        second_row.setSpacing(15)

        self.perspective_group = self.create_perspective_settings_group()
        self.transform_group = self.create_transform_settings_group()

        second_row.addWidget(self.perspective_group)
        second_row.addWidget(self.transform_group)

        parent_layout.addLayout(second_row)

        # Third row of settings
        third_row = QHBoxLayout()
        third_row.setSpacing(15)

        self.calibration_group = self.create_calibration_settings_group()
        self.debug_group = self.create_debug_settings_group()

        third_row.addWidget(self.calibration_group)
        third_row.addWidget(self.debug_group)

        parent_layout.addLayout(third_row)

    def create_chessboard_settings_group(self):
        """Create chessboard calibration settings group"""
        group = QGroupBox("Chessboard Settings")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Chessboard Width
        label = QLabel("Chessboard Width:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_width_input = self.create_spinbox(3, 20, 9, " corners")
        layout.addWidget(self.chessboard_width_input, row, 1)

        # Chessboard Height
        row += 1
        label = QLabel("Chessboard Height:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_height_input = self.create_spinbox(3, 20, 6, " corners")
        layout.addWidget(self.chessboard_height_input, row, 1)

        # Square Size
        row += 1
        label = QLabel("Square Size:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.square_size_input = self.create_double_spinbox(1.0, 100.0, 25.0, " mm")
        layout.addWidget(self.square_size_input, row, 1)

        # Skip Frames
        row += 1
        label = QLabel("Skip Frames:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.skip_frames_input = self.create_spinbox(0, 100, 5)
        layout.addWidget(self.skip_frames_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_aruco_settings_group(self):
        """Create ArUco detection settings group"""
        group = QGroupBox("ArUco Detection")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # ArUco Dictionary
        label = QLabel("Dictionary:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_dictionary_combo = QComboBox()
        self.aruco_dictionary_combo.setMinimumHeight(40)
        self.aruco_dictionary_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.aruco_dictionary_combo.addItems([
            "DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250", "DICT_4X4_1000",
            "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250", "DICT_5X5_1000",
            "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250", "DICT_6X6_1000"
        ])
        self.aruco_dictionary_combo.setCurrentText("DICT_4X4_250")
        layout.addWidget(self.aruco_dictionary_combo, row, 1)

        # Flip Image
        row += 1
        label = QLabel("Flip Image:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_flip_toggle = QToggle("Flip")
        self.aruco_flip_toggle.setCheckable(True)
        self.aruco_flip_toggle.setMinimumHeight(35)
        self.aruco_flip_toggle.setChecked(False)
        layout.addWidget(self.aruco_flip_toggle, row, 1)

        # Max Attempts
        row += 1
        label = QLabel("Max Attempts:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_attempts_input = self.create_spinbox(1, 100, 60)
        layout.addWidget(self.max_attempts_input, row, 1)

        # Required Marker IDs
        row += 1
        label = QLabel("Workspace IDs:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.marker_ids_label = QLabel("30, 31, 32, 33")
        self.marker_ids_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.marker_ids_label, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_perspective_settings_group(self):
        """Create perspective transform settings group"""
        group = QGroupBox("Perspective Transform")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Auto-compute on detection
        label = QLabel("Auto Compute:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.auto_compute_toggle = QToggle("Auto")
        self.auto_compute_toggle.setCheckable(True)
        self.auto_compute_toggle.setMinimumHeight(35)
        self.auto_compute_toggle.setChecked(True)
        layout.addWidget(self.auto_compute_toggle, row, 1)

        # Storage path
        row += 1
        label = QLabel("Storage Path:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.storage_path_label = QLabel("Default")
        self.storage_path_label.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")
        self.storage_path_label.setWordWrap(True)
        layout.addWidget(self.storage_path_label, row, 1)

        # Matrix status
        row += 1
        label = QLabel("Matrix Status:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.matrix_status_label = QLabel("Not Computed")
        self.matrix_status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self.matrix_status_label, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_transform_settings_group(self):
        """Create camera-to-robot transform settings group"""
        group = QGroupBox("Camera-Robot Transform")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Transform method
        label = QLabel("Method:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.transform_method_combo = QComboBox()
        self.transform_method_combo.setMinimumHeight(40)
        self.transform_method_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.transform_method_combo.addItems(["Homography", "Affine", "Rigid"])
        layout.addWidget(self.transform_method_combo, row, 1)

        # Point pairs required
        row += 1
        label = QLabel("Min Point Pairs:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.min_point_pairs_input = self.create_spinbox(4, 20, 4)
        layout.addWidget(self.min_point_pairs_input, row, 1)

        # Transform status
        row += 1
        label = QLabel("Transform Status:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.transform_status_label = QLabel("Not Computed")
        self.transform_status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self.transform_status_label, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_calibration_settings_group(self):
        """Create general calibration settings group"""
        group = QGroupBox("Calibration Settings")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Auto-save results
        label = QLabel("Auto Save:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.auto_save_toggle = QToggle("Auto")
        self.auto_save_toggle.setCheckable(True)
        self.auto_save_toggle.setMinimumHeight(35)
        self.auto_save_toggle.setChecked(True)
        layout.addWidget(self.auto_save_toggle, row, 1)

        # Validation threshold
        row += 1
        label = QLabel("Validation Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.validation_threshold_input = self.create_double_spinbox(0.1, 10.0, 2.0, " px")
        layout.addWidget(self.validation_threshold_input, row, 1)

        # Calibration attempts
        row += 1
        label = QLabel("Max Attempts:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.calibration_attempts_input = self.create_spinbox(1, 20, 5)
        layout.addWidget(self.calibration_attempts_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_debug_settings_group(self):
        """Create debug and testing settings group"""
        group = QGroupBox("Debug & Testing")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Show intermediate images
        label = QLabel("Show Intermediate:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.show_intermediate_toggle = QToggle("Show")
        self.show_intermediate_toggle.setCheckable(True)
        self.show_intermediate_toggle.setMinimumHeight(35)
        self.show_intermediate_toggle.setChecked(False)
        layout.addWidget(self.show_intermediate_toggle, row, 1)

        # Save debug images
        row += 1
        label = QLabel("Save Debug Images:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.save_debug_toggle = QToggle("Save")
        self.save_debug_toggle.setCheckable(True)
        self.save_debug_toggle.setMinimumHeight(35)
        self.save_debug_toggle.setChecked(False)
        layout.addWidget(self.save_debug_toggle, row, 1)

        # Verbose logging
        row += 1
        label = QLabel("Verbose Logging:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.verbose_logging_toggle = QToggle("Verbose")
        self.verbose_logging_toggle.setCheckable(True)
        self.verbose_logging_toggle.setMinimumHeight(35)
        self.verbose_logging_toggle.setChecked(True)
        layout.addWidget(self.verbose_logging_toggle, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def connect_default_callbacks(self):
        """Connect default button callbacks"""
        # Main calibration controls
        self.start_calibration_button.clicked.connect(self.start_calibration)
        self.stop_calibration_button.clicked.connect(self.stop_calibration)
        self.save_calibration_button.clicked.connect(lambda: self.save_calibration_requested.emit())
        self.load_calibration_button.clicked.connect(lambda: self.load_calibration_requested.emit())
        self.reset_calibration_button.clicked.connect(lambda: self.reset_calibration_requested.emit())

        # ArUco detection
        self.test_aruco_button.clicked.connect(lambda: self.test_aruco_detection_requested.emit())
        self.detect_workspace_button.clicked.connect(lambda: self.detect_workspace_markers_requested.emit())

        # Perspective transform
        self.compute_perspective_button.clicked.connect(lambda: self.compute_perspective_matrix_requested.emit())
        self.save_perspective_button.clicked.connect(lambda: self.save_perspective_matrix_requested.emit())

        # Camera-Robot transform
        self.compute_transform_button.clicked.connect(lambda: self.compute_camera_robot_transform_requested.emit())
        self.save_transform_button.clicked.connect(lambda: self.save_camera_robot_transform_requested.emit())

        # Debug and testing
        self.capture_image_button.clicked.connect(lambda: self.capture_calibration_image_requested.emit())
        self.test_transformation_button.clicked.connect(lambda: self.test_transformation_requested.emit())
        self.debug_mode_button.toggled.connect(self.toggle_debug_mode)

    def start_calibration(self):
        """Start calibration process"""
        self.calibration_in_progress = True
        self.start_calibration_button.setEnabled(False)
        self.stop_calibration_button.setEnabled(True)
        self.update_calibration_status("Starting...", "info")
        self.update_progress(0, True)
        self.add_log_message("Calibration process started", "info")
        self.start_calibration_requested.emit()

    def stop_calibration(self):
        """Stop calibration process"""
        self.calibration_in_progress = False
        self.start_calibration_button.setEnabled(True)
        self.stop_calibration_button.setEnabled(False)
        self.update_calibration_status("Stopped", "warning")
        self.update_progress(0, False)
        self.add_log_message("Calibration process stopped", "warning")
        self.stop_calibration_requested.emit()

    def toggle_debug_mode(self, checked):
        """Toggle debug mode on/off"""
        self.debug_mode_active = checked

        if checked:
            self.debug_mode_button.setText("Exit Debug Mode")
            self.debug_mode_button.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
            self.add_log_message("Debug mode enabled", "info")
        else:
            self.debug_mode_button.setText("Debug Mode")
            self.debug_mode_button.setStyleSheet("")
            self.add_log_message("Debug mode disabled", "info")

        self.show_debug_view_requested.emit(self.debug_mode_active)

    def update_matrix_status(self, has_matrix, matrix_type="perspective"):
        """Update matrix status labels"""
        status = "Computed" if has_matrix else "Not Computed"
        color = "#4caf50" if has_matrix else "#d32f2f"

        if matrix_type == "perspective" and hasattr(self, 'matrix_status_label'):
            self.matrix_status_label.setText(status)
            self.matrix_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        elif matrix_type == "transform" and hasattr(self, 'transform_status_label'):
            self.transform_status_label.setText(status)
            self.transform_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def update_storage_path(self, path):
        """Update storage path display"""
        if hasattr(self, 'storage_path_label'):
            # Truncate long paths for display
            display_path = path if len(path) < 30 else "..." + path[-27:]
            self.storage_path_label.setText(display_path)
            self.storage_path_label.setToolTip(path)  # Full path in tooltip

    def on_calibration_success(self, message=""):
        """Handle successful calibration"""
        self.calibration_in_progress = False
        self.start_calibration_button.setEnabled(True)
        self.stop_calibration_button.setEnabled(False)
        self.update_calibration_status("Success", "success")
        self.update_progress(100, True)
        self.add_log_message(f"Calibration successful: {message}", "success")

        # Auto-hide progress after success
        QTimer.singleShot(2000, lambda: self.update_progress(0, False))

    def on_calibration_failure(self, message=""):
        """Handle failed calibration"""
        self.calibration_in_progress = False
        self.start_calibration_button.setEnabled(True)
        self.stop_calibration_button.setEnabled(False)
        self.update_calibration_status("Failed", "error")
        self.update_progress(0, False)
        self.add_log_message(f"Calibration failed: {message}", "error")

    def on_aruco_detection_result(self, detected_ids, required_ids):
        """Handle ArUco detection results"""
        if detected_ids:
            detected_set = set(detected_ids)
            required_set = set(required_ids)
            missing = required_set - detected_set

            if missing:
                self.add_log_message(f"ArUco detected: {detected_ids}, missing: {list(missing)}", "warning")
            else:
                self.add_log_message(f"All required ArUco markers detected: {detected_ids}", "success")
        else:
            self.add_log_message("No ArUco markers detected", "error")

    def connectValueChangeCallbacks(self, callback):
        """Connect value change signals to callback methods"""
        # Chessboard settings
        self.chessboard_width_input.valueChanged.connect(
            lambda value: callback("chessboard_width", value, "CalibrationServiceTabLayout"))
        self.chessboard_height_input.valueChanged.connect(
            lambda value: callback("chessboard_height", value, "CalibrationServiceTabLayout"))
        self.square_size_input.valueChanged.connect(
            lambda value: callback("square_size_mm", value, "CalibrationServiceTabLayout"))
        self.skip_frames_input.valueChanged.connect(
            lambda value: callback("skip_frames", value, "CalibrationServiceTabLayout"))

        # ArUco settings
        self.aruco_dictionary_combo.currentTextChanged.connect(
            lambda value: callback("aruco_dictionary", value, "CalibrationServiceTabLayout"))
        self.aruco_flip_toggle.toggled.connect(
            lambda value: callback("aruco_flip", value, "CalibrationServiceTabLayout"))
        self.max_attempts_input.valueChanged.connect(
            lambda value: callback("max_attempts", value, "CalibrationServiceTabLayout"))

        # Perspective settings
        self.auto_compute_toggle.toggled.connect(
            lambda value: callback("auto_compute_perspective", value, "CalibrationServiceTabLayout"))

        # Transform settings
        self.transform_method_combo.currentTextChanged.connect(
            lambda value: callback("transform_method", value, "CalibrationServiceTabLayout"))
        self.min_point_pairs_input.valueChanged.connect(
            lambda value: callback("min_point_pairs", value, "CalibrationServiceTabLayout"))

        # Calibration settings
        self.auto_save_toggle.toggled.connect(
            lambda value: callback("auto_save", value, "CalibrationServiceTabLayout"))
        self.validation_threshold_input.valueChanged.connect(
            lambda value: callback("validation_threshold", value, "CalibrationServiceTabLayout"))
        self.calibration_attempts_input.valueChanged.connect(
            lambda value: callback("calibration_attempts", value, "CalibrationServiceTabLayout"))

        # Debug settings
        self.show_intermediate_toggle.toggled.connect(
            lambda value: callback("show_intermediate", value, "CalibrationServiceTabLayout"))
        self.save_debug_toggle.toggled.connect(
            lambda value: callback("save_debug", value, "CalibrationServiceTabLayout"))
        self.verbose_logging_toggle.toggled.connect(
            lambda value: callback("verbose_logging", value, "CalibrationServiceTabLayout"))

    def getValues(self):
        """Returns a dictionary of current values from all input fields"""
        return {
            # Chessboard settings
            "chessboard_width": self.chessboard_width_input.value(),
            "chessboard_height": self.chessboard_height_input.value(),
            "square_size_mm": self.square_size_input.value(),
            "skip_frames": self.skip_frames_input.value(),

            # ArUco settings
            "aruco_dictionary": self.aruco_dictionary_combo.currentText(),
            "aruco_flip": self.aruco_flip_toggle.isChecked(),
            "max_attempts": self.max_attempts_input.value(),

            # Perspective settings
            "auto_compute_perspective": self.auto_compute_toggle.isChecked(),

            # Transform settings
            "transform_method": self.transform_method_combo.currentText(),
            "min_point_pairs": self.min_point_pairs_input.value(),

            # Calibration settings
            "auto_save": self.auto_save_toggle.isChecked(),
            "validation_threshold": self.validation_threshold_input.value(),
            "calibration_attempts": self.calibration_attempts_input.value(),

            # Debug settings
            "show_intermediate": self.show_intermediate_toggle.isChecked(),
            "save_debug": self.save_debug_toggle.isChecked(),
            "verbose_logging": self.verbose_logging_toggle.isChecked(),
        }

    def updateValues(self, settings_dict):
        """Update input field values from a settings dictionary"""
        print("Updating calibration service input fields from settings...")

        # Chessboard settings
        if "chessboard_width" in settings_dict:
            self.chessboard_width_input.setValue(settings_dict["chessboard_width"])
        if "chessboard_height" in settings_dict:
            self.chessboard_height_input.setValue(settings_dict["chessboard_height"])
        if "square_size_mm" in settings_dict:
            self.square_size_input.setValue(settings_dict["square_size_mm"])
        if "skip_frames" in settings_dict:
            self.skip_frames_input.setValue(settings_dict["skip_frames"])

        # ArUco settings
        if "aruco_dictionary" in settings_dict:
            self.aruco_dictionary_combo.setCurrentText(settings_dict["aruco_dictionary"])
        if "aruco_flip" in settings_dict:
            self.aruco_flip_toggle.setChecked(settings_dict["aruco_flip"])
        if "max_attempts" in settings_dict:
            self.max_attempts_input.setValue(settings_dict["max_attempts"])

        # Perspective settings
        if "auto_compute_perspective" in settings_dict:
            self.auto_compute_toggle.setChecked(settings_dict["auto_compute_perspective"])

        # Transform settings
        if "transform_method" in settings_dict:
            self.transform_method_combo.setCurrentText(settings_dict["transform_method"])
        if "min_point_pairs" in settings_dict:
            self.min_point_pairs_input.setValue(settings_dict["min_point_pairs"])

        # Calibration settings
        if "auto_save" in settings_dict:
            self.auto_save_toggle.setChecked(settings_dict["auto_save"])
        if "validation_threshold" in settings_dict:
            self.validation_threshold_input.setValue(settings_dict["validation_threshold"])
        if "calibration_attempts" in settings_dict:
            self.calibration_attempts_input.setValue(settings_dict["calibration_attempts"])

        # Debug settings
        if "show_intermediate" in settings_dict:
            self.show_intermediate_toggle.setChecked(settings_dict["show_intermediate"])
        if "save_debug" in settings_dict:
            self.save_debug_toggle.setChecked(settings_dict["save_debug"])
        if "verbose_logging" in settings_dict:
            self.verbose_logging_toggle.setChecked(settings_dict["verbose_logging"])

        print("Calibration service settings updated from dictionary.")

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()

    def enable_calibration_controls(self, enabled=True):
        """Enable or disable calibration controls during operation"""
        controls = [
            self.chessboard_width_input, self.chessboard_height_input,
            self.square_size_input, self.skip_frames_input,
            self.aruco_dictionary_combo, self.max_attempts_input
        ]

        for control in controls:
            if hasattr(control, 'setEnabled'):
                control.setEnabled(enabled)

    def set_calibration_mode(self, mode):
        """Set calibration mode and update UI accordingly"""
        modes = {
            "idle": {"status": "Ready", "type": "ready"},
            "detecting": {"status": "Detecting Markers...", "type": "info"},
            "calibrating": {"status": "Calibrating...", "type": "info"},
            "computing": {"status": "Computing Transform...", "type": "info"},
            "saving": {"status": "Saving Results...", "type": "info"}
        }

        if mode in modes:
            self.update_calibration_status(modes[mode]["status"], modes[mode]["type"])
            self.enable_calibration_controls(mode == "idle")

    def get_calibration_settings(self):
        """Get calibration settings for the service"""
        return {
            'chessboardWidth': self.chessboard_width_input.value(),
            'chessboardHeight': self.chessboard_height_input.value(),
            'squareSizeMM': self.square_size_input.value(),
            'skipFrames': self.skip_frames_input.value(),
            'arucoDict': self.aruco_dictionary_combo.currentText(),
            'arucoFlip': self.aruco_flip_toggle.isChecked(),
            'maxAttempts': self.max_attempts_input.value(),
            'autoSave': self.auto_save_toggle.isChecked(),
            'debug': self.debug_mode_active,
            'showIntermediate': self.show_intermediate_toggle.isChecked(),
            'saveDebug': self.save_debug_toggle.isChecked(),
            'verboseLogging': self.verbose_logging_toggle.isChecked()
        }

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    main_widget = QWidget()
    layout = CalibrationServiceTabLayout(main_widget)
    main_widget.setLayout(layout)
    main_widget.show()
    sys.exit(app.exec())