from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QCheckBox,
    QHBoxLayout, QVBoxLayout, QApplication, QLabel,
    QGroupBox, QGridLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
import sys
from pl_gui.controller.ButtonKey import ButtonKey
from pl_gui.controller.UserPermissionManager import UserPermissionManager
from API.shared.user.User import Role
from PyQt6.QtWidgets import QScroller
from PyQt6.QtCore import Qt
from pl_gui.customWidgets.SwitchButton import QToggle


class RolePermissionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)

        self.roles = [role.name for role in Role]
        self.permissions = [btn.value for btn in ButtonKey]

        # Group permissions by category (you can customize these groups)
        self.permission_groups = self.group_permissions()

        self.setup_ui()
        self.setup_styles()

        # Load saved permissions and update checkboxes accordingly
        saved_permissions = UserPermissionManager.get_permissions()
        self.loadPermissions(saved_permissions)

    def group_permissions(self):
        """Group permissions into logical categories"""
        # You can customize these groups based on your actual permissions
        groups = {
            "Core Features": [],
            "Administration": [],
            "Data Management": [],
            "User Management": [],
            "System": [],
            "Other": []
        }

        # Auto-categorize based on permission names (customize as needed)
        for permission in self.permissions:
            lower_perm = permission.lower()
            if any(word in lower_perm for word in ['admin', 'manage', 'config']):
                groups["Administration"].append(permission)
            elif any(word in lower_perm for word in ['user', 'role', 'permission']):
                groups["User Management"].append(permission)
            elif any(word in lower_perm for word in ['data', 'import', 'export', 'save', 'load']):
                groups["Data Management"].append(permission)
            elif any(word in lower_perm for word in ['system', 'setting', 'log']):
                groups["System"].append(permission)
            elif any(word in lower_perm for word in ['dashboard', 'start', 'main', 'home']):
                groups["Core Features"].append(permission)
            else:
                groups["Other"].append(permission)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Role Permissions")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Create role sections
        self.checkboxes = {}  # Store checkboxes for easy access

        for role in self.roles:
            role_frame = self.create_role_section(role)
            content_layout.addWidget(role_frame)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def create_role_section(self, role):
        """Create a section for each role with grouped permissions"""
        role_frame = QFrame()
        role_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        role_layout = QVBoxLayout(role_frame)

        # Role title
        role_label = QLabel(f"{role} Permissions")
        role_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #905BA9; margin: 5px;")
        role_layout.addWidget(role_label)

        # Create groups layout
        groups_layout = QHBoxLayout()

        for group_name, permissions in self.permission_groups.items():
            if not permissions:  # Skip empty groups
                continue

            group_box = QGroupBox(group_name)
            group_layout = QGridLayout(group_box)

            # Calculate columns based on number of permissions
            max_cols = min(3, len(permissions))  # Max 3 columns per group

            for i, permission in enumerate(permissions):
                row = i // max_cols
                col = i % max_cols

                # checkbox = QCheckBox(permission)
                checkbox = QToggle()
                checkbox.setText(permission)
                checkbox.setChecked(True)  # Default checked
                checkbox.stateChanged.connect(self.on_checkbox_state_changed)

                # Store checkbox reference
                if role not in self.checkboxes:
                    self.checkboxes[role] = {}
                self.checkboxes[role][permission] = checkbox

                group_layout.addWidget(checkbox, row, col)

            groups_layout.addWidget(group_box)

        role_layout.addLayout(groups_layout)

        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #d0d0d0; margin: 10px 0;")
        role_layout.addWidget(separator)

        return role_frame

    def setup_styles(self):
        """Apply custom styles to the widget"""
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }

            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }

            QLabel {
                color: black;
            }

            QScrollArea {
                border: none;
                background-color: white;
            }

            QScrollBar:vertical, QScrollBar:horizontal {
                background: #e0e0e0;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:hover {
                background: #a0a0a0;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #905BA9;
                font-size: 14px;
            }

            QCheckBox {
                spacing: 8px;
                padding: 4px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #905BA9;
            }

            QCheckBox::indicator:checked {
                background-color: #905BA9;
                border: 2px solid #905BA9;
            }

            QCheckBox::indicator:unchecked {
                background-color: white;
                border: 2px solid #ccc;
            }

            QCheckBox::indicator:hover {
                border: 2px solid #7A4D92;
            }

            QCheckBox:hover {
                color: #905BA9;
            }
        """)

    def on_checkbox_state_changed(self, state):
        """Handle checkbox state changes"""
        updated_permissions = {}

        for role in self.roles:
            permissions_for_role = []

            if role in self.checkboxes:
                for permission, checkbox in self.checkboxes[role].items():
                    if checkbox.isChecked():
                        permissions_for_role.append(permission)

            updated_permissions[role] = permissions_for_role

        # Save updated permissions
        UserPermissionManager.set_permissions(updated_permissions)
        print(f"[DEBUG] Permissions updated and saved: {updated_permissions}")

    def loadPermissions(self, permissions_dict):
        """Load permissions from saved data"""
        for role, allowed_permissions in permissions_dict.items():
            print(f"[DEBUG] Loading permissions for role '{role}': {allowed_permissions}")

            if role in self.checkboxes:
                for permission, checkbox in self.checkboxes[role].items():
                    checkbox.setChecked(permission in allowed_permissions)


# Alternative compact table version
class CompactRolePermissionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)

        self.roles = [role.name for role in Role]
        self.permissions = [btn.value for btn in ButtonKey]

        self.setup_ui()
        self.setup_styles()

        saved_permissions = UserPermissionManager.get_permissions()
        self.loadPermissions(saved_permissions)

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title
        label = QLabel("Role Permissions")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(label)

        # Create a more compact table with better column management
        self.table = QTableWidget()
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)
        QScroller.grabGesture(self.table.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        # Calculate optimal column width
        permissions_per_row = min(8, len(self.permissions))  # Max 8 permissions per row
        num_permission_rows = (len(self.permissions) + permissions_per_row - 1) // permissions_per_row

        self.table.setRowCount(len(self.roles) * num_permission_rows)
        self.table.setColumnCount(permissions_per_row + 1)  # +1 for role names

        # Set up headers for first row of permissions
        headers = ["Role"] + self.permissions[:permissions_per_row]
        self.table.setHorizontalHeaderLabels(headers)

        # Fill table with grouped permissions
        for role_idx, role in enumerate(self.roles):
            base_row = role_idx * num_permission_rows

            # Role name spans multiple rows if needed
            role_item = QTableWidgetItem(role)
            role_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(base_row, 0, role_item)

            if num_permission_rows > 1:
                self.table.setSpan(base_row, 0, num_permission_rows, 1)

            # Add permissions in rows
            for perm_row in range(num_permission_rows):
                actual_row = base_row + perm_row
                start_perm = perm_row * permissions_per_row
                end_perm = min(start_perm + permissions_per_row, len(self.permissions))

                for col_idx in range(1, permissions_per_row + 1):
                    perm_idx = start_perm + col_idx - 1
                    if perm_idx < len(self.permissions):
                        checkbox = QCheckBox()
                        checkbox.setChecked(True)
                        checkbox.stateChanged.connect(self.on_checkbox_state_changed)

                        cell_widget = QWidget()
                        cell_layout = QHBoxLayout(cell_widget)
                        cell_layout.addWidget(checkbox)
                        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        cell_layout.setContentsMargins(0, 0, 0, 0)

                        self.table.setCellWidget(actual_row, col_idx, cell_widget)
                    else:
                        # Empty cell for alignment
                        empty_item = QTableWidgetItem("")
                        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                        self.table.setItem(actual_row, col_idx, empty_item)

        # Set column headers for all permission rows
        for perm_row in range(num_permission_rows):
            start_perm = perm_row * permissions_per_row
            for col_idx in range(1, permissions_per_row + 1):
                perm_idx = start_perm + col_idx - 1
                if perm_idx < len(self.permissions):
                    header_text = self.permissions[perm_idx]
                    if perm_row > 0:  # Add row indicator for clarity
                        header_text = f"{header_text} (R{perm_row + 1})"
                    self.table.horizontalHeaderItem(col_idx).setText(header_text)

        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def setup_styles(self):
        """Apply styles similar to original"""
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }
            QLabel {
                color: black;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: black;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-size: 12px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f5f5f5;
                color: black;
            }
            QTableWidget::item:selected {
                background-color: #905BA9;
                color: white;
            }
        """)

    def on_checkbox_state_changed(self, state):
        # Similar to original implementation
        updated_permissions = {}
        permissions_per_row = min(8, len(self.permissions))
        num_permission_rows = (len(self.permissions) + permissions_per_row - 1) // permissions_per_row

        for role_idx, role in enumerate(self.roles):
            base_row = role_idx * num_permission_rows
            permissions_for_role = []

            for perm_row in range(num_permission_rows):
                actual_row = base_row + perm_row
                start_perm = perm_row * permissions_per_row

                for col_idx in range(1, permissions_per_row + 1):
                    perm_idx = start_perm + col_idx - 1
                    if perm_idx < len(self.permissions):
                        cell_widget = self.table.cellWidget(actual_row, col_idx)
                        if cell_widget:
                            checkbox = cell_widget.findChild(QCheckBox)
                            if checkbox and checkbox.isChecked():
                                permissions_for_role.append(self.permissions[perm_idx])

            updated_permissions[role] = permissions_for_role

        UserPermissionManager.set_permissions(updated_permissions)
        print("[DEBUG] Permissions updated and saved:", updated_permissions)

    def loadPermissions(self, permissions_dict):
        """Load permissions similar to original"""
        permissions_per_row = min(8, len(self.permissions))
        num_permission_rows = (len(self.permissions) + permissions_per_row - 1) // permissions_per_row

        for role_idx, role in enumerate(self.roles):
            base_row = role_idx * num_permission_rows
            allowed_permissions = permissions_dict.get(role, [])

            for perm_row in range(num_permission_rows):
                actual_row = base_row + perm_row
                start_perm = perm_row * permissions_per_row

                for col_idx in range(1, permissions_per_row + 1):
                    perm_idx = start_perm + col_idx - 1
                    if perm_idx < len(self.permissions):
                        cell_widget = self.table.cellWidget(actual_row, col_idx)
                        if cell_widget:
                            checkbox = cell_widget.findChild(QCheckBox)
                            if checkbox:
                                permission = self.permissions[perm_idx]
                                checkbox.setChecked(permission in allowed_permissions)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Use the grouped version (recommended)
    widget = RolePermissionsWidget()

    # Or use the compact table version
    # widget = CompactRolePermissionsWidget()

    widget.resize(1000, 600)
    widget.show()
    sys.exit(app.exec())