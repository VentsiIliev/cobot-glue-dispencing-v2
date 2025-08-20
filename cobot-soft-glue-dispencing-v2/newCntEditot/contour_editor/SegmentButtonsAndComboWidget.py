import os
import sys
from types import SimpleNamespace

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout,
    QPushButton, QComboBox, QSizePolicy
)

# --- Resource Paths ---
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
BIN_ICON = os.path.join(RESOURCE_DIR, "BIN_BUTTON_SQUARE.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")
ACTIVE_ICON = os.path.join(RESOURCE_DIR, "active.png")
INACTIVE_ICON = os.path.join(RESOURCE_DIR, "inactive.png")
DROPDOWN_OPEN_ICON = os.path.join(RESOURCE_DIR, "dropdown_open.png")


class SegmentButtonsAndComboWidget(QWidget):
    def __init__(self, seg_index, segment, layer_name,
                 on_visibility, on_activate, on_delete, on_settings, on_layer_change):
        super().__init__()

        self.segment = segment
        self.on_visibility = on_visibility

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Buttons
        self.visibility_btn = self._create_visibility_button()
        layout.addWidget(self.visibility_btn)

        self.active_btn = self._create_icon_button(
            ACTIVE_ICON if getattr(segment, "is_active", False) else INACTIVE_ICON,
            "Set as active segment",
            on_activate
        )
        layout.addWidget(self.active_btn)

        self.delete_btn = self._create_icon_button(
            BIN_ICON, "Delete this segment", on_delete
        )
        layout.addWidget(self.delete_btn)

        self.settings_btn = QPushButton("S")
        self.settings_btn.setToolTip("Segment settings")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.clicked.connect(on_settings)
        layout.addWidget(self.settings_btn)

        # Combo Box for Layer Selection
        self.combo_box = QComboBox()
        self.combo_box.addItems(["External", "Contour", "Fill"])
        self.combo_box.setCurrentText(layer_name)
        self.combo_box.setFixedHeight(40)
        self.combo_box.setMinimumWidth(100)
        self.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_box.currentTextChanged.connect(on_layer_change)
        layout.addWidget(self.combo_box)

        layout.addStretch()

    def _create_icon_button(self, icon_path, tooltip, callback):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(32, 32))
        button.setToolTip(tooltip)
        button.setFixedSize(40, 40)
        button.clicked.connect(callback)
        return button

    def _create_visibility_button(self):
        button = QPushButton()
        button.setCheckable(True)
        is_visible = getattr(self.segment, "visible", True)
        button.setChecked(is_visible)
        button.setIcon(QIcon(HIDE_ICON if is_visible else SHOW_ICON))
        print("Visibility icon set to:", HIDE_ICON if is_visible else SHOW_ICON)
        button.setIconSize(QSize(32, 32))
        button.setToolTip("Toggle segment visibility")
        button.setFixedSize(40, 40)
        button.clicked.connect(lambda: self._toggle_visibility(button))
        return button

    def _toggle_visibility(self, button):
        is_visible = button.isChecked()
        button.setIcon(QIcon(HIDE_ICON if is_visible else SHOW_ICON))
        self.on_visibility(button)


# --- Testing ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    segment = SimpleNamespace(visible=True, is_active=False)
    layer_name = "Contour"


    def on_visibility(btn):
        print("Visibility toggled:", btn.isChecked())


    def on_activate():
        print("Activated")


    def on_delete():
        print("Deleted")


    def on_settings():
        print("Settings opened")


    def on_layer_change(value):
        print("Layer changed to:", value)


    widget = SegmentButtonsAndComboWidget(
        seg_index=0,
        segment=segment,
        layer_name=layer_name,
        on_visibility=on_visibility,
        on_activate=on_activate,
        on_delete=on_delete,
        on_settings=on_settings,
        on_layer_change=on_layer_change
    )
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SegmentButtonsAndComboWidget(
        seg_index=0,
        segment=SimpleNamespace(visible=True, is_active=False),
        layer_name="Contour",
        on_visibility=lambda btn: print("Visibility toggled:", btn.isChecked()),
        on_activate=lambda: print("Activated"),
        on_delete=lambda: print("Deleted"),
        on_settings=lambda: print("Settings opened"),
        on_layer_change=lambda value: print("Layer changed to:", value)
    )
    widget.show()
    sys.exit(app.exec())
