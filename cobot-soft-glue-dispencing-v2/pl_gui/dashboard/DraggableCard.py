from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QWidget


class DraggableCard(QFrame):
    def __init__(self, title: str, content_widgets: list, remove_callback=None, container=None):
        super().__init__()
        self.setObjectName(title)
        self.container = container
        self.remove_callback = remove_callback
        self.dragEnabled = True

        self.is_minimized = False
        self.content_widgets = content_widgets
        self.original_min_height = 80

        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMaximumWidth(500)
        self.setMinimumHeight(self.original_min_height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # --- Title bar layout ---
        self.top_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setMaximumHeight(40)
        self.title_label.setStyleSheet("font-weight: bold;")

        self.top_layout.addWidget(self.title_label)
        self.top_layout.addStretch()

        self.layout.addLayout(self.top_layout)

        # --- Add content widgets ---
        for w in self.content_widgets:
            if isinstance(w, QLabel):
                # For QLabel widgets, create a container widget to avoid frame wrapping
                container_widget = QWidget()
                container_widget.setStyleSheet("QWidget { border: none; background: transparent; }")
                container_layout = QVBoxLayout(container_widget)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.addWidget(w)
                self.layout.addWidget(container_widget)
            else:
                self.layout.addWidget(w)

    def hideLabel(self):
        self.title_label.setVisible(False)

    def on_close(self):
        if self.remove_callback:
            for widget in self.content_widgets:
                widget.close()

            self.remove_callback(self)

    def set_selected(self, selected: bool):
        if selected:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #0078d7;
                    border-radius: 10px;
                    background-color: #d0e7ff;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    padding: 10px;
                }
            """)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

        if self.container:
            self.container.select_card(self)

        if hasattr(self, 'glue_type_combo') and callable(getattr(self, 'on_double_click', None)):
            glue_type = self.glue_type_combo.currentText()
            self.on_double_click(glue_type)

    def mousePressEvent(self, event):
        if not self.dragEnabled:
            # Dragging disabled — ignore drag start
            return super().mousePressEvent(event)

        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.objectName())
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())

            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        event.ignore()

    def dragMoveEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        event.ignore()


# Alternative approach: Create a single label with HTML content
class DraggableCardSimple(QFrame):
    def __init__(self, title: str, content_texts: list, remove_callback=None, container=None):
        super().__init__()
        self.setObjectName(title)
        self.container = container
        self.remove_callback = remove_callback
        self.dragEnabled = True

        self.is_minimized = False
        self.original_min_height = 80

        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMaximumWidth(500)
        self.setMinimumHeight(self.original_min_height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # --- Title bar layout ---
        self.top_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setMaximumHeight(40)
        self.title_label.setStyleSheet("font-weight: bold;")

        self.top_layout.addWidget(self.title_label)
        self.top_layout.addStretch()

        self.layout.addLayout(self.top_layout)

        # --- Single content label with HTML ---
        if content_texts:
            content_html = "<br>".join(content_texts)
            self.content_label = QLabel(content_html)
            self.content_label.setStyleSheet("QLabel { border: none; background: transparent; }")
            self.content_label.setWordWrap(True)
            self.layout.addWidget(self.content_label)

    def hideLabel(self):
        self.title_label.setVisible(False)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Option 1: Using container widgets
    card1 = DraggableCard("Test Card 1", [QLabel("Content 1"), QLabel("Content 2")])
    card1.show()

    # Option 2: Using single HTML label
    card2 = DraggableCardSimple("Test Card 2", ["Content 1", "Content 2"])
    card2.move(520, 0)
    card2.show()

    sys.exit(app.exec())