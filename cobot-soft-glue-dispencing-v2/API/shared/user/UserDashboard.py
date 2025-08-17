import sys
import qrcode
import os
from PyQt6.QtGui import QPixmap

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QComboBox, QLabel,
                             QDialog, QFormLayout, QMessageBox, QHeaderView,
                             QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from enum import Enum
import pandas as pd

# Import your existing classes (adjust paths as needed)
from API.shared.user.User import User, Role, UserField
from API.shared.user.UserService import UserService
from API.shared.user.CSVUsersRepository import CSVUsersRepository
from API.localization.LanguageResourceLoader import LanguageResourceLoader
from API.localization.enums.Message import Message
from API.localization.enums.Language import Language
from pl_gui.ToastWidget import ToastWidget


class UserTableModel:
    """Model to handle user data for the table"""

    def __init__(self, users=None):
        self.langLoader = LanguageResourceLoader()
        self.users = users or []
        self.headers = ["ID", "First Name", "Last Name", "Password", "Role"]

    def get_user_data(self, user):
        """Convert user object to list for table display"""
        try:
            # # Debug: Print user attributes
            # print(f"User object: {user}")
            # print(f"User type: {type(user)}")
            # print(f"User id: {getattr(user, 'id', 'NO ID')}")
            # print(f"User firstName: {getattr(user, 'firstName', 'NO FIRSTNAME')}")
            # print(f"User lastName: {getattr(user, 'lastName', 'NO LASTNAME')}")
            # print(f"User password: {getattr(user, 'password', 'NO PASSWORD')}")
            # print(f"User role: {getattr(user, 'role', 'NO ROLE')}")

            # role_display = "Unknown"
            role_display = self.langLoader.get_message(Message.UNKNOWN)
            if hasattr(user, 'role'):
                if hasattr(user.role, 'value'):
                    role_display = user.role.value
                else:
                    role_display = str(user.role)

            data = [
                str(getattr(user, 'id', '')),
                str(getattr(user, 'firstName', '')),
                str(getattr(user, 'lastName', '')),
                "****",  # Hide password for security
                role_display
            ]
            # print(f"Converted user data: {data}")
            return data
        except Exception as e:
            # print(f"Error in get_user_data: {e}")
            return ["Error", "Error", "Error", "Error", "Error"]

    def update_users(self, users):
        """Update the user list"""
        self.users = users


class UserDialog(QDialog):
    """Dialog for adding/editing users"""

    # def __init__(self, parent=None, user=None, title="Add User"):
    def __init__(self, parent=None, user=None, title=""):
        super().__init__(parent)
        self.langLoader = LanguageResourceLoader()
        self.user = user
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setup_ui()

        if user:
            self.populate_fields()

    def setup_ui(self):
        layout = QFormLayout()

        self.id_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        for role in Role:
            self.role_combo.addItem(role.value, role)

        # UserDialog setup_ui
        layout.addRow(self.langLoader.get_message(Message.ID) + ":", self.id_edit)
        layout.addRow(self.langLoader.get_message(Message.FIRST_NAME) + ":", self.first_name_edit)
        layout.addRow(self.langLoader.get_message(Message.LAST_NAME) + ":", self.last_name_edit)
        layout.addRow(self.langLoader.get_message(Message.PASSWORD) + ":", self.password_edit)
        layout.addRow(self.langLoader.get_message(Message.ROLE) + ":", self.role_combo)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.langLoader.get_message(Message.SAVE))
        self.cancel_button = QPushButton(self.langLoader.get_message(Message.CANCEL))

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)

        self.setLayout(layout)

        # Connect signals
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def update_language(self):
        """Update headers to current language"""
        self.headers = [
            self.langLoader.get_message(Message.ID),
            self.langLoader.get_message(Message.FIRST_NAME),
            self.langLoader.get_message(Message.LAST_NAME),
            self.langLoader.get_message(Message.PASSWORD),
            self.langLoader.get_message(Message.ROLE),
        ]

    def populate_fields(self):
        """Populate fields when editing existing user"""
        if self.user:
            self.id_edit.setText(str(self.user.id))
            self.id_edit.setReadOnly(True)  # Don't allow ID changes
            self.first_name_edit.setText(self.user.firstName)
            self.last_name_edit.setText(self.user.lastName)
            self.password_edit.setText(self.user.password)

            # Set role combo
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == self.user.role:
                    self.role_combo.setCurrentIndex(i)
                    break

    def get_user_data(self):
        """Get user data from form"""
        try:
            user_id = int(self.id_edit.text().strip())
        except ValueError:
            raise ValueError("ID must be a valid number")

        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentData()

        if not all([first_name, last_name, password]):
            raise ValueError("All fields are required")

        return {
            'id': user_id,
            'firstName': first_name,
            'lastName': last_name,
            'password': password,
            'role': role
        }

    def update_language(self):
        """Update all UI texts to current language"""
        self.id_label.setText(self.langLoader.get_message(Message.ID) + ":")
        self.first_name_label.setText(self.langLoader.get_message(Message.FIRST_NAME) + ":")
        self.last_name_label.setText(self.langLoader.get_message(Message.LAST_NAME) + ":")
        self.password_label.setText(self.langLoader.get_message(Message.PASSWORD) + ":")
        self.role_label.setText(self.langLoader.get_message(Message.ROLE) + ":")

        self.save_button.setText(self.langLoader.get_message(Message.SAVE))
        self.cancel_button.setText(self.langLoader.get_message(Message.CANCEL))


class UserManagementWidget(QWidget):
    """Main widget for user management"""

    def __init__(self, csv_file_path="users.csv"):
        super().__init__()
        self.langLoader = LanguageResourceLoader(Language.BULGARIAN)
        self.csv_file_path = csv_file_path
        self.setup_service()
        self.setup_ui()
        self.load_users()
        self.setup_styles()

    def setup_service(self):
        """Initialize the user service and repository"""
        user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME,
                       UserField.PASSWORD, UserField.ROLE]
        self.repository = CSVUsersRepository(self.csv_file_path, user_fields, User)
        self.service = UserService(self.repository)
        self.model = UserTableModel()

    def setup_ui(self):
        """Setup the user interface"""
        self.main_layout = QVBoxLayout()

        # Title
        self.title_label = QLabel(self.langLoader.get_message(Message.USER_MANAGEMENT))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        self.main_layout.addWidget(self.title_label)

        # Filter section
        self.filter_group = QGroupBox()
        self.filter_group.setTitle(self.langLoader.get_message(Message.FILTER_USERS))
        self.filter_layout = QHBoxLayout()

        self.filter_layout.addWidget(QLabel(self.langLoader.get_message(Message.FILTER_BY) + ":"))
        self.filter_column_combo = QComboBox()
        self.filter_column_combo.addItems([
            self.langLoader.get_message(Message.ALL),
            self.langLoader.get_message(Message.ID),
            self.langLoader.get_message(Message.FIRST_NAME),
            self.langLoader.get_message(Message.LAST_NAME),
            self.langLoader.get_message(Message.ROLE),
        ])
        self.filter_layout.addWidget(self.filter_column_combo)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(self.langLoader.get_message(Message.ENTER_FILTER_VALUE))
        self.filter_layout.addWidget(self.filter_input)

        self.filter_button = QPushButton()
        self.clear_filter_button = QPushButton()

        self.filter_button.setText(self.langLoader.get_message(Message.APPLY_FILTERS))
        self.clear_filter_button.setText(self.langLoader.get_message(Message.CLEAR_FILTERS))
        self.filter_layout.addWidget(self.filter_button)
        self.filter_layout.addWidget(self.clear_filter_button)

        self.filter_group.setLayout(self.filter_layout)
        self.main_layout.addWidget(self.filter_group)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Password", "Role"])

        # Make table look better and ensure visibility
        self.header = self.table.horizontalHeader()
        self.header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(True)

        # Set minimum size to ensure table is visible
        self.table.setMinimumHeight(200)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_layout.addWidget(self.table)

        # Buttons
        self.button_group = QGroupBox("")
        self.button_layout = QHBoxLayout()

        self.add_button = QPushButton()
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()
        self.refresh_button = QPushButton()
        self.test_button = QPushButton()

        self.add_button.setText(self.langLoader.get_message(Message.ADD_USER))
        self.edit_button.setText(self.langLoader.get_message(Message.EDIT_USER))
        self.delete_button.setText(self.langLoader.get_message(Message.DELETE_USER))
        self.refresh_button.setText(self.langLoader.get_message(Message.REFRESH))
        self.test_button.setText(self.langLoader.get_message(Message.GENERATE_QR))

        # Style buttons
        self.buttons = [self.add_button, self.edit_button, self.delete_button, self.refresh_button]
        for button in self.buttons:
            button.setMinimumHeight(35)
            self.button_layout.addWidget(button)

        self.button_group.setLayout(self.button_layout)
        self.main_layout.addWidget(self.button_group)

        # Status label
        self.status_label = QLabel()

        self.status_label.setText(self.langLoader.get_message(Message.READY))
        self.main_layout.addWidget(self.status_label)

        self.setLayout(self.main_layout)

        # Connect signals
        self.add_button.clicked.connect(self.add_user)
        self.edit_button.clicked.connect(self.edit_user)
        self.delete_button.clicked.connect(self.delete_user)
        self.refresh_button.clicked.connect(self.load_users)
        self.filter_button.clicked.connect(self.apply_filter)
        self.clear_filter_button.clicked.connect(self.clear_filter)
        self.filter_input.returnPressed.connect(self.apply_filter)

        # Enable/disable edit and delete buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # Add test button for debugging (remove in production)
        self.test_button = QPushButton("Generate QR")
        self.test_button.clicked.connect(self.generateQrCode)
        self.button_layout.addWidget(self.test_button)

        # Initially disable edit and delete buttons
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def setup_styles(self):
        """Apply custom styles to the widget"""
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
            }

            QScrollBar:vertical, QScrollBar:horizontal {
                background: #e0e0e0;
            }

            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c0c0c0;
            }

            QScrollBar::add-line, QScrollBar::sub-line {
                background: #d0d0d0;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }

            QPushButton {
                background-color: #905BA9;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #7A4D92;
            }

            QPushButton:pressed {
                background-color: #644080;
            }

            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
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

            QLineEdit, QComboBox {
                background-color: white;
                color: black;
            }
        """)

    def load_users(self):
        """Load users from the repository and display in table"""
        try:
            users = self.repository.get_all()
            # print(f"Loaded {len(users)} users from repository")  # Debug
            for i, user in enumerate(users):
                print(f"User {i}: {user}")  # Debug

            self.model.update_users(users)
            self.populate_table(users)
            self.status_label.setText(f"Loaded {len(users)} users")
        except Exception as e:
            # print(f"Exception in load_users: {e}")  # Debug
            self.show_error(self.langLoader.get_message(Message.ERROR_LOADING_USERS))
            self.status_label.setText("Error loading users")

    def populate_table(self, users):
        """Populate the table with user data"""
        # print(f"Populating table with {len(users)} users")  # Debug

        # Clear the table first
        self.table.clearContents()
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            try:
                # print(f"Processing user {row}: {user}")  # Debug
                user_data = self.model.get_user_data(user)
                # print(f"User data for row {row}: {user_data}")  # Debug

                for col, data in enumerate(user_data):
                    item = QTableWidgetItem(str(data))
                    item.setData(Qt.ItemDataRole.UserRole, user)  # Store user object
                    # Set item flags to make it selectable and enabled
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.table.setItem(row, col, item)
                    # print(f"Set item at ({row}, {col}): {data}")  # Debug
            except Exception as e:
                print(f"Error processing user {row}: {e}")  # Debug
                continue

        # Force table refresh
        self.table.viewport().update()
        self.table.repaint()

        # print(f"Table now has {self.table.rowCount()} rows")  # Debug

        # Check if items are actually there
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    print(f"Verification - Item at ({row}, {col}): {item.text()}")
                else:
                    print(f"Verification - No item at ({row}, {col})")

    def add_user(self):
        """Add a new user"""
        dialog = UserDialog(self, title=self.langLoader.get_message(Message.ADD_NEW_USER))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                user_data = dialog.get_user_data()
                new_user = User(**user_data)

                if self.service.addUser(new_user):
                    self.load_users()
                    self.status_label.setText(f"{new_user.firstName} {self.langLoader.get_message(Message.ADDED_SUCCESSFULLY)}")
                else:
                    self.show_error(self.langLoader.get_message(Message.USER_ALREADY_EXISTS))
            except Exception as e:
                self.show_error(f"{self.langLoader.get_message(Message.ERROR_ADDING_USER)}: {str(e)}")
    def edit_user(self):
        """Edit selected user"""
        current_row = self.table.currentRow()
        if current_row < 0:
            # self.show_error(self.langLoader.get_message(Message.PLEASE_SELECT_USER_TO_EDIT))

            toast = ToastWidget(self,self.langLoader.get_message(Message.PLEASE_SELECT_USER_TO_EDIT),5)
            toast.show()
            return

        user = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = UserDialog(self, user, "Edit User")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                user_data = dialog.get_user_data()
                updated_user = User(**user_data)
                # Update using repository (you might need to implement update method)
                self.repository.update([updated_user])
                self.load_users()
                self.status_label.setText(f"User {updated_user.firstName} updated successfully")
            except Exception as e:
                print(f"Exception in edit_user: {e}")  # Debug
                self.show_error(f"Error updating user: {str(e)}")

    def delete_user(self):
        """Delete selected user"""
        current_row = self.table.currentRow()
        if current_row < 0:
            toast = ToastWidget(self, self.langLoader.get_message(Message.PLEASE_SELECT_USER_TO_DELETE), 5)
            toast.show()
            return

        user = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{user.firstName} {user.lastName}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repository.delete(user.id)
                self.load_users()
                self.status_label.setText(f"User {user.firstName} deleted successfully")
            except Exception as e:
                self.show_error(f"Error deleting user: {str(e)}")

    def apply_filter(self):
        """Apply filter to the table"""
        filter_column = self.filter_column_combo.currentText()
        filter_value = self.filter_input.text().strip().lower()

        if not filter_value or filter_column == "All":
            self.load_users()
            return

        try:
            all_users = self.repository.get_all()
            filtered_users = []

            for user in all_users:
                should_include = False

                if filter_column == "ID":
                    should_include = filter_value in str(user.id).lower()
                elif filter_column == "First Name":
                    should_include = filter_value in user.firstName.lower()
                elif filter_column == "Last Name":
                    should_include = filter_value in user.lastName.lower()
                elif filter_column == "Role":
                    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
                    should_include = filter_value in role_value.lower()

                if should_include:
                    filtered_users.append(user)

            self.populate_table(filtered_users)
            self.status_label.setText(f"Filter applied: {len(filtered_users)} users found")

        except Exception as e:
            self.show_error(f"Error applying filter: {str(e)}")

    def clear_filter(self):
        """Clear the filter and show all users"""
        self.filter_input.clear()
        self.filter_column_combo.setCurrentIndex(0)
        self.load_users()

    def on_selection_changed(self):
        """Handle table selection changes"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def show_error(self, message):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        """Show info message dialog"""
        QMessageBox.information(self, "Information", message)

    def generateQrCode(self):
        """Generate a QR code with user ID and password"""
        current_row = self.table.currentRow()
        if current_row < 0:
            toast = ToastWidget(self, self.langLoader.get_message(Message.PLEASE_SELECT_USER_TO_GENERATE_QR_CODE) , 5)
            toast.show()
            return

        user_item = self.table.item(current_row, 0)
        user = user_item.data(Qt.ItemDataRole.UserRole)

        # Format QR content as requested
        qr_data = f"id = {user.id}\npassword = {user.password}"

        # Generate the QR code image
        qr = qrcode.make(qr_data)

        # Save temporarily to file
        temp_path = "temp_qr.png"
        qr.save(temp_path)

        # Load into QPixmap
        pixmap = QPixmap(temp_path)

        # Show in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("QR Code")
        layout = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec()

        # Optional: remove temp file after use
        os.remove(temp_path)

    def update_language(self,message):
        """Update all UI texts when language changes."""
        self.title_label.setText(self.langLoader.get_message(Message.USER_MANAGEMENT))

        # Update static labels
        self.filter_column_combo.clear()
        self.filter_column_combo.addItems([
            self.langLoader.get_message(Message.ALL),
            self.langLoader.get_message(Message.ID),
            self.langLoader.get_message(Message.FIRST_NAME),
            self.langLoader.get_message(Message.LAST_NAME),
            self.langLoader.get_message(Message.ROLE),
        ])

        # Update buttons
        self.filter_button.setText(self.langLoader.get_message(Message.APPLY_FILTERS))
        self.clear_filter_button.setText(self.langLoader.get_message(Message.CLEAR_FILTERS))

        self.add_button.setText(self.langLoader.get_message(Message.ADD_USER))
        self.edit_button.setText(self.langLoader.get_message(Message.EDIT_USER))
        self.delete_button.setText(self.langLoader.get_message(Message.DELETE_USER))
        self.refresh_button.setText(self.langLoader.get_message(Message.REFRESH))
        self.test_button.setText(self.langLoader.get_message(Message.GENERATE_QR))

        # Update group box titles and labels
        # Assuming you saved references to these in __init__ or setup_ui, e.g.:
        # self.filter_group.setTitle(...)
        # For now, let's assume you store them as attributes
        self.filter_group.setTitle(self.langLoader.get_message(Message.FILTER_USERS))
        self.status_label.setText(self.langLoader.get_message(Message.READY))

        # Update table headers
        self.table.setHorizontalHeaderLabels([
            self.langLoader.get_message(Message.ID),
            self.langLoader.get_message(Message.FIRST_NAME),
            self.langLoader.get_message(Message.LAST_NAME),
            self.langLoader.get_message(Message.PASSWORD),
            self.langLoader.get_message(Message.ROLE),
        ])

        # If you have any placeholders or other labels, update those too
        self.filter_input.setPlaceholderText(self.langLoader.get_message(Message.ENTER_FILTER_VALUE))


class UserManagementWindow(QMainWindow):
    """Main window containing the user management widget"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Management")
        self.setGeometry(100, 100, 800, 600)

        # Create and set central widget
        self.user_widget = UserManagementWidget()
        self.setCentralWidget(self.user_widget)


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set a light palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("white"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Base, QColor("white"))  # Text entry fields, combo boxes
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f5f5f5"))  # Alternating table rows
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Text, QColor("black"))
    palette.setColor(QPalette.ColorRole.Button, QColor("white"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("black"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#905BA9"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))

    # Apply the palette!
    app.setPalette(palette)

    window = UserManagementWindow()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()