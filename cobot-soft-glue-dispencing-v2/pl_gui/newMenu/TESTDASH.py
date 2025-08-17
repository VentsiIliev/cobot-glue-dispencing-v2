import os
import time

from PyQt6.QtCore import QSize, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QFont, QColor

from pl_gui.ButtonConfig import ButtonConfig
from pl_gui.Sidebar import Sidebar
from pl_gui.ManualControlWidget import ManualControlWidget
from pl_gui.Endpoints import *
from PyQt6.QtCore import QPoint, QPropertyAnimation, pyqtSignal
from pl_gui.SessionInfoWidget import SessionInfoWidget
from pl_gui.controller.ButtonKey import ButtonKey

# Resource directory setup
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources")
RUN_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "RUN_BUTTON.png")
RUN_BUTTON_PRESSED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_RUN_BUTTON.png")
STOP_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "STOP_BUTTON.png")
STOP_BUTTON_PRESSED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_STOP_BUTTON.png")
CREATE_WORKPIECE_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "CREATE_WORKPIECE_BUTTON_SQUARE.png")
CREATE_WORKPIECE_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons",
                                                         "PRESSED_CREATE_WORKPIECE_BUTTON_SQUARE.png")
DXF_BUTTON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "DXF_BUTTON.png")
HOME_ROBOT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HOME_MACHINE_BUTTON.png")
STATIC_IMAGE_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "BACKGROUND_&_Logo.png")
ACCOUNT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "ACCOUNT_BUTTON_SQUARE.png")
GALLERY_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LIBRARY_BUTTON_SQARE.png")


class MaterialSidebar(QFrame):
    """Material Design 3 sidebar with proper elevation and tokens"""

    def __init__(self, screen_width, upper_buttons, lower_buttons, parent=None):
        super().__init__(parent)
        self.setupMaterialDesign(screen_width, upper_buttons, lower_buttons)

    def setupMaterialDesign(self, screen_width, upper_buttons, lower_buttons):
        """Setup Material Design 3 sidebar styling"""
        self.setFixedWidth(max(120, int(screen_width * 0.08)))

        # Material Design 3 surface container styling
        self.setStyleSheet("""
            QFrame {
                background: #F7F2FA;
                border: none;
                border-right: 1px solid #E7E0EC;
            }
        """)

        # Material Design elevation shadow (level 2)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(2, 0)
        self.setGraphicsEffect(shadow)

        # Use original Sidebar logic but with Material Design styling
        # You would replace this with your actual Sidebar implementation
        # but applying Material Design 3 tokens and elevation


class MaterialDrawer(QFrame):
    """Material Design 3 session info drawer with proper motion and elevation"""

    logout_requested = pyqtSignal()

    def __init__(self, parent=None, logout_callback=None):
        super().__init__(parent)
        self.logout_callback = logout_callback
        self.is_visible = False
        self.setupMaterialDesign()

    def setupMaterialDesign(self):
        """Setup Material Design 3 drawer styling"""
        self.setFixedWidth(360)  # Material Design standard drawer width

        # Material Design 3 surface container high styling
        self.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: none;
                border-left: 1px solid #E7E0EC;
            }
        """)

        # Material Design elevation shadow (level 3)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(-4, 0)
        self.setGraphicsEffect(shadow)

        # Position off-screen initially
        self.hide()

    def toggle(self):
        """Material Design 3 drawer toggle with proper motion"""
        if self.is_visible:
            self.slide_out()
        else:
            self.slide_in()

    def slide_in(self):
        """Material Design slide-in animation"""
        if not self.parent():
            return

        self.show()
        self.raise_()

        # Material Design motion timing
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)  # Material standard timing
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        parent_width = self.parent().width()
        start_pos = QPoint(parent_width, 0)
        end_pos = QPoint(parent_width - self.width(), 0)

        self.move(start_pos)
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.start()

        self.is_visible = True

    def slide_out(self):
        """Material Design slide-out animation"""
        if not self.parent():
            return

        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        parent_width = self.parent().width()
        start_pos = self.pos()
        end_pos = QPoint(parent_width, 0)

        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.finished.connect(self.hide)
        self.slide_animation.start()

        self.is_visible = False

    def resize_to_parent_height(self):
        """Maintain proper sizing relative to parent"""
        if self.parent():
            self.setFixedHeight(self.parent().height())


class MaterialDashboardContent(QFrame):
    """Material Design 3 dashboard content with proper surface hierarchy and elevation"""

    logout_requested = pyqtSignal()

    def __init__(self, screenWidth=1280, controller=None, parent=None):
        super().__init__()
        self.screenWidth = screenWidth
        self.parent = parent
        self.controller = controller

        # Material Design 3 setup
        self.setupMaterialDesign()
        self.setupLayout()
        self.setupComponents()

        # Animation timers for performance
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.updateMaterialSizing)

    def setupMaterialDesign(self):
        """Setup Material Design 3 surface styling"""
        # Material Design 3 surface styling
        self.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: none;
            }
        """)
        self.setContentsMargins(0, 0, 0, 0)

    def setupLayout(self):
        """Setup Material Design 3 layout system"""
        # Main layout with Material Design spacing
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)  # No spacing for surface boundaries
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def setupComponents(self):
        """Setup dashboard components with Material Design 3 principles"""

        # Material Design drawer setup
        self.drawer = MaterialDrawer(self, self.onLogout)
        self.drawer.logout_requested.connect(self.logout_requested.emit)
        self.drawer.setVisible(False)

        # Material Design sidebar
        self.side_menu = self.create_material_side_menu()
        self.createWpButtonEnableToggle(False)
        self.startButtonEnableToggle(False)
        self.main_layout.addWidget(self.side_menu)

        # Material Design content area
        self.stacked_widget = QStackedWidget()
        self.content_area = QWidget()

        # Import your dashboard widget here
        from pl_gui.dashboard.NewDashboardWidget import GlueDashboardWidget
        self.dashboard_widget = GlueDashboardWidget(
            updateCameraFeedCallback=self.updateCameraFeed,
            parent=self
        )

        # Apply Material Design styling to dashboard widget
        self.styleDashboardWidget()

        # Content layout with Material Design principles
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(24, 24, 24, 24)  # Material Design margins
        self.content_layout.setSpacing(24)  # Material Design spacing
        self.content_layout.addWidget(self.dashboard_widget)
        self.content_area.setLayout(self.content_layout)

        # Add to stacked widget
        self.stacked_widget.addWidget(self.content_area)
        self.main_layout.addWidget(self.stacked_widget)

        # Initialize form references
        self.createWorkpieceForm = None
        self.manualMoveContent = None

    def styleDashboardWidget(self):
        """Apply Material Design 3 styling to dashboard widget"""
        if hasattr(self.dashboard_widget, 'setStyleSheet'):
            self.dashboard_widget.setStyleSheet("""
                QWidget {
                    background: transparent;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                }
                QFrame {
                    background: #FFFBFE;
                    border: 1px solid #E7E0EC;
                    border-radius: 24px;
                }
                QPushButton {
                    background: #6750A4;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px 24px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background: #7965AF;
                }
                QPushButton:pressed {
                    background: #5A3D99;
                }
                QPushButton:disabled {
                    background: #E8DEF8;
                    color: #79747E;
                }
                QLabel {
                    color: #1D1B20;
                    font-weight: 400;
                }
            """)

    def create_material_side_menu(self):
        """Create Material Design 3 sidebar with proper elevation and tokens"""
        upper_buttons_config = [
            ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH,
                         ButtonKey.START.value, self.onStartButton),
            ButtonConfig(STOP_BUTTON_ICON_PATH, STOP_BUTTON_PRESSED_ICON_PATH,
                         ButtonKey.SETTINGS.value, self.onStopButton),
            ButtonConfig(CREATE_WORKPIECE_BUTTON_ICON_PATH, CREATE_WORKPIECE_PRESSED_BUTTON_ICON_PATH,
                         ButtonKey.CREATE_WORKPIECE.value, self.onCreateWorkpiece),
            ButtonConfig(HOME_ROBOT_BUTTON_ICON_PATH, HOME_ROBOT_BUTTON_ICON_PATH,
                         ButtonKey.HOME_ROBOT.value, self.onHomeRobot),
            ButtonConfig(DXF_BUTTON_PATH, DXF_BUTTON_PATH,
                         ButtonKey.DFX.value, self.dfxUpload),
            ButtonConfig(GALLERY_BUTTON_ICON_PATH, GALLERY_BUTTON_ICON_PATH,
                         ButtonKey.GALLERY.value, self.onGallery),
            ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH,
                         ButtonKey.TEST_CREATE_WP.value, self.on_test_create_workpiece),
        ]

        lower_buttons_config = [
            ButtonConfig(ACCOUNT_BUTTON_ICON_PATH, ACCOUNT_BUTTON_ICON_PATH,
                         ButtonKey.ACCOUNT.value, self.openAccountPage)
        ]

        # Create sidebar with Material Design styling
        side_menu = Sidebar(self.screenWidth, upper_buttons_config, lower_buttons_config)
        side_menu.setContentsMargins(0, 0, 0, 0)

        # Apply Material Design 3 styling to sidebar
        side_menu.setStyleSheet("""
            QFrame {
                background: #F7F2FA;
                border: none;
                border-right: 1px solid #E7E0EC;
            }
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 24px;
                padding: 12px;
                margin: 8px;
            }
            QPushButton:hover {
                background: #E8DEF8;
            }
            QPushButton:pressed {
                background: #D1C4E9;
            }
            QPushButton:checked {
                background: #6750A4;
            }
        """)

        # Add Material Design elevation shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(2, 0)
            side_menu.setGraphicsEffect(shadow)
        except:
            pass

        return side_menu

    def updateMaterialSizing(self):
        """Update Material Design sizing based on screen dimensions"""
        new_width = self.width()

        # Material Design responsive icon sizing
        icon_size = max(48, min(64, int(new_width * 0.04)))

        # Update sidebar button icon sizes
        if hasattr(self.side_menu, 'buttons'):
            for button in self.side_menu.buttons:
                button.setIconSize(QSize(icon_size, icon_size))

        # Ensure drawer maintains proper proportions
        self.drawer.resize_to_parent_height()

    def onLogout(self):
        """Handle logout with Material Design feedback"""
        if self.parent is None:
            return
        self.parent.logout()
        self.drawer.setVisible(False)

    def updateCameraFeed(self):
        """Camera feed update handler"""
        return self.controller.handle(UPDATE_CAMERA_FEED)

    def onToggleCameraViewSize(self):
        """Toggle camera view with Material Design transitions"""
        if hasattr(self, 'cameraFeed'):
            is_expanded = self.cameraFeed.current_resolution == self.cameraFeed.resolution_small
            if hasattr(self, 'glueMeters'):
                self.glueMeters.setVisible(is_expanded)

    # Button event handlers with Material Design feedback
    def onStartButton(self):
        """Handle start button with Material Design interaction"""
        self.controller.handle(START)

    def onStopButton(self):
        """Handle stop button with Material Design interaction"""
        self.controller.handle(STOP)

    def onHomeRobot(self):
        """Handle home robot with Material Design feedback"""
        self.controller.handle(HOME_ROBOT)
        self.createWpButtonEnableToggle(True)
        self.startButtonEnableToggle(True)

    def startButtonEnableToggle(self, state):
        """Toggle start button state with Material Design styling"""
        if hasattr(self.side_menu, 'buttonsDict'):
            button = self.side_menu.buttonsDict.get(ButtonKey.START.value)
            if button:
                button.setEnabled(state)
                # Apply disabled styling if needed
                if not state:
                    button.setStyleSheet(button.styleSheet() + """
                        QPushButton:disabled {
                            background: #E8DEF8;
                            color: #79747E;
                        }
                    """)

    def createWpButtonEnableToggle(self, state):
        """Toggle create workpiece button state with Material Design styling"""
        if hasattr(self.side_menu, 'buttonsDict'):
            button = self.side_menu.buttonsDict.get(ButtonKey.CREATE_WORKPIECE.value)
            if button:
                button.setEnabled(state)

    def openAccountPage(self):
        """Open account page with Material Design motion"""
        self.drawer.toggle()

    def onManualMoveButton(self):
        """Handle manual move with Material Design drawer animation"""
        DRAWER_WIDTH = 400  # Material Design standard drawer width

        if self.manualMoveContent is None:
            if self.createWorkpieceForm:
                self.createWorkpieceForm.close()
                self.createWorkpieceForm = None

            self.manualMoveContent = ManualControlWidget(
                self,
                callback=self.manualMoveCallback,
                jogCallback=self.controller.handle
            )

            # Apply Material Design styling
            self.manualMoveContent.setStyleSheet("""
                QWidget {
                    background: #FFFBFE;
                    border: none;
                    border-left: 1px solid #E7E0EC;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                }
            """)

            self.manualMoveContent.setParent(self)
            self.manualMoveContent.setGeometry(self.width(), 0, DRAWER_WIDTH, self.height())
            self.manualMoveContent.raise_()
            self.manualMoveContent.show()

            # Material Design slide animation
            self.drawer_anim = QPropertyAnimation(self.manualMoveContent, b"pos")
            self.drawer_anim.setDuration(300)  # Material standard timing
            self.drawer_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.drawer_anim.setStartValue(QPoint(self.width(), 0))
            self.drawer_anim.setEndValue(QPoint(self.width() - DRAWER_WIDTH, 0))
            self.drawer_anim.start()
        else:
            # Material Design slide-out animation
            self.drawer_anim = QPropertyAnimation(self.manualMoveContent, b"pos")
            self.drawer_anim.setDuration(300)
            self.drawer_anim.setEasingCurve(QEasingCurve.Type.InCubic)
            self.drawer_anim.setStartValue(self.manualMoveContent.pos())
            self.drawer_anim.setEndValue(QPoint(self.width(), 0))
            self.drawer_anim.finished.connect(self.manualMoveContent.deleteLater)
            self.drawer_anim.start()
            self.manualMoveContent = None

    def on_test_create_workpiece(self):
        """Test create workpiece with Material Design feedback"""
        print("Material Design: Test Create Workpiece Button Clicked")

    def onGallery(self):
        """Handle gallery button with Material Design interaction"""
        if self.parent:
            self.parent.onGalleryButton()

    def onCreateWorkpiece(self):
        """Handle create workpiece with Material Design dialog"""
        from pl_gui.dashboard.WorkpieceOptionsWidget import WorkpieceOptionsWidget
        dialog = WorkpieceOptionsWidget(self)

        # Apply Material Design styling to dialog
        dialog.setStyleSheet("""
            QDialog {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 28px;
            }
            QPushButton {
                background: #6750A4;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 24px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #7965AF;
            }
        """)

        def onCamera():
            print("Material Design: Camera option selected")
            self.controller.handle(CREATE_WORKPIECE_TOPIC, self.handleCreateWorkpieceSuccess,
                                   self.handleCreateWorkpieceFailure)

        def onDxfUpload():
            print("Material Design: DXF upload option selected")
            self.dfxUpload()

        dialog.camera_selected.connect(onCamera)
        dialog.dxf_selected.connect(onDxfUpload)
        dialog.exec()

    def handleCreateWorkpieceSuccess(self, frame, contours, data):
        """Handle successful workpiece creation with Material Design transitions"""
        self.parent.show_contour_editor()
        self.parent.contourEditor.set_image(frame)
        contours_by_layer = {
            "External": [contours] if len(contours) > 0 else [],
            "Contour": [],
            "Fill": []
        }
        self.parent.contourEditor.init_contours(contours_by_layer)
        self.parent.contourEditor.createWorkpieceForm.onSubmitCallBack = self.onCreateWorkpieceSubmit

    def handleCreateWorkpieceFailure(self, req, msg):
        """Handle workpiece creation failure with Material Design feedback"""
        from pl_gui.FeedbackProvider import FeedbackProvider
        FeedbackProvider.showMessage(msg)

    def manualMoveCallback(self):
        """Manual move callback cleanup"""
        self.manualMoveContent = None

    def onCreateWorkpieceSubmit(self, data):
        """Handle workpiece submission with Material Design feedback"""
        wp_contours_data = self.parent.contourEditor.contourEditor.manager.to_wp_data()

        print("WP Contours Data: ", wp_contours_data)
        print("WP form data: ", data)

        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour')
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill')

        from API.shared.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External')

        self.side_menu.uncheck_all_buttons()
        if hasattr(self.dashboard_widget, 'camera_feed'):
            self.dashboard_widget.camera_feed.resume_feed()

        self.controller.handle(SAVE_WORKPIECE, data)
        if hasattr(self.dashboard_widget, 'camera_feed'):
            self.dashboard_widget.camera_feed.resume_feed()
        self.parent.show_home()

    def dfxUpload(self):
        """Handle DXF upload with Material Design interaction"""
        if self.parent:
            self.parent.showDxfBrowser()

    def resizeEvent(self, event):
        """Handle resize with Material Design responsive behavior"""
        super().resizeEvent(event)

        # Debounced resize for performance
        self._resize_timer.stop()
        self._resize_timer.start(150)  # Material Design timing

    def calibPickup(self):
        """Handle calibration pickup"""
        if self.controller:
            self.controller.calibPickupArea()

    def sendMoveBeltReq(self):
        """Handle belt movement request"""
        if self.controller:
            self.controller.moveBelt()


# Alias for backward compatibility
MainContent = MaterialDashboardContent

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Material Design 3 application setup
    app.setStyle('Fusion')

    # Material Design font
    font = QFont("Roboto", 10)
    if not font.exactMatch():
        font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Material Design application styling
    app.setStyleSheet("""
        QApplication {
            background: #FFFBFE;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        QToolTip {
            background: #313033;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
        }
    """)


    # Create mock controller for testing
    class MockController:
        def handle(self, *args):
            print(f"Material Design Dashboard: Handle called with {args}")
            return True


    # Create and show dashboard
    controller = MockController()
    window = MaterialDashboardContent(1280, controller)
    window.show()
    window.resize(1400, 900)

    print("Material Design 3 Dashboard Content")
    print("• Modern Material Design 3 styling")
    print("• Proper elevation and surface hierarchy")
    print("• Responsive design with Material Design tokens")
    print("• Smooth animations with Material Design timing")

    sys.exit(app.exec())