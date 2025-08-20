from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QPushButton


class TouchButton(QPushButton):
    """Touch-optimized button with improved styling and feedback"""

    def __init__(self, text="", size=(60, 60)):
        super().__init__(text)
        self.setFixedSize(QSize(*size))

        # Professional styling for touch
        self.setStyleSheet("""
            TouchButton {
                border: 2px solid #dcdcdc;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: 600;
                font-size: 12px;
            }
            TouchButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            TouchButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
                padding: 2px;
            }
            TouchButton:checked {
                background-color: #007bff;
                border-color: #0056b3;
                color: white;
            }
            TouchButton:disabled {
                background-color: #f8f9fa;
                color: #9ca3af;
                border-color: #e5e7eb;
            }
        """)

if __name__ == "__main__":
    # Example usage
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    button = TouchButton("Click Me", size=(80, 40))
    button.show()
    sys.exit(app.exec())