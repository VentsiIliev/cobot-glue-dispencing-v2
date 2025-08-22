from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget


class FolderOverlay(QWidget):
    """Overlay widget that appears when folder is opened"""

    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.disable_overlay_close = False
        # Animation for fade in/out
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fade_in(self):
        """Animate overlay appearance"""
        self.setWindowOpacity(0.0)
        self.show()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def fade_out(self):
        """Animate overlay disappearance"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.hide)
        self.opacity_animation.start()

    def mousePressEvent(self, event):
        """Close folder when clicking outside, unless disabled"""
        if not self.disable_overlay_close:
            parent = self.parent()
            expanded_view = None
            if hasattr(parent, 'current_app_folder') and hasattr(parent.current_app_folder, 'expanded_view'):
                expanded_view = parent.current_app_folder.expanded_view
            if expanded_view:
                if expanded_view._current_app_name:
                    # App is running - minimize expanded view (collapse to floating icon)
                    expanded_view.close_from_outside()
                    event.accept()
                    return

            # No app running - normal close
            self.close_requested.emit()
        super().mousePressEvent(event)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    overlay = FolderOverlay()
    overlay.resize(800, 600)
    overlay.fade_in()
    overlay.show()
    sys.exit(app.exec())