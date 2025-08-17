from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QSpinBox, QPushButton,
    QGridLayout, QGroupBox, QVBoxLayout, QHBoxLayout, QScrollArea
)
import sys

class RobotConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Config UI")
        self.resize(600, 700)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        # --- Robot Info ---
        robot_group = QGroupBox("Robot Info")
        robot_layout = QGridLayout()
        self.ip_edit = QLineEdit("192.168.58.2")
        self.tool_edit = QSpinBox()
        self.tool_edit.setRange(0, 10)
        self.tool_edit.setValue(0)
        self.user_edit = QSpinBox()
        self.user_edit.setRange(0, 10)
        self.user_edit.setValue(0)
        robot_layout.addWidget(QLabel("ROBOT_IP:"), 0, 0)
        robot_layout.addWidget(self.ip_edit, 0, 1)
        robot_layout.addWidget(QLabel("ROBOT_TOOL:"), 1, 0)
        robot_layout.addWidget(self.tool_edit, 1, 1)
        robot_layout.addWidget(QLabel("ROBOT_USER:"), 2, 0)
        robot_layout.addWidget(self.user_edit, 2, 1)
        robot_group.setLayout(robot_layout)
        main_layout.addWidget(robot_group)

        # --- Positions & related groups ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Data structured as {group_name: {position_name: (vel, acc)}}
        # Start with None or example defaults
        data = {
            "LOGIN_POS": {"VEL": None, "ACC": None},
            "HOME_POS": {"VEL": None, "ACC": None},
            "CALIBRATION_POS": {"VEL": None, "ACC": None},

            "JOG": {"JOG_VELOCITY": 50, "JOG_ACCELERATION": 50},

            "NOZZLE CLEAN": {
                "CLEAN_NOZZLE_1": None,
                "CLEAN_NOZZLE_2": None,
                "CLEAN_NOZZLE_3": None,
                "CLEAN_NOZZLE_VELOCITY": 30,
                "CLEAN_NOZZLE_ACCELERATION": 30,
            },

            "TOOL CHANGER": {
                "TOOL_CHANGING_VELOCITY": 100,
                "TOOL_CHANGING_ACCELERATION": 30,
            },

            "SLOT 0": {
                "SLOT_0_PICKUP_0": None,
                "SLOT_0_PICKUP_1": None,
                "SLOT_0_PICKUP_2": None,
                "SLOT_0_PICKUP_3": None,
                "SLOT_0_DROPOFF_1": None,
                "SLOT_0_DROPOFF_2": None,
                "SLOT_0_DROPOFF_3": None,
                "SLOT_0_DROPOFF_4": None,
            },

            "SLOT 1": {
                "SLOT_1_PICKUP_0": None,
                "SLOT_1_PICKUP_1": None,
                "SLOT_1_PICKUP_2": None,
                "SLOT_1_DROPOFF_1": None,
                "SLOT_1_DROPOFF_2": None,
                "SLOT_1_DROPOFF_3": None,
            },

            "SLOT 4": {
                "SLOT_4_PICKUP_1": None,
                "SLOT_4_PICKUP_2": None,
                "SLOT_4_PICKUP_3": None,
                "SLOT_4_DROPOFF_1": None,
                "SLOT_4_DROPOFF_2": None,
                "SLOT_4_DROPOFF_3": None,
            },
        }

        self.spinboxes = {}

        for group, positions in data.items():
            group_box = QGroupBox(group)
            grid = QGridLayout()
            row = 0
            for pos_name, val in positions.items():
                # If the pos_name ends with _VELOCITY or _ACCELERATION, only one input needed
                # Otherwise show Vel and Acc spinboxes side by side

                # For JOG, NOZZLE CLEAN, TOOL CHANGER velocities and accelerations are individual keys,
                # treat those specially as single spinbox lines

                # Detect if pos_name includes velocity/acceleration word to show only one spinbox
                pos_name_upper = pos_name.upper()
                if "VELOCITY" in pos_name_upper or "ACCELERATION" in pos_name_upper:
                    label = QLabel(pos_name)
                    spin = QSpinBox()
                    spin.setRange(0, 1000)
                    spin.setValue(val or 0)
                    grid.addWidget(label, row, 0)
                    grid.addWidget(spin, row, 1)
                    self.spinboxes[pos_name] = spin
                    row += 1
                else:
                    # Show velocity and acceleration spinboxes for the position
                    label = QLabel(pos_name)
                    grid.addWidget(label, row, 0)

                    vel_label = QLabel("VEL")
                    vel_spin = QSpinBox()
                    vel_spin.setRange(0, 1000)
                    vel_spin.setValue(0)
                    acc_label = QLabel("ACC")
                    acc_spin = QSpinBox()
                    acc_spin.setRange(0, 1000)
                    acc_spin.setValue(0)

                    grid.addWidget(vel_label, row, 1)
                    grid.addWidget(vel_spin, row, 2)
                    grid.addWidget(acc_label, row, 3)
                    grid.addWidget(acc_spin, row, 4)

                    self.spinboxes[pos_name] = {"vel": vel_spin, "acc": acc_spin}
                    row += 1

            group_box.setLayout(grid)
            content_layout.addWidget(group_box)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Save/Reset buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Reset")
        save_btn.clicked.connect(self.save)
        reset_btn.clicked.connect(self.reset)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def save(self):
        data_out = {
            "ROBOT_IP": self.ip_edit.text(),
            "ROBOT_TOOL": self.tool_edit.value(),
            "ROBOT_USER": self.user_edit.value(),
            "POSITIONS": {}
        }

        for key, widget in self.spinboxes.items():
            if isinstance(widget, QSpinBox):
                # Single spinbox (vel or acc)
                data_out["POSITIONS"][key] = widget.value()
            else:
                # dict with 'vel' and 'acc' spinboxes
                data_out["POSITIONS"][key] = {
                    "vel": widget["vel"].value(),
                    "acc": widget["acc"].value()
                }

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Saved Data", str(data_out))

    def reset(self):
        # Reset robot info
        self.ip_edit.setText("192.168.58.2")
        self.tool_edit.setValue(0)
        self.user_edit.setValue(0)

        # Reset all spinboxes to 0 or default values for known ones
        defaults = {
            "JOG_VELOCITY": 50,
            "JOG_ACCELERATION": 50,
            "CLEAN_NOZZLE_VELOCITY": 30,
            "CLEAN_NOZZLE_ACCELERATION": 30,
            "TOOL_CHANGING_VELOCITY": 100,
            "TOOL_CHANGING_ACCELERATION": 30,
        }
        for key, widget in self.spinboxes.items():
            if isinstance(widget, QSpinBox):
                widget.setValue(defaults.get(key, 0))
            else:
                widget["vel"].setValue(0)
                widget["acc"].setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotConfigUI()
    window.show()
    sys.exit(app.exec())
