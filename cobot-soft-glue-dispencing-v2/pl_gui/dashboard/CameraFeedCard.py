import numpy as np
from PyQt6.QtGui import QPixmap
from pl_gui.dashboard.DraggableCard import DraggableCard


class CameraFeedCard(DraggableCard):
    def __init__(self, camera_feed, toggleCallback=None, parent=None, **kwargs):
        self.camera_feed = camera_feed
        super().__init__("Camera Feed", content_widgets=[self.camera_feed] if self.camera_feed else [], **kwargs)
        self.callback = toggleCallback
        self.camera_feed.toggleCallback = self.toggle_resolution  # Set the callback to adjust layout on toggle
        self.hideLabel()
        self.adjustLayout()  # Apply appropriate styling/resizing


    def toggle_resolution(self):
        self.adjustLayout()
        if self.callback:
            self.callback()

    def adjustLayout(self):
        self.setStyleSheet("""
            QFrame {
                background-color: black;
                padding: 0px;
                border: none;
                border-radius: 0px;
            }
        """)

        is_high_res = self.camera_feed.current_resolution == self.camera_feed.resolution_large

        if is_high_res:
            self.setFixedSize(1280, 720)
            self.setContentsMargins(0, 0, 0, 0)

            if hasattr(self, "title_label"):
                self.title_label.hide()

            if hasattr(self, "layout"):
                self.layout.setContentsMargins(0, 0, 0, 0)
                self.layout.setSpacing(0)
        else:
            self.setFixedSize(400, 300)
            self.setContentsMargins(2, 2, 2, 2)

            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    padding: 10px;
                }
            """)

            if hasattr(self, "layout"):
                self.layout.setContentsMargins(2, 2, 2, 2)
                self.layout.setSpacing(5)

        self.updateGeometry()


    def on_close(self):
        print(f"Camera Feed on_close")

        super().on_close()

    def closeEvent(self, event):
        super().closeEvent(event)

# Example usage for standalone testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    from pl_gui.CameraFeed import CameraFeed


    def updateCallback():
        from PyQt6.QtGui import QColor
        pixmap = QPixmap(320, 180)
        pixmap.fill(QColor("red"))
        image = np.zeros((180, 320, 3), dtype=np.uint8)
        return image


    app = QApplication(sys.argv)
    camera_feed = CameraFeed(updateCallback=updateCallback, toggleCallback=lambda: None)
    camera_feed_card = CameraFeedCard(camera_feed)
    camera_feed_card.show()
    sys.exit(app.exec())
