import os
import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGridLayout, QSizePolicy,
                             QStackedWidget)
from PyQt6.QtCore import Qt

from API.shared.settings.conreateSettings.CameraSettings import CameraSettings
from API.shared.settings.conreateSettings.RobotSettings import RobotSettings
from API.shared.user.CSVUsersRepository import CSVUsersRepository
from API.shared.user.Session import SessionManager
from API.shared.user.User import UserField, User
from API.shared.user.UserService import UserService
from pl_gui.main_application.helpers.Endpoints import *
from pl_gui.main_application.login.LoginWindow import LoginWindow
from pl_gui.main_application.Folder import Folder
from pl_gui.main_application.appWidgets.AppWidget import AppWidget
from pl_gui.main_application.appWidgets.ContourEditorAppWidget import ContourEditorAppWidget
from pl_gui.main_application.appWidgets.Dashboard import DashboardAppWidget
from pl_gui.main_application.appWidgets.SettingsAppWidget import SettingsAppWidget
from pl_gui.main_application.appWidgets.UserManagementAppWidget import UserManagementAppWidget
from pl_gui.main_application.appWidgets.GalleryAppWidget import GalleryAppWidget
from pl_gui.main_application.appWidgets.CreateWorkpieceOptionsAppWidget import CreateWorkpieceOptionsAppWidget

from pl_gui.Header import Header
from pl_gui.main_application.controller.CreateWorkpieceManager import CreateWorkpieceManager




# Resource paths
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
PLACEHOLDER_ICON = os.path.join(RESOURCES_DIR, "placeholder_icon.png")
BACKGROUND_IMAGE = os.path.join(RESOURCES_DIR, "background.png")
# work icons
START_ICON = os.path.join(RESOURCES_DIR, "work/RUN_BUTTON.png")
GALLERY_ICON = os.path.join(RESOURCES_DIR, "work/LIBRARY_BUTTON_SQARE.png")
CREATE_WORKPIECE_ICON = os.path.join(RESOURCES_DIR, "work/CREATE_WORKPIECE_BUTTON_SQUARE.png")
DASHBOARD_ICON = os.path.join(RESOURCES_DIR, "work/dashboard.png")


# service icons
SERVICE_ICON = os.path.join(RESOURCES_DIR, "service/SETTINGS_BUTTON.png")
SETTINGS_ICON = os.path.join(RESOURCES_DIR, "service/SETTINGS_BUTTON.png")
CALIBRATION_ICON = os.path.join(RESOURCES_DIR, "service/CALIBRATION_BUTTON_SQUARE.png")

# administration icons
USER_MANAGEMENT_ICON = os.path.join(RESOURCES_DIR, "administration/user_management.png")




class ApplicationDemo(QWidget):
    """Demo application showing the Android folder widget with QStackedWidget for app management"""

    def __init__(self,controller):
        super().__init__()
        self.controller= controller
        self.folders = []  # Keep track of all folders
        self.current_running_app = None  # Track currently running app
        self.current_app_folder = None  # Track which folder has the running app
        self.stacked_widget = None  # The main stacked widget
        self.folder_page = None  # The main folder page widget
        self.setup_ui()


    def on_folder_opened(self, opened_folder):
        """Handle when a folder is opened - gray out other folders"""
        for folder in self.folders:
            if folder != opened_folder:
                folder.set_grayed_out(True)

    def on_folder_closed(self):
        """Handle when a folder is closed - restore all folders"""
        print("Demo: Folder closed - restoring all folders")
        # Reset the current app state
        self.current_running_app = None
        self.current_app_folder = None

        # Restore all folders
        for folder in self.folders:
            folder.set_grayed_out(False)

    def on_app_selected(self, app_name):
        """Handle when an app is selected from any folder"""
        print(f"Demo: App selected - {app_name}")

        # Find which folder emitted this signal
        sender_folder = self.sender()

        # Store the running app info
        self.current_running_app = app_name
        self.current_app_folder = sender_folder

        # Show the appropriate app
        self.show_app(app_name)

    def on_back_button_pressed(self):
        """Handle when the back button is pressed in the sidebar"""
        print("Demo: Back button signal received - closing app and returning to main")
        self.close_current_app()

    def show_app(self, app_name):
        """Show the specified app in the stacked widget"""
        # Create the appropriate app widget
        if app_name == "User Management":
            app_widget = UserManagementAppWidget()
        elif app_name == "Settings":
            app_widget = SettingsAppWidget(controller = self.controller)
            # app_widget = AppWidget(app_name)
        elif app_name == "Create Workpiece Options":
            app_widget = CreateWorkpieceOptionsAppWidget(controller=self.controller)
            app_widget.create_workpiece_camera_selected.connect(self.create_workpiece_via_camera_selected)
            app_widget.create_workpiece_dxf_selected.connect(self.create_workpiece_via_dxf_selected)
        elif app_name == "Contour Editor":
            app_widget = ContourEditorAppWidget(parent = self,controller=self.controller)
            # app_widget = AppWidget(app_name)
        elif app_name == "Start":
            app_widget = DashboardAppWidget(controller=self.controller)
            app_widget.start_requested.connect(lambda: self.controller.handle(START))
            app_widget.LOGOUT_REQUEST.connect(self.onLogout)
        elif app_name == "Gallery":
            app_widget = GalleryAppWidget(controller=self.controller)
        elif app_name == "Calibrate":
            pass
            # from pl_gui.calibration.CalibrationAppWidget import CalibrationAppWidget
            # app_widget = CalibrationAppWidget(controller=self.controller)
        elif app_name == "DXF Browser":
            from pl_gui.gallery.DxfThumbnailLoader import DXFThumbnailLoader
            from pl_gui.settings.Paths import DXF_DIRECTORY
            loader = DXFThumbnailLoader(DXF_DIRECTORY)
            thumbnails = loader.run()

            app_widget = GalleryAppWidget(controller=self.controller,onApplyCallback=self.onDxfBrowserSubmit,thumbnails= thumbnails)
        else:
            app_widget = AppWidget(app_name)

        # Connect the app's close signal
        app_widget.app_closed.connect(self.close_current_app)

        # Only hide the overlay if the sidebar drawer is not active
        sidebar_active = False
        expanded_view = getattr(self.current_app_folder, "expanded_view", None)
        if expanded_view and getattr(expanded_view, "sidebar_drawer", None):
            sidebar_active = expanded_view.sidebar_drawer.isVisible()
        if not sidebar_active and self.current_app_folder and self.current_app_folder.overlay:
            self.current_app_folder.overlay.hide()

        # Add the app widget to the stacked widget (index 1)
        if self.stacked_widget.count() > 1:
            # Remove existing app widget
            old_app = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(old_app)
            old_app.deleteLater()

        self.stacked_widget.addWidget(app_widget)

        # Switch to the app view (index 1)
        self.stacked_widget.setCurrentIndex(1)

        print(f"App '{app_name}' is now running. Press ESC to close or click the back button.")
        return app_widget

    def close_current_app(self):
        """Close the currently running app and restore the folder interface"""
        if self.current_running_app:
            print(f"Demo: Closing app - {self.current_running_app}")

            # Switch back to the folder view (index 0)
            self.stacked_widget.setCurrentIndex(0)

            # Remove the app widget
            if self.stacked_widget.count() > 1:
                app_widget = self.stacked_widget.widget(1)
                self.stacked_widget.removeWidget(app_widget)
                app_widget.deleteLater()

            # Close the app in the folder if needed
            if self.current_app_folder:
                self.current_app_folder.close_app()

            # Clear the running app info
            self.current_running_app = None
            self.current_app_folder = None

            # Restore all folders
            for folder in self.folders:
                folder.set_grayed_out(False)

    def setup_ui(self):
        self.setWindowTitle("Android-Style App Folder Demo with QStackedWidget")

        # Set reasonable window size instead of maximized
        self.resize(1200, 800)  # Reasonable default size

        # Center the window on screen
        self.center_on_screen()

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(248, 250, 252, 1),
                    stop:1 rgba(241, 245, 249, 1));
            }
        """)

        # Create main layout for the window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.header = Header(
            screen_width=self.width(),
            screen_height=self.height(),
            toggle_menu_callback=None,
            dashboard_button_callback=None
        )
        self.header.menu_button.hide()
        self.header.dashboardButton.hide()
        main_layout.addWidget(self.header)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create the folder page (index 0)
        self.create_folder_page()

    def create_folder_page(self):
        """Create the main folder page widget"""
        self.folder_page = QWidget()

        # Main container widget with size constraints
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Use a main layout to center the container
        page_layout = QVBoxLayout(self.folder_page)
        page_layout.setContentsMargins(40, 40, 40, 40)
        page_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)

        # Grid layout for folders with controlled spacing
        layout = QGridLayout(container)
        layout.setSpacing(30)  # Reasonable spacing between folders
        layout.setContentsMargins(0, 0, 0, 0)

        # Create 6 folders in a 3x2 grid
        workFolder = Folder("Work")
        workButtons = [
            ("Start", DASHBOARD_ICON, self.onStartPressed),
            ("Create Workpiece Options", CREATE_WORKPIECE_ICON, self.onCreateWorkpiecePressed),
            ("Gallery", GALLERY_ICON, self.onGalleryPressed),
        ]
        for button, icon_path, callback in workButtons:
            workFolder.add_app(button, icon_path, callback)

        serviceFolder = Folder("Service")
        serviceButtons = [
            ("Settings", SETTINGS_ICON, self.onSettingsPressed),
            ("Calibration", CALIBRATION_ICON, self.onCalibrationPressed),
            ("Service Tools", SETTINGS_ICON, self.onServicePressed),
        ]
        for button, icon, callback in serviceButtons:
            serviceFolder.add_app(button, icon, callback)

        administrationFolder = Folder("Administration")
        administrationButtons = [
            ("User Management", USER_MANAGEMENT_ICON, self.onUserManagementPressed)
        ]
        for button, icon, callback in administrationButtons:
            administrationFolder.add_app(button, icon, callback)

        statistics = Folder("Statistics")
        apps4 = [
            ("Analytics", "PLACEHOLDER ICON"),
            ("Reports", "PLACEHOLDER ICON"),
            ("Metrics", "PLACEHOLDER ICON"),
            ("Dashboard", "PLACEHOLDER ICON"),
        ]
        for button, icon in apps4:
            statistics.add_app(button, icon)

        folder5 = Folder("Development")
        apps5 = [
            ("Code Editor", "PLACEHOLDER ICON"),
            ("Debug Tools", "PLACEHOLDER ICON"),
            ("Version Control", "PLACEHOLDER ICON"),
        ]
        for button, icon in apps5:
            folder5.add_app(button, icon)

        folder6 = Folder("Utilities")
        apps6 = [
            ("File Manager", "PLACEHOLDER ICON"),
            ("System Monitor", "PLACEHOLDER ICON"),
            ("Network Tools", "PLACEHOLDER ICON"),
            ("Backup", "PLACEHOLDER ICON"),
            ("Cleanup", "PLACEHOLDER ICON"),
        ]
        for button, icon in apps6:
            folder6.add_app(button, icon)

        # Store all folders for management
        self.folders = [workFolder, serviceFolder, administrationFolder, statistics, folder5, folder6]

        # Set main window reference for all folders and connect signals
        for folder in self.folders:
            folder.set_main_window(self)
            folder.folder_opened.connect(self.on_folder_opened)
            folder.folder_closed.connect(self.on_folder_closed)
            folder.app_selected.connect(self.on_app_selected)
            # Connect the close current app signal if it exists
            if hasattr(folder, 'close_current_app_signal'):
                folder.close_current_app_signal.connect(self.close_current_app)

        # Add folders to grid (3 columns, 2 rows) with center alignment
        layout.addWidget(self.folders[0], 0, 0, Qt.AlignmentFlag.AlignCenter)  # Work
        layout.addWidget(self.folders[1], 0, 1, Qt.AlignmentFlag.AlignCenter)  # Service
        layout.addWidget(self.folders[2], 0, 2, Qt.AlignmentFlag.AlignCenter)  # Administration
        layout.addWidget(self.folders[3], 1, 0, Qt.AlignmentFlag.AlignCenter)  # Statistics
        layout.addWidget(self.folders[4], 1, 1, Qt.AlignmentFlag.AlignCenter)  # Development
        layout.addWidget(self.folders[5], 1, 2, Qt.AlignmentFlag.AlignCenter)  # Utilities

        # Set the container to use its content size
        container.adjustSize()

        # Add the folder page to the stacked widget (index 0)
        self.stacked_widget.addWidget(self.folder_page)

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def resizeEvent(self, event):
        """Handle window resize to maintain proper layout"""
        super().resizeEvent(event)
        # The responsive folders will handle their own sizing

    def sizeHint(self):
        """Provide a reasonable size hint for the window"""
        # Calculate size based on folder grid (3x2) plus margins
        folder_size = 350  # Approximate folder width
        spacing = 30
        margins = 80  # Total margins (40 on each side)

        width = (folder_size * 3) + (spacing * 2) + margins
        height = (folder_size * 2) + spacing + margins

        return self.size() if hasattr(self, '_initialized') else self.size()

    # App callback methods
    def onStartPressed(self):
        """Handle start button press"""
        print("Start button pressed - launching start app")

    def onCreateWorkpiecePressed(self):
        """Handle create workpiece button press"""
        print("Create Workpiece button pressed - launching workpiece creator")

    def onGalleryPressed(self):
        """Handle gallery button press"""
        print("Gallery button pressed - launching gallery app")

    def onSettingsPressed(self):
        """Handle settings button press"""
        print("Settings button pressed - launching settings app")

    def onCalibrationPressed(self):
        """Handle calibration button press"""
        print("Calibration button pressed - launching calibration app")

    def onServicePressed(self):
        """Handle service button press"""
        print("Service button pressed - launching service tools")

    def onUserManagementPressed(self):
        """Handle user management button press"""
        print("User Management button pressed - launching user management app")
        # The app selection signal will handle showing the app

    def keyPressEvent(self, event):
        """Handle key press events"""
        # ESC key to close current app (for demo purposes)
        if event.key() == Qt.Key.Key_Escape and self.current_running_app:
            self.close_current_app()
        super().keyPressEvent(event)

    def create_workpiece_via_camera_selected(self):
        """Handle camera selection for workpiece creation"""
        print("Create Workpiece via Camera selected")
        self.contour_editor = self.show_app("Contour Editor")
        createWorkpieceManager = CreateWorkpieceManager(self.contour_editor, self.controller)
        createWorkpieceManager.via_camera()



    def create_workpiece_via_dxf_selected(self):
        """Handle DXF selection for workpiece creation"""

        self.show_app("DXF Browser")


    def onLogEvent(self):
        print("Log event triggered in ApplicationDemo")

    def lock(self):
        """Lock the GUI to prevent interaction"""
        self.setEnabled(False)
        print("GUI locked")

    def unlock(self):
        """Unlock the GUI to allow interaction"""
        self.setEnabled(True)
        print("GUI unlocked")

    def onDxfBrowserSubmit(self, file_name, thumbnail):
        if not file_name:
            return

        from API.shared.dxf.DxfParser import DXFPathExtractor
        from pl_gui.settings.Paths import DXF_DIRECTORY
        from API.shared.dxf.utils import scale_contours
        from pl_gui.contour_editor.utils import qpixmap_to_cv, create_light_gray_pixmap

        file_name = file_name  # Assume single select for now
        extractor = DXFPathExtractor(os.path.join(DXF_DIRECTORY, file_name))

        wp_contour, spray, fill = extractor.get_opencv_contours()
        print("Extracted Contours:", spray)

        scale_x = 1280 / 900  # 1.422
        scale_y = 720 / 600  # 1.2

        wp_contour = scale_contours(wp_contour, scale_x, scale_y)
        spray = scale_contours(spray, scale_x, scale_y)
        fill = scale_contours(fill, scale_x, scale_y)

        print("Extracted Contours after scale:", spray)

        # SHOW AND SETUP CONTOUR EDITOR
        self.contour_editor = self.show_app("Contour Editor")

        # Create the image
        image = create_light_gray_pixmap()
        image = qpixmap_to_cv(image)

        # Set up the contour editor
        self.contour_editor.set_image(image)

        # Prepare dictionary for initContour (layer -> contours)
        contours_by_layer = {
            "External": [wp_contour] if wp_contour is not None and len(wp_contour) > 0 else [],
            "Contour": spray if len(spray) > 0 else [],
            "Fill": fill if len(fill) > 0 else []
        }

        # Initialize contours in the editor
        self.contour_editor.init_contours(contours_by_layer)

        # Set up the callback with proper error checking
        from PyQt6.QtCore import QTimer
        def set_callback():
            self.contour_editor.set_create_workpiece_for_on_submit_callback(self.onCreateWorkpieceSubmitDxf)
            print("DXF callback set successfully")

        # set_callback()
        QTimer.singleShot(100, set_callback)


    def onCreateWorkpieceSubmitDxf(self, data):
        """Handle DXF workpiece form submission - mirrors camera workflow"""
        print("onCreateWorkpieceSubmitDxf called with data:", data)

        wp_contours_data = self.contour_editor.to_wp_data()

        print("WP Contours Data: ", wp_contours_data)
        print("WP form data: ", data)

        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour', [])
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill', [])

        from API.shared.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External', [])
        data[WorkpieceField.CONTOUR_AREA.value] = 0 # PLACEHOLDER NEED TO CALCULATE AREA
        # Navigate back to main content like camera workflow

        # Save the workpiece using DXF endpoint
        print("Saving DXF workpiece with data:", data)
        self.controller.handle(SAVE_WORKPIECE, data)
        print("DXF workpiece saved successfully")

    def onLogout(self):
        """Handle logout action"""
        print("Logout action triggered")
        # Perform logout logic here
        # For example, clear session data, redirect to login screen, etc.
        SessionManager.logout()
        print("User logged out successfully")
        # Show login window fullscreen (non-blocking)
        login = LoginWindow(self.controller, onLogEventCallback=self.onLogEvent, header=self.header)
        login.showFullScreen()

        # Block here until login window returns
        if login.exec():
            print("Logged in successfully")
            self.setEnabled(True)  # Re-enable after successful login
        else:
            print("Login failed or cancelled")
            return  # You could also call self.close() or sys.exit() if needed

        self.onLogEvent()
        # Optionally, you can close the application or redirect to a login screen

class MockController():
    def init(self):
        pass

    def handle(self, *args):
        print("Handle: ", args)

    def sendRequest(self, message):
        if message == GET_SETTINGS:
            return self.__getSettings()

        print("Sending Request: ", message)
        return True, {"image": "MockImage",
                      "height": 4}

    def updateCameraFeed(self):
        pass

    def saveWorkpiece(self, data):
        print("Saving WP: ", data)

    def sendJogRequest(self, request):
        print("Sending Jog Request: ", request)

    def saveRobotCalibrationPoint(self):
        print("Saving Robot Point")

    def __getSettings(self):
        cameraSettings = CameraSettings()
        robotSettings = RobotSettings()
        return cameraSettings, robotSettings


    def saveWorkpieceFromDXF(self,data):
        print("Saving wp from dxf: ",data)

    def handleLogin(self,user,password):
        csv_file_path = os.path.join(os.path.dirname(__file__), "API/shared/user/users.csv")
        user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME, UserField.PASSWORD, UserField.ROLE]
        repo = CSVUsersRepository(csv_file_path, user_fields, User)
        service = UserService(repo)

        user = service.getUserById(2)
        SessionManager.login(user)
        return  "1"



def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show demo
    controller = MockController()
    demo = ApplicationDemo(controller)
    demo.show()

    print("Demo Instructions:")
    print("1. Click on any folder to open it")
    print("2. Click on any app icon to select it and see it open in full screen")
    print("3. Click the back button (←) in the sidebar to return to the main view")
    print("4. Press ESC to manually close the current app")
    print("5. Apps now open in a full-screen view using QStackedWidget")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()