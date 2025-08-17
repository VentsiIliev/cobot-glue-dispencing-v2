import sys
from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QLabel, QComboBox, QSizePolicy
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import random

from PyQt6.QtCore import Qt, pyqtSignal

from pl_gui.dashboard.DraggableCard import DraggableCard
from pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
from API.MessageBroker import MessageBroker
from pl_gui.specific.enums.GlueType import GlueType
from PyQt6.QtWidgets import QFrame
from API.localization.LanguageResourceLoader import LanguageResourceLoader
from API.localization.enums.Message import Message

class GlueSetpointFields(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.langLoader = LanguageResourceLoader()
        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.g_per_m_input = QLineEdit()
        self.g_per_sqm_input = QLineEdit()

        self.g_per_m_input.setPlaceholderText("g/m")
        self.g_per_sqm_input.setPlaceholderText("g/m²")

        self.layout.addRow("g/m:", self.g_per_m_input)
        self.layout.addRow("g/m²:", self.g_per_sqm_input)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


import sys
from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QLabel, QComboBox, QSizePolicy, QVBoxLayout
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import random
# from pl_gui.dashboard.DraggableCard import DraggableCard
# from pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
# from API.MessageBroker import MessageBroker
# from pl_gui.specific.enums.GlueType import GlueType
from PyQt6.QtWidgets import QFrame




class GlueSetpointFields(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.g_per_m_input = QLineEdit()
        self.g_per_sqm_input = QLineEdit()

        self.g_per_m_input.setPlaceholderText("g/m")
        self.g_per_sqm_input.setPlaceholderText("g/m²")

        self.layout.addRow("g/m:", self.g_per_m_input)
        self.layout.addRow("g/m²:", self.g_per_sqm_input)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


class GlueMeterCard(QFrame):
    glueTypeChanged = pyqtSignal(str)
    def __init__(self, label_text, index):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.build_ui()
        self.subscribe()

    def build_ui(self):
        # Create the main layout for the card
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create the glue type combo box
        self.glue_type_combo = QComboBox()
        self.glue_type_combo.addItems([GlueType.TypeA.value, GlueType.TypeB.value, GlueType.TypeC.value])
        self.glue_type_combo.setCurrentText("Type A")
        self.glue_type_combo.currentTextChanged.connect(self.on_glue_type_changed)

        # Create the setpoints widget
        self.setpoints = GlueSetpointFields()

        # Create the meter widget (placeholder for now)
        self.meter_widget = GlueMeterWidget(self.index)
        # self.meter_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meter_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")

        # Add all widgets to the main layout
        # main_layout.addWidget(self.label)
        # main_layout.addWidget(QLabel("Glue Type:"))
        main_layout.addWidget(self.glue_type_combo)
        main_layout.addWidget(self.meter_widget)
        main_layout.addWidget(self.setpoints)

        # Set a border for the card
        self.setStyleSheet("GlueMeterCard { border: 2px solid #ccc; border-radius: 5px; }")

    def on_glue_type_changed(self, glue_type):
        print(f"Glue type changed to: {glue_type}")
        self.glueTypeChanged.emit(glue_type)
    def subscribe(self):
        meter = GlueMeterWidget(self.index)
        broker = MessageBroker()
        broker.subscribe(f"GlueMeter_{self.index}/VALUE", meter.updateWidgets)
        broker.subscribe(f"GlueMeter_{self.index}/STATE", meter.updateState)

    def unsubscribe(self):
        meter = GlueMeterWidget(self.index)
        broker = MessageBroker()
        broker.unsubscribe(f"GlueMeter_{self.index}/VALUE", meter.updateWidgets)
        broker.unsubscribe(f"GlueMeter_{self.index}/STATE", meter.updateState)

    def closeEvent(self, event):
        self.unsubscribe()
        super().closeEvent(event)


from PyQt6.QtWidgets import QApplication, QMainWindow

if __name__ == "__main__":
    app = QApplication([])

    # Create a main window to host the GlueMeterCard
    main_window = QMainWindow()
    main_window.setWindowTitle("GlueMeterCard Test")
    main_window.setGeometry(100, 100, 400, 300)

    # Initialize the GlueMeterCard
    card = GlueMeterCard("Test Glue Meter", 1)

    # Set the card as the central widget of the main window
    main_window.setCentralWidget(card)

    # Show the main window
    main_window.show()

    # Execute the application
    app.exec()