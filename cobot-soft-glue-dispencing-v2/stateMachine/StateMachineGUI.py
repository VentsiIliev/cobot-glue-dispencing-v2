import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import QTimer

# Import your state machine modules
from stateMachine.DummyGlueSprayingApplication import DummyGlueSprayingApplication
from stateMachine.StateMachineEnhancedGlueSprayingApplication import StateMachineEnhancedGlueSprayingApplication


class StateMachineGUI(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

        self.setWindowTitle("State Machine Tester")
        self.resize(300, 250)

        layout = QVBoxLayout()

        # State label
        self.state_label = QLabel(f"Current State: {self.app_instance.get_current_state().name}")
        self.state_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.state_label)

        # Buttons
        buttons = [
            ("Start", lambda: self.app_instance.start(contourMatching=True)),
            ("Calibrate Robot", self.app_instance.calibrateRobot),
            ("Create Workpiece", self.app_instance.createWorkpiece),
            ("Emergency Stop", self.app_instance.emergency_stop),
            ("Reset", self.app_instance.reset),
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.run_command(c))
            layout.addWidget(btn)

        self.setLayout(layout)

        # Timer to update state label
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_state_label)
        self.timer.start(200)

    def run_command(self, command):
        def worker():
            result = command()
            print("[GUI Command Result]", result)
        threading.Thread(target=worker, daemon=True).start()

    def update_state_label(self):
        self.state_label.setText(f"Current State: {self.app_instance.get_current_state().name}")


if __name__ == "__main__":
    original_app = DummyGlueSprayingApplication()
    app_instance = StateMachineEnhancedGlueSprayingApplication(original_app)

    qt_app = QApplication(sys.argv)
    gui = StateMachineGUI(app_instance)
    gui.show()
    sys.exit(qt_app.exec())
