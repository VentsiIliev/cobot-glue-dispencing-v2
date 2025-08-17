import sys
import time
import math
import threading
import numpy as np
import cv2
from collections import deque
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap, QPalette, QPainter, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from API.MessageBroker import MessageBroker


class CompactCard(QFrame):
    """Compact card component with minimal padding"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)

        # Reduced shadow for compact design
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class CompactTimeMetric(QWidget):
    """Compact time metric with horizontal layout"""

    def __init__(self, title, value="0.00 s", color="#1976D2", parent=None):
        super().__init__(parent)
        self.color = color
        self.init_ui(title, value)

    def init_ui(self, title, value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Title label (smaller)
        self.title_label = QLabel(title + ":")
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        self.title_label.setStyleSheet(f"color: {self.color}; font-weight: 500;")

        # Value label (compact)
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #212121; font-weight: 600;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_value(self, value):
        self.value_label.setText(value)


class SmoothTrajectoryWidget(QWidget):
    def __init__(self, image_width=640, image_height=360):
        super().__init__()

        # Store image dimensions
        self.image_width = image_width
        self.image_height = image_height

        # External data
        self.estimated_time_value = 0.0
        self.time_left_value = 0.0

        # Frame and trajectory storage
        self.base_frame = None
        self.current_frame = None

        # Trajectory tracking
        self.trajectory_points = deque()
        self.current_position = None
        self.last_position = None

        # Trail settings
        self.trail_length = 100
        self.trail_thickness = 2
        self.trail_fade = False
        self.show_current_point = True
        self.interpolate_motion = True

        # Colors (BGR) - Material Design colors
        self.trail_color = (156, 39, 176)  # Purple 500
        self.current_point_color = (0, 0, 128)  # Navy Blue

        # Performance tracking
        self.start_time = time.time() * 1000
        self.update_count = 0
        self.is_running = True

        self.init_ui()

        # Timer to refresh display
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(33)  # 30 FPS

    def init_ui(self):
        self.setWindowTitle("Trajectory Tracker")

        # Calculate exact widget size based on image dimensions
        # Only add necessary padding, no extra space
        widget_width = self.image_width + 32  # 24 margins + 8 card padding
        widget_height = self.image_height + 80  # Metrics height + margins + card padding

        self.setFixedSize(widget_width, widget_height)

        # Set modern background
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins
        main_layout.setSpacing(8)  # Reduced spacing

        # Compact metrics at top
        metrics_card = CompactCard()
        metrics_layout = QHBoxLayout(metrics_card)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(16)

        # Estimated Time metric (compact horizontal layout)
        self.estimated_metric = CompactTimeMetric("Est. Time", "0.00 s", "#1976D2")

        # Time Left metric (compact horizontal layout)
        self.time_left_metric = CompactTimeMetric("Time Left", "0.00 s", "#388E3C")

        metrics_layout.addWidget(self.estimated_metric)
        metrics_layout.addWidget(self.time_left_metric)
        metrics_layout.addStretch()  # Push metrics to left

        main_layout.addWidget(metrics_card)

        # Camera view with fixed size - no expansion
        camera_card = CompactCard()
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(4, 4, 4, 4)  # Minimal padding

        self.image_label = QLabel()

        # Set fixed size based on provided image dimensions - no expanding!
        self.image_label.setFixedSize(self.image_width, self.image_height)

        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border-radius: 6px;
                border: 1px solid #E0E0E0;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        camera_layout.addWidget(self.image_label)

        # Add stretch to push everything to top-left, preventing white space
        camera_layout.addStretch()

        # Add camera card without stretch factor - only takes space it needs
        main_layout.addWidget(camera_card)

        # Add stretch at the end to push content to top
        main_layout.addStretch()

        # Remove the stretch factor settings since we're not using stretch factors anymore
        # The layout will now only take the space it actually needs

    def update(self, message=None):
        if message is None:
            return

        x, y = message.get("x", 0), message.get("y", 0)
        # Adjust center point based on actual image dimensions
        # screen_x = int(x + self.image_width // 2)
        # screen_y = int(y + self.image_height // 2)

        self.last_position = self.current_position
        self.current_position = (x, y)

        if self.last_position is not None and self.interpolate_motion:
            self._add_interpolated_points(self.last_position, self.current_position)
        else:
            self.trajectory_points.append((x, y, time.time()))

    def _add_interpolated_points(self, start_pos, end_pos, num_interpolated=3):
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        current_time = time.time()

        distance = np.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

        if distance > 5:
            for i in range(1, num_interpolated + 1):
                t = i / (num_interpolated + 1)
                interp_x = int(start_x + t * (end_x - start_x))
                interp_y = int(start_y + t * (end_y - start_y))
                self.trajectory_points.append((interp_x, interp_y, current_time))

        self.trajectory_points.append((end_x, end_y, current_time))

    def update_display(self):
        if self.base_frame is None:
            return

        self.current_frame = self.base_frame.copy()
        self._draw_smooth_trail()

        if self.current_position is not None and self.show_current_point:
            # Draw current position with Material Design styling
            cv2.circle(self.current_frame, self.current_position, 8, self.current_point_color, -1)
            cv2.circle(self.current_frame, self.current_position, 12, (255, 255, 255), 2)

        self._update_label_from_frame()
        self.update_count += 1

        # Update time displays
        self.estimated_metric.update_value(f"{self.estimated_time_value:.2f} s")
        self.time_left_metric.update_value(f"{self.time_left_value:.2f} s")

    def _draw_smooth_trail(self):
        if len(self.trajectory_points) < 2:
            return

        points = np.array([(p[0], p[1]) for p in self.trajectory_points], dtype=np.float32)
        smoothed_points = []
        kernel_size = 5

        for i in range(len(points)):
            start = max(0, i - kernel_size + 1)
            avg_x = np.mean(points[start:i + 1, 0])
            avg_y = np.mean(points[start:i + 1, 1])
            smoothed_points.append((int(avg_x), int(avg_y)))

        total = len(smoothed_points)

        for i in range(total - 1):
            fade_factor = (i + 1) / total if self.trail_fade else 1.0
            color = (
                int(self.trail_color[0] * fade_factor),
                int(self.trail_color[1] * fade_factor),
                int(self.trail_color[2] * fade_factor)
            )
            thickness = max(1, int(self.trail_thickness * fade_factor * 1.5))
            cv2.line(self.current_frame, smoothed_points[i], smoothed_points[i + 1],
                     color, thickness, lineType=cv2.LINE_AA)

    def _update_label_from_frame(self):
        rgb_image = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        q_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)

        # Convert to pixmap and set directly without scaling
        # The image should exactly match the label's fixed size
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

    def set_image(self, message=None):
        """Receive an external image from outside."""
        # Verify that the frame matches expected dimensions

        frame = message.get("image")
        frame = cv2.resize(frame, (self.image_width, self.image_height))

        self.base_frame = frame.copy()
        self.clear_trail()

    def set_estimated_time(self, time_value):
        """Update estimated time value"""
        self.estimated_time_value = time_value

    def set_time_left(self, time_value):
        """Update time left value"""
        self.time_left_value = time_value

    def clear_trail(self):
        self.trajectory_points.clear()
        self.current_position = None
        self.last_position = None

    def get_image_dimensions(self):
        """Return the configured image dimensions"""
        return self.image_width, self.image_height

    def set_image_dimensions(self, width, height):
        """Update image dimensions and adjust widget accordingly"""
        self.image_width = width
        self.image_height = height

        # Update widget to exact size needed
        widget_width = width + 32  # 24 margins + 8 card padding
        widget_height = height + 80  # Metrics height + margins + card padding
        self.setFixedSize(widget_width, widget_height)

        # Update image label to new fixed size
        self.image_label.setFixedSize(width, height)

        # Clear current trajectory since coordinates may be invalid
        self.clear_trail()

    def closeEvent(self, event):
        self.is_running = False
        self.timer.stop()
        event.accept()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Space-Optimized Trajectory Tracker")
        self.setGeometry(50, 50, 800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        layout.setSpacing(4)  # Reduced spacing

        # Smaller, compact title
        title = QLabel("Trajectory Tracker")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #424242; margin: 4px;")
        layout.addWidget(title)

        self.camera_widget = SmoothTrajectoryWidget(image_width=1280,image_height=720)
        self.camera_widget.set_image(np.zeros((1280, 720, 3), dtype=np.uint8))
        self.camera_widget.estimated_time_value = 5.0
        self.camera_widget.time_left_value = 3.0
        broker = MessageBroker()
        broker.subscribe("robot/trajectory/point", self.camera_widget.update)
        broker.subscribe("robot/trajectory/updateImage", self.camera_widget.set_image)
        layout.addWidget(self.camera_widget)
        self.setLayout(layout)
        self.start_smooth_trajectory_thread()

    def start_smooth_trajectory_thread(self):
        def generate_smooth_trajectory():
            broker = MessageBroker()
            t = 0.0
            dt = 0.02
            while True:
                x = 80 * math.cos(t * 2)
                y = 80 * math.sin(t * 2)
                broker.publish("robot/trajectory/point", {"x": x, "y": y})
                t += dt
                time.sleep(dt)

        threading.Thread(target=generate_smooth_trajectory, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

