import os

from PyQt6.QtCore import Qt, QPointF, QSize
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QComboBox, QPushButton, QApplication, QHBoxLayout, QSizePolicy
)
from functools import partial
from PyQt6.QtGui import QIcon, QFont

from newCntEditot.contour_editor.SegmentSettingsWidget import SegmentSettingsWidget
from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from pl_gui.specific.enums.GlueType import GlueType
from newCntEditot.contour_editor.LayerButtonsWidget import LayerButtonsWidget
from newCntEditot.contour_editor.SegmentButtonsAndComboWidget import SegmentButtonsAndComboWidget
from PyQt6.QtWidgets import QApplication
import sys

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
BIN_ICON = os.path.join(RESOURCE_DIR, "BIN_BUTTON_SQUARE.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")
ACTIVE_ICON = os.path.join(RESOURCE_DIR, "active.png")
INACTIVE_ICON = os.path.join(RESOURCE_DIR, "inactive.png")
DROPDOWN_OPEN_ICON = os.path.join(RESOURCE_DIR,"dropdown_open.png")

class PointManagerWidget(QWidget):
    def __init__(self, contour_editor=None):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(8, 8, 8, 8)
        self.layout().setSpacing(4)
        self.setStyleSheet("""
            QWidget {
                font-size: 18px;
            }
            QPushButton {
                min-width: 64px;
                min-height: 64px;
                padding: 10px;
                border: None;
            }
            QComboBox {
                min-height: 40px;
                font-size: 18px;
            }
            QTreeWidget {
                outline: none;
                border: 1px solid #ccc;
                background-color: white;
            }
            QTreeWidget::item {
                height: 52px;
                padding: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #e6f3ff;
                border: 1px solid #007acc;
            }
            QTreeWidget::item:hover {
                background-color: #f0f8ff;
            }
        """)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        self.contour_editor = contour_editor
        if self.contour_editor:
            self.contour_editor.pointsUpdated.connect(self.refresh_points)

        self._setup_tree_widget()
        self.layout().addWidget(self.tree)

        self.layers = {}
        self.is_drag_mode = False

        self.initialize_tree_structure()

    def _setup_tree_widget(self):
        """Initialize and configure the tree widget"""
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([""])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIndentation(20)

        # Set initial column widths
        self.tree.setColumnWidth(0, 440)
        # self.tree.setColumnWidth(1, 320)

        # Connect signals
        self.tree.itemClicked.connect(self.highlight_selected_point)
        self.tree.itemChanged.connect(self.handle_segment_toggle)

    def initialize_tree_structure(self):
        """Initialize the tree structure with layer items"""
        self.tree.clear()
        self.layers = {}

        for name in ["External", "Contour", "Fill"]:
            layer_item = self._create_layer_item(name)
            self.tree.addTopLevelItem(layer_item)
            self.layers[name] = layer_item

            button_container = self._create_layer_button_container(name, layer_item)
            self.tree.setItemWidget(layer_item, 0, button_container)

        # Expand all layers by default
        for layer_item in self.layers.values():
            layer_item.setExpanded(True)

    def _create_layer_item(self, name):
        """Create a layer item with proper configuration"""
        layer_item = QTreeWidgetItem([""])
        layer_item.setFlags(layer_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        layer_item.setFont(0, QFont("Arial", 16, QFont.Weight.Bold))
        return layer_item

    def _create_layer_button_container(self, layer_name, layer_item):
        is_locked = self.contour_editor.manager.isLayerLocked(layer_name)

        widget = LayerButtonsWidget(
            layer_name=layer_name,
            layer_item=layer_item,
            on_visibility_toggle=lambda visible: self.set_layer_visibility(layer_name, visible),
            on_add_segment=self._make_add_segment(layer_name, layer_item),
            on_lock_toggle=self._make_layer_lock_toggle(layer_name),
            is_locked=is_locked
        )
        return widget

    def _make_layer_lock_toggle(self, layer_name):
        def toggle_lock(locked):
            if self.contour_editor:
                self.contour_editor.set_layer_locked(layer_name, locked)
                self.contour_editor.update()
            print(f"[ContourEditor] Set {layer_name} locked = {locked}")

        return toggle_lock


    def _make_add_segment(self, layer_name, layer_item):
        """Create an add segment function"""

        def add_segment():
            print(f"Adding new segment to {layer_name}")
            self.contour_editor.addNewSegment(layer_name)
            self.refresh_points()

            if layer_item:
                self.tree.expandItem(layer_item)

            # Force UI refresh
            self.tree.viewport().update()

        return add_segment

    def set_layer_visibility(self, layer_name, visible):
        """Set the visibility of a layer"""
        print(f"[ContourEditor] Set {layer_name} visibility to {visible}")
        self.contour_editor.set_layer_visibility(layer_name, visible)
        self.update()

    def get_current_selected_layer(self):
        """Get the currently selected layer name"""
        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if self.tree.currentItem() == top_item or top_item.isSelected():
                return top_item.text(0)
        return "External"

    def refresh_points(self):
        """Refresh the points display in the tree"""
        self.tree.blockSignals(True)
        try:
            if not self.contour_editor:
                return

            expanded_paths = self._save_expanded_state()
            selected_path = self._save_selected_path()
            # Remember the active segment index
            active_segment_index = getattr(self.contour_editor.manager, "active_segment_index", None)

            self._clear_layer_children()
            self._populate_segments()

            self._restore_expanded_state(expanded_paths)
            self._restore_selected_path(selected_path)
            # Restore the active segment UI
            if active_segment_index is not None:
                self.set_active_segment_ui(active_segment_index)
        finally:
            self.tree.blockSignals(False)

    def _save_expanded_state(self):
        """Save the current expanded state of tree items"""
        expanded_paths = set()

        def record_expansion(item, path=""):
            if item.isExpanded():
                expanded_paths.add(path)
            for i in range(item.childCount()):
                child = item.child(i)
                record_expansion(child, f"{path}/{child.text(0)}")

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            record_expansion(item, item.text(0))

        return expanded_paths

    def _save_selected_path(self):
        """Save the path to the currently selected item"""
        selected_item = self.tree.currentItem()
        if not selected_item:
            return None

        path = []
        node = selected_item
        while node:
            path.insert(0, node.text(0))
            node = node.parent()
        return "/".join(path)

    def _clear_layer_children(self):
        """Clear all children from layer items"""
        for layer_item in self.layers.values():
            layer_item.takeChildren()

    def _populate_segments(self):
        """Populate segments in the tree structure"""
        segments = self.contour_editor.manager.get_segments()
        print(f"Segments: {segments}")

        for seg_index, segment in enumerate(segments):
            layer = getattr(segment, "layer")
            if layer is None:
                continue

            print(f"Segment {seg_index}: Layer = {layer}")
            layer_name = layer.name

            parent_layer = self.layers.get(layer_name)

            # Create layer dynamically if it doesn't exist
            if not parent_layer:
                print(f"Warning: Layer '{layer_name}' not found, creating it.")
                parent_layer = self._create_layer_item(layer_name)
                self.layers[layer_name] = parent_layer
                self.tree.addTopLevelItem(parent_layer)

            # Create segment item
            seg_item = QTreeWidgetItem([f"S{seg_index}", ""])
            seg_item.setFlags(seg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            seg_item.setFont(0, QFont("Arial", 14))
            parent_layer.addChild(seg_item)

            # Create segment control widgets
            seg_container = self._create_segment_container(seg_item, seg_index, segment, layer_name)
            self.tree.setItemWidget(seg_item, 1, seg_container)

            # Add point children
            self._add_anchor_and_control_points(seg_item, segment)

        print("Segments populated.")

    def _create_segment_container(self, seg_item, seg_index, segment, layer_name):
        def on_visibility(btn):
            visible = btn.isChecked()
            btn.setIcon(QIcon(HIDE_ICON if visible else SHOW_ICON))
            self.contour_editor.manager.set_segment_visibility(seg_index, visible)
            self.contour_editor.update()

        def on_activate():
            self.set_active_segment_ui(seg_index)

        def on_delete():
            self.delete_segment(seg_index)

        def on_settings():
            self._on_settings_button_clicked(seg_index)

        def on_layer_change(new_layer_name):
            self.assign_segment_layer(seg_index, new_layer_name)

        return SegmentButtonsAndComboWidget(
            seg_index=seg_index,
            segment=segment,
            layer_name=layer_name,
            on_visibility=on_visibility,
            on_activate=on_activate,
            on_delete=on_delete,
            on_settings=on_settings,
            on_layer_change=on_layer_change
        )

    def _show_settings_dialog(self,seg_index, segment):
        # Prepare input keys for the settings widget
        inputKeys = [key.value for key in GlueSettingKey]
        if GlueSettingKey.GLUE_TYPE.value in inputKeys:
            inputKeys.remove(GlueSettingKey.GLUE_TYPE.value)

        inputKeys.append(RobotSettingKey.VELOCITY.value)
        inputKeys.append(RobotSettingKey.ACCELERATION.value)

        comboEnums = [[GlueSettingKey.GLUE_TYPE.value, GlueType]]

        # Create the settings widget
        from PyQt6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog()
        dialog.setWindowTitle(f"Segment {seg_index} Settings")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)

        widget = SegmentSettingsWidget(inputKeys + [GlueSettingKey.GLUE_TYPE.value], comboEnums, segment=segment,
                                       parent=dialog)
        layout = QVBoxLayout(dialog)
        layout.addWidget(widget)
        dialog.setLayout(layout)

        dialog.exec()  # This will keep the dialog open until closed explicitly

    def _on_settings_button_clicked(self, seg_index):
        segment = self.contour_editor.manager.get_segments()[seg_index]
        layer = getattr(segment, "layer", None)
        layer_name = layer.name if layer else "Unknown"
        print(f"Settings button clicked for segment {seg_index} (Layer: {layer_name})")
        self._show_settings_dialog(seg_index,segment)



    def _add_anchor_and_control_points(self, seg_item, segment):
        """Add anchor and control points as children of the segment item"""
        # Add anchor points
        for i, pt in enumerate(segment.points):
            coords = f"({pt.x():.1f}, {pt.y():.1f})" if isinstance(pt, QPointF) else "Invalid"
            pt_item = QTreeWidgetItem([f"P{i}", coords])
            pt_item.setFont(0, QFont("Arial", 12))
            pt_item.setForeground(0, QColor("#0066cc"))
            seg_item.addChild(pt_item)

        # Add control points
        for i, ctrl in enumerate(segment.controls):
            coords = f"({ctrl.x():.1f}, {ctrl.y():.1f})" if isinstance(ctrl, QPointF) else "Invalid"
            ctrl_item = QTreeWidgetItem([f"C{i}", coords])
            ctrl_item.setFont(0, QFont("Arial", 12))
            ctrl_item.setForeground(0, QColor("#cc6600"))
            seg_item.addChild(ctrl_item)

    def _restore_expanded_state(self, expanded_paths):
        """Restore the expanded state of tree items"""

        def restore_expansion(item, path=""):
            if path in expanded_paths:
                item.setExpanded(True)
            for i in range(item.childCount()):
                child = item.child(i)
                restore_expansion(child, f"{path}/{child.text(0)}")

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            restore_expansion(item, item.text(0))

    def _restore_selected_path(self, selected_path):
        """Restore the selected item based on saved path"""
        if not selected_path:
            return

        def find_item_by_path(root, path_parts):
            if not path_parts:
                return root
            for i in range(root.childCount()):
                child = root.child(i)
                if child.text(0) == path_parts[0]:
                    return find_item_by_path(child, path_parts[1:])
            return None

        path_parts = selected_path.split("/")
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) == path_parts[0]:
                target = find_item_by_path(item, path_parts[1:])
                if target:
                    self.tree.setCurrentItem(target)
                    break

    def set_active_segment_ui(self, seg_index):
        """Update UI to reflect the active segment"""
        self.contour_editor.manager.set_active_segment(seg_index)
        print(f"[DEBUG] Set active segment to {seg_index}")

        # Update all segment active buttons
        for i in range(self.tree.topLevelItemCount()):
            layer_item = self.tree.topLevelItem(i)
            for j in range(layer_item.childCount()):
                seg_item = layer_item.child(j)
                is_active = seg_item.text(0) == f"S{seg_index}"

                container = self.tree.itemWidget(seg_item, 1)
                if container:
                    buttons = container.findChildren(QPushButton)
                    for btn in buttons:
                        if btn.toolTip() == "Set as active segment":
                            print("setting active button for segment", seg_index)
                            btn.setIcon(QIcon(ACTIVE_ICON if is_active else INACTIVE_ICON))

        self.tree.viewport().update()
        self.contour_editor.update()

    def delete_segment(self, seg_index):
        """Delete a segment"""
        if self.contour_editor:
            print(f"Deleting segment {seg_index}")
            self.contour_editor.manager.delete_segment(seg_index)
            self.contour_editor.update()
            self.refresh_points()

    def assign_segment_layer(self, seg_index, layer_name):
        """Assign a segment to a different layer"""
        print(f"Assigning Segment {seg_index} to layer '{layer_name}'")
        if self.contour_editor:
            self.contour_editor.manager.assign_segment_layer(seg_index, layer_name)
            self.refresh_points()
            self.contour_editor.update()

    def handle_segment_toggle(self, item, column):
        """Handle segment toggle events"""
        if not self.contour_editor:
            return

        # Layer visibility toggle
        if item.parent() is None and column == 0:
            layer_name = item.text(0)
            visible = item.checkState(0) == Qt.CheckState.Checked
            self.set_layer_visibility(layer_name, visible)
            self.contour_editor.update()
            return

        # Segment visibility toggle
        if item.parent() and column == 0:
            seg_text = item.text(0)
            if seg_text.startswith("S"):
                try:
                    seg_index = int(seg_text[1:])
                    visible = item.checkState(0) == Qt.CheckState.Checked
                    self.contour_editor.manager.set_segment_visibility(seg_index, visible)
                    self.contour_editor.update()
                except Exception as e:
                    print(f"[Error] segment visibility toggle: {e}")
                return

        # Segment activation toggle
        if item.parent() and column == 2:
            seg_text = item.text(0)
            if seg_text.startswith("S"):
                try:
                    seg_index = int(seg_text[1:])
                    self.tree.blockSignals(True)
                    self.set_active_segment_ui(seg_index)
                    self.tree.blockSignals(False)
                except Exception as e:
                    print(f"[Error] handle_segment_toggle: {e}")

    def highlight_selected_point(self, item):
        """Handle point selection and highlighting"""
        if not item or not self.contour_editor:
            print("No item selected.")
            return

        print(f"Item clicked: {item.text(0)}")

        try:
            # Handle segment selection
            if item.text(0).startswith("S"):
                seg_index = int(item.text(0)[1:])
                self.tree.blockSignals(True)
                self.set_active_segment_ui(seg_index)
                self.tree.blockSignals(False)
                return

            # Handle point selection
            parent = item.parent()
            if parent and parent.text(0).startswith("S"):
                seg_index = int(parent.text(0)[1:])
                label = item.text(0)

                if label.startswith("P"):
                    idx = int(label[1:])
                    self.contour_editor.selected_point_info = ('anchor', seg_index, idx)
                elif label.startswith("C"):
                    idx = int(label[1:])
                    self.contour_editor.selected_point_info = ('control', seg_index, idx)

                self.tree.blockSignals(True)
                self.set_active_segment_ui(seg_index)
                self.tree.blockSignals(False)

        except Exception as e:
            print(f"Selection error: {e}")


if __name__ == "__main__":
    import sys
    from unittest.mock import MagicMock

    app = QApplication(sys.argv)
    mock_contour_editor = MagicMock()
    mock_manager = MagicMock()
    mock_contour_editor.manager = mock_manager
    widget = PointManagerWidget(contour_editor=mock_contour_editor)
    widget.show()
    sys.exit(app.exec())
