from PyQt6.QtWidgets import QWidget

from API.MessageBroker import MessageBroker
from pl_gui.Endpoints import WORPIECE_GET_ALL
from pl_gui.main_application.appWidgets.AppWidget import AppWidget



class ServiceCalibrationAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None):
        self.parent= parent
        self.controller = controller
        super().__init__("ServiceCalibrationAppWidget", parent)
        print("ServiceCalibrationAppWidget initialized with parent:", self.parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button
        self.setStyleSheet("""
                           QWidget {
                               background-color: #f8f9fa;
                               font-family: 'Segoe UI', Arial, sans-serif;
                               color: #000000;  /* Force black text */
                           }

                       """)
        try:
            from pl_gui.settings_view.CalibrationSettingsTab import CalibrationServiceTabLayout

            content_widget = QWidget(self.parent)
            content_layout = CalibrationServiceTabLayout()
            content_widget.setLayout(content_layout)
            print("CALIBRATION WIDGET TYPE:", type(content_widget))
            # broker = MessageBroker()
            # broker.subscribe("Language", content_widget.updateLanguage)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("Service Calibration not available, using placeholder")
