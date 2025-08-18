import sys
from enum import Enum
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGroupBox, QGridLayout, QPushButton,
                             QTextEdit, QProgressBar)
from API.MessageBroker import MessageBroker
from pl_gui.ToastWidget import ToastWidget
from pl_gui.customWidgets.SwitchButton import QToggle
from pl_gui.settings_view.BaseSettingsTabLayout import BaseSettingsTabLayout
from pl_gui.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox, FocusSpinBox
from PyQt6.QtWidgets import QScroller
from PyQt6.QtCore import Qt
from pl_gui.robotManualControl.RobotJogWidget import RobotJogWidget

class CalibrationServiceTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Robot movement signals
    jogRequested = QtCore.pyqtSignal(str, str, str, float)
    update_camera_feed_signal = QtCore.pyqtSignal()
    move_to_pickup_requested = QtCore.pyqtSignal()
    move_to_calibration_requested = QtCore.pyqtSignal()
    save_point_requested = QtCore.pyqtSignal()

    # Image capture signals
    capture_image_requested = QtCore.pyqtSignal()
    save_images_requested = QtCore.pyqtSignal()

    # Calibration process signals
    calibrate_camera_requested = QtCore.pyqtSignal()
    detect_markers_requested = QtCore.pyqtSignal()
    compute_homography_requested = QtCore.pyqtSignal()
    auto_calibrate_requested = QtCore.pyqtSignal()
    test_calibration_requested = QtCore.pyqtSignal()

    # Debug and testing signals
    show_debug_view_requested = QtCore.pyqtSignal(bool)

    def __init__(self, parent_widget=None, calibration_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.parent_widget = parent_widget
        self.calibration_service = calibration_service
        self.debug_mode_active = False
        self.calibration_in_progress = False

        # Create main content with new layout
        self.create_main_content()

        self.updateFrequency = 30  # in milliseconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_camera_feed_signal.emit())
        self.timer.start(self.updateFrequency)

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        broker = MessageBroker()
        broker.subscribe("vision-system/calibration-feedback",self.addLog)
        broker.subscribe("vision-system/calibration_image_captured",self.addLog)

    def addLog(self, message):
        print("Message received in addLog:", message)
        """Add a log message to the output area"""
        if hasattr(self, 'log_output'):
            self.log_output.append(message)
            self.log_output.ensureCursorVisible()

    def update_camera_preview_from_cv2(self, cv2_image):
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

    def update_camera_feed(self, frame):
        try:
            if frame is not None:
                self.update_camera_preview_from_cv2(frame)
            else:
                return
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            pass

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
        self.calibration_preview_label.setMinimumSize(460, 259)
        self.calibration_preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

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

        # Control buttons grid - UPDATED SECTION
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Robot movement buttons
        self.move_to_pickup_button = QPushButton("Move to Pickup")
        self.move_to_calibration_button = QPushButton("Move to Calibration")

        movement_buttons = [self.move_to_pickup_button, self.move_to_calibration_button]
        for i, btn in enumerate(movement_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Image capture buttons
        # self.save_images_button = QPushButton("Save Images")

        self.capture_image_button = QPushButton("Capture Image")
        self.capture_image_button.setMinimumHeight(40)
        button_grid.addWidget(self.capture_image_button,1, 0,1,2)

        # Row 2: Calibration process buttons
        # self.calibrate_camera_button = QPushButton("Calibrate Camera")
        # self.detect_markers_button = QPushButton("Detect Markers")

        # calibration_buttons = [self.detect_markers_button]
        # for i, btn in enumerate(calibration_buttons):
        #     btn.setMinimumHeight(40)
        #     button_grid.addWidget(btn, 2, i)

        # Row 3: Compute homography (spans both columns)

        self.calibrate_camera_button = QPushButton("Calibrate Camera")
        self.calibrate_camera_button.setMinimumHeight(40)
        button_grid.addWidget(self.calibrate_camera_button, 2, 0,1,2)

        self.compute_homography_button = QPushButton("Calibrate Robot")
        self.compute_homography_button.setMinimumHeight(40)
        button_grid.addWidget(self.compute_homography_button, 3, 0, 1, 2)  # Span 2 columns

        self.auto_calibrate = QPushButton("Camera and Robot Calibration")
        self.auto_calibrate.setMinimumHeight(40)
        button_grid.addWidget(self.auto_calibrate, 4, 0, 1, 2)  # Span 2 columns

        self.test_calibration_button = QPushButton("Test Calibration")
        self.test_calibration_button.setMinimumHeight(40)
        button_grid.addWidget(self.test_calibration_button, 5, 0, 1, 2)  # Span 2 columns

        preview_layout.addLayout(button_grid)

        # Log output area
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(120)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Logs")
        preview_layout.addWidget(self.log_output)

        preview_layout.addStretch()

        self.connect_default_callbacks()

        for btn in movement_buttons   + [self.compute_homography_button,
                                                                               self.auto_calibrate]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
            self.calibration_preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

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
        """Create the main content with camera preview on left, settings in middle, and robot jog on right"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(2)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left: Camera Preview ---
        preview_widget = self.create_calibration_preview_section()
        # Set minimum width to prevent excessive shrinking
        # preview_widget.setMinimumWidth(400)

        # --- Middle: Settings scroll area ---
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # SOLUTION 1: Set minimum width for settings area
        settings_scroll_area.setMinimumWidth(200)  # Prevent squashing below this width

        # SOLUTION 2: Set preferred size
        settings_scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(2)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        # Add all the settings groups to the middle section
        self.add_settings_to_layout(settings_content_layout)

        settings_scroll_area.setWidget(settings_content_widget)

        # --- Right: Robot Jog Widget ---
        robot_jog_widget = QWidget()
        robot_jog_widget.setMinimumWidth(400)  # Prevent excessive shrinking
        robot_jog_layout = QVBoxLayout(robot_jog_widget)
        robot_jog_layout.setSpacing(2)
        robot_jog_layout.setContentsMargins(0, 0, 0, 0)

        self.robotManualControlWidget = RobotJogWidget(self.parent_widget)
        self.robotManualControlWidget.jogRequested.connect(lambda command, axis, direction, value:
                                                 self.jogRequested.emit(command, axis, direction, value))
        self.robotManualControlWidget.save_point_requested.connect(lambda: self.save_point_requested.emit())
        robot_jog_layout.addWidget(self.robotManualControlWidget,1)
        # robot_jog_layout.addStretch()

        # SOLUTION 3: Use different stretch factors
        # Give middle section higher priority to maintain its space
        main_horizontal_layout.addWidget(preview_widget, 1)  # Left - stretch factor 1
        main_horizontal_layout.addWidget(settings_scroll_area, 2)  # Middle - stretch factor 2 (more space priority)
        main_horizontal_layout.addWidget(robot_jog_widget, 1)  # Right - stretch factor 1
        # --- Wrap inside QWidget ---
        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)

        # SOLUTION 5: Set minimum width for the entire main widget
        main_widget.setMinimumWidth(1200)  # Ensure window doesn't get too narrow

        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout in vertical arrangement"""
        # First row of settings
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        parent_layout.addLayout(first_row)

        # Second row of settings
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        parent_layout.addLayout(second_row)

        # Third row of settings
        third_row = QHBoxLayout()
        third_row.setSpacing(15)
        parent_layout.addLayout(third_row)

    def connect_default_callbacks(self):
        """Connect default button callbacks"""
        # Robot movement controls
        self.move_to_pickup_button.clicked.connect(lambda: self.move_to_pickup_requested.emit())
        self.move_to_calibration_button.clicked.connect(lambda: self.move_to_calibration_requested.emit())

        # Image capture controls
        self.capture_image_button.clicked.connect(lambda: self.capture_image_requested.emit())
        # self.save_images_button.clicked.connect(lambda: self.save_images_requested.emit())

        # Calibration process controls
        self.calibrate_camera_button.clicked.connect(lambda: self.calibrate_camera_requested.emit())
        # self.detect_markers_button.clicked.connect(lambda: self.detect_markers_requested.emit())
        self.compute_homography_button.clicked.connect(lambda: self.compute_homography_requested.emit())
        self.auto_calibrate.clicked.connect(lambda: self.auto_calibrate_requested.emit())
        self.test_calibration_button.clicked.connect(lambda: self.test_calibration_requested.emit())

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    main_widget = QWidget()
    layout = CalibrationServiceTabLayout(main_widget)
    main_widget.setLayout(layout)
    main_widget.show()
    sys.exit(app.exec())