from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QPushButton, QLabel

import os

from newCntEditot.contour_editor.TouchButton import TouchButton

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
FOLDER_ICON = os.path.join(RESOURCE_DIR, "folder.png")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")


class LayerButtonsWidget(QWidget):
    toggleRequested = pyqtSignal(str, bool)  # layer_name, is_expanded
    selectedChanged = pyqtSignal(str, bool)  # layer_name, selected
    layerVisibilityToggled = pyqtSignal(str, bool, object, object)  # layer_name, is_visible
    layerLockRequested = pyqtSignal(str, bool, object, object)  # layer_name, is_locked
    addSegmentRequested = pyqtSignal(str)  # layer_name, is_add_segment

    def __init__(self, layer_name, layer_item, on_visibility_toggle, on_add_segment, on_lock_toggle, is_locked=False):
        super().__init__()
        self.layer_name = layer_name
        self.layer_item = layer_item
        self.on_visibility_toggle = on_visibility_toggle
        self.on_add_segment = on_add_segment
        self.on_lock_toggle = on_lock_toggle
        self.is_expanded = True
        self.is_locked = True
        self.selected = False

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)  # Increased padding for touch
        layout.setSpacing(12)  # Increased spacing

        # Toggle button - larger for touch
        self.toggle_btn = TouchButton("▼", size=(50, 50))  # Increased from 30x30
        self.toggle_btn.clicked.connect(self.toggle_expansion)
        self.toggle_btn.setStyleSheet("""
                TouchButton {
                    background-color: #f8f9fa;
                    color: #905BA9;
                    font-size: 18px;
                    font-weight: bold;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    min-width: 50px;
                    min-height: 50px;
                }
                TouchButton:hover {
                    background-color: #905BA9;
                    color: white;
                    border-color: #905BA9;
                }
                TouchButton:pressed {
                    background-color: #7a4d91;
                    border: 3px solid #7a4d91;
                }
            """)
        layout.addWidget(self.toggle_btn)

        # Layer icon and name - larger icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap(FOLDER_ICON).scaled(32, 32))  # Increased from 20x20
        self.icon_label.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(f" {self.layer_name}")
        self.text_label.setContentsMargins(0, 0, 0, 0)
        self.text_label.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: #343a40;
                    background: none;
                    padding: 8px 12px;
                    min-height: 30px;
                }
            """)
        layout.addWidget(self.text_label)
        layout.addStretch()

        # Layer actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)  # Increased spacing between action buttons

        # Add segment button - larger for touch
        add_segment_btn = TouchButton("➕", size=(50, 50))  # Increased from 30x30
        add_segment_btn.setToolTip("Add segment")
        add_segment_btn.clicked.connect(self._handle_add_segment)
        add_segment_btn.setStyleSheet("""
                TouchButton {
                    background-color: #f8f9fa;
                    color: #905BA9;
                    font-size: 18px;
                    font-weight: bold;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    min-width: 50px;
                    min-height: 50px;
                }
                TouchButton:hover {
                    background-color: #905BA9;
                    color: white;
                    border-color: #905BA9;
                }
                TouchButton:pressed {
                    background-color: #7a4d91;
                    border: 3px solid #7a4d91;
                }
            """)
        actions_layout.addWidget(add_segment_btn)

        # visibility toggle button - larger for touch
        self.visibility_btn = TouchButton("👁️", size=(50, 50))  # Increased from 30x30
        self.visibility_btn.setToolTip("Toggle visibility")
        self.visibility_btn.clicked.connect(self.toggleVisibility)
        self.visibility_btn.setStyleSheet("""
                       TouchButton {
                           background-color: #f8f9fa;
                           color: #905BA9;
                           font-size: 18px;
                           font-weight: bold;
                           border: 2px solid #e9ecef;
                           border-radius: 8px;
                           min-width: 50px;
                           min-height: 50px;
                       }
                       TouchButton:hover {
                           background-color: #905BA9;
                           color: white;
                           border-color: #905BA9;
                       }
                       TouchButton:pressed {
                           background-color: #7a4d91;
                           border: 3px solid #7a4d91;
                       }
                   """)
        layout.addWidget(self.visibility_btn)

        # Lock layer button - larger for touch
        self.lock_layer_btn = TouchButton("🔒", size=(50, 50))  # Increased from 30x30
        self.lock_layer_btn.setToolTip("Lock layer")
        self.lock_layer_btn.setStyleSheet("""
                              TouchButton {
                                    background-color: #f8f9fa;
                                    color: #6c757d;
                                    border: 2px solid #e9ecef;
                                    border-radius: 8px;
                                    font-weight: bold;
                                    font-size: 18px;
                                    min-width: 50px;
                                    min-height: 50px;
                                }
                                TouchButton:hover {
                                    background-color: #905BA9;
                                    color: white;
                                    border-color: #905BA9;
                                }
                                TouchButton:pressed {
                                    background-color: #7a4d91;
                                    border: 3px solid #7a4d91;
                                }
                            """)
        self.lock_layer_btn.clicked.connect(lambda: self.layer_lock_toggled())
        actions_layout.addWidget(self.lock_layer_btn)


        layout.addLayout(actions_layout)

        # Main widget styling - increased overall height
        self.setStyleSheet("""
                LayerHeaderItem {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 white, stop: 1 #f8f9fa);
                    border: 2px solid #e9ecef;
                    border-radius: 12px;
                    margin: 4px;
                    min-height: 70px;
                }
                LayerHeaderItem:hover {
                    border-color: #905BA9;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #fefefe, stop: 1 #f5f3f7);
                }
            """)


    def _handle_add_segment(self):
        if self.on_add_segment:
            self.on_add_segment()
        self.addSegmentRequested.emit(self.layer_name)
    def layer_lock_toggled(self):
        """Handle layer lock toggle"""
        print("Current lock state:", self.is_locked)
        self.is_locked = not self.is_locked

        def onSuccess():
            if self.is_locked:
                self.lock_layer_btn.setText("🔒")
                self.lock_layer_btn.setToolTip("Layer locked")
                print("Lock icon updated to locked")
            else:
                self.lock_layer_btn.setText("🔓")
                self.lock_layer_btn.setToolTip("Layer unlocked")
                print("Lock icon updated to locked")
            print("New lock state:", self.is_locked)
            if self.on_lock_toggle:
                self.on_lock_toggle(self.is_locked)

        def onFailure():
            print("Failed to toggle layer lock state")

        self.layerLockRequested.emit(self.layer_name, self.is_locked, onSuccess
                                     , onFailure)

    def toggleVisibility(self):
        """Toggle visibility of the segment"""
        self.is_visible = not getattr(self, 'is_visible', True)

        def onSuccess():
            if self.is_visible:
                self.visibility_btn.setText("👁️")
                self.visibility_btn.setToolTip("Layer visible")
            else:
                self.visibility_btn.setText("👁️‍🗨️")
                self.visibility_btn.setToolTip("Layer hidden")
            print(f"Layer '{self.layer_name}' visibility set to {self.is_visible}")

        def onFailure():
            print(f"Failed to toggle visibility for layer '{self.layer_name}'")

        self.visibility_btn.setText("👁️" if self.is_visible else "👁️‍🗨️")
        if self.on_visibility_toggle:
            self.on_visibility_toggle(self.is_visible)
        self.layerVisibilityToggled.emit(self.layer_name, self.is_visible, onSuccess, onFailure)

    def toggle_expansion(self):
        """Toggle the expansion state"""
        self.is_expanded = not self.is_expanded
        self.update_toggle_button()
        self.toggleRequested.emit(self.layer_name, self.is_expanded)

    def update_toggle_button(self):
        """Update the toggle button appearance"""
        if self.is_expanded:
            self.toggle_btn.setText("▼")
            self.toggle_btn.setToolTip("Collapse layer")
        else:
            self.toggle_btn.setText("▶")
            self.toggle_btn.setToolTip("Expand layer")

    # def toggle_selected(self):
    #     """Toggle selection state"""
    #     self.selected = not self.selected
    #     self.update_selection_style()
    #     self.selectedChanged.emit(self.layer_name, self.selected)

    def update_selection_style(self):
        """Update the selection button style based on state"""
        if self.selected:
            self.select_layer_btn.setStyleSheet("""
                    TouchButton {
                        background-color: #905BA9;
                        color: white;
                        border: 2px solid #905BA9;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 18px;
                        min-width: 50px;
                        min-height: 50px;
                    }
                    TouchButton:hover {
                        background-color: #7a4d91;
                        border-color: #7a4d91;
                    }
                    TouchButton:pressed {
                        background-color: #6b4280;
                        border: 3px solid #6b4280;
                    }
                """)
            self.select_layer_btn.setToolTip("Layer selected")
        else:
            self.select_layer_btn.setStyleSheet("""
                    TouchButton {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 2px solid #e9ecef;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 18px;
                        min-width: 50px;
                        min-height: 50px;
                    }
                    TouchButton:hover {
                        background-color: #905BA9;
                        color: white;
                        border-color: #905BA9;
                    }
                    TouchButton:pressed {
                        background-color: #7a4d91;
                        border: 3px solid #7a4d91;
                    }
                """)
            self.select_layer_btn.setToolTip("Select layer")

    def mark_layer_selected(self):
        """Mark the layer as selected"""
        self.selected = True
        self.update_selection_style()

    def mark_layer_unselected(self):
        """Mark the layer as unselected"""
        self.selected = False
        self.update_selection_style()

    def set_expanded(self, expanded):
        """Set expansion state programmatically"""
        if self.is_expanded != expanded:
            self.is_expanded = expanded
            self.update_toggle_button()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = LayerButtonsWidget("Test Layer", None, None, None, None)
    widget.show()
    sys.exit(app.exec())
