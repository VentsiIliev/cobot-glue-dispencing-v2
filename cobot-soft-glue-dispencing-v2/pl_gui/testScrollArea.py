import sys
import os
import random
import time
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLabel, QScrollArea, \
    QGridLayout, QPushButton, QSizePolicy, QSplitter, QListWidget, QListWidgetItem
from PyQt6.QtWidgets import QScroller

# Define the resource directory and placeholder image path
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
PLACEHOLDER_IMAGE_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "placeholder.jpg")
APPLY_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "createWorkpieceIcons", "ACCEPT_BUTTON.png")
SELECT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PLUS_BUTTON.png")
REMOVE_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "MINUS_BUTTON.png")


class ThumbnailWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)  # Enable touch events for the widget
        self.setWindowTitle("Date Picker and Thumbnail Viewer")
        self.setGeometry(100, 100, 800, 400)

        # Store references to the preview image labels and timestamps
        self.preview_images = []
        self.timestamps = []  # List to store timestamps corresponding to the images

        # Main layout: Horizontal layout with two sections (left and right)
        main_layout = QHBoxLayout(self)

        # Create a splitter to manage the left and right sections
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Section Layout: Date Picker and Thumbnails
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout

        # Create Date Pickers for "From" and "To" date range
        self.from_date_picker = QDateEdit(self)
        self.from_date_picker.setCalendarPopup(True)
        self.from_date_picker.setDate(QDate.currentDate())  # Set default "from" date to today's date

        self.to_date_picker = QDateEdit(self)
        self.to_date_picker.setCalendarPopup(True)
        self.to_date_picker.setDate(QDate.currentDate())  # Set default "to" date to today's date

        # Label for the date range
        date_range_label = QLabel("Select Date Range:", self)

        # Add the date pickers and label to the layout
        left_layout.addWidget(date_range_label)
        left_layout.addWidget(QLabel("From:"))
        left_layout.addWidget(self.from_date_picker)
        left_layout.addWidget(QLabel("To:"))
        left_layout.addWidget(self.to_date_picker)

        # Thumbnails Section
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_layout.setSpacing(10)  # Spacing between thumbnails
        self.thumbnail_layout.setHorizontalSpacing(10)  # Horizontal spacing
        self.thumbnail_layout.setVerticalSpacing(10)  # Vertical spacing
        self.thumbnail_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the grid layout

        # Load the placeholder image once
        self.placeholder_pixmap = QPixmap(100, 100)
        self.placeholder_pixmap.load(PLACEHOLDER_IMAGE_PATH)

        self.thumbnail_size = (120, 120)  # Initial thumbnail size (width, height)

        # Add sample thumbnails (This can be dynamic in a real use case)
        import random
        import time

        for i in range(100):  # Increased the number of thumbnails for testing vertical scroll
            # Create a vertical layout for each thumbnail item
            thumbnail_item_layout = QVBoxLayout()
            thumbnail_item_layout.setSpacing(0)  # Remove spacing between label and button
            thumbnail_item_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the thumbnail layout

            # Generate a random timestamp or use the current time for a unique label
            random_timestamp = time.strftime('%Y-%m-%d %H:%M:%S',
                                             time.localtime(random.randint(1609459200, 1704067200)))

            # Create label for thumbnail with random timestamp
            thumbnail_label = QLabel(f"{random_timestamp}", self)
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Create button for thumbnail
            thumbnail_button = QPushButton(self)
            thumbnail_button.clicked.connect(lambda _, i=i, timestamp=random_timestamp: self.show_preview(i, timestamp))
            thumbnail_button.setIcon(QIcon(self.placeholder_pixmap))  # Set the placeholder image as the icon
            thumbnail_button.setIconSize(self.placeholder_pixmap.size())  # Ensure the icon size matches the image size
            thumbnail_button.setFixedSize(QSize(*self.thumbnail_size))  # Convert tuple to QSize

            # Add label and button to the thumbnail layout
            thumbnail_item_layout.addWidget(thumbnail_label)
            thumbnail_item_layout.addWidget(thumbnail_button)

            # Add the thumbnail item layout to the grid layout
            self.thumbnail_layout.addLayout(thumbnail_item_layout, i // 4, i % 4)  # Adjust the grid to 4 columns

        # Scrollable Area for Thumbnails with only vertical scroll enabled
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
        self.scroll_area.setWidget(self.create_thumbnail_widget())

        # Enable scrolling by pixel
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        # Ensure touch events are enabled for the scroll area
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)

        # Add date picker and scroll area for thumbnails to the left section
        left_layout.addWidget(self.scroll_area)

        # Right Section Layout: Preview area
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the right layout

        # Create horizontal splitter for the right section
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half: Preview label and image
        preview_layout = QVBoxLayout()
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)  # Align top-center
        preview_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the preview layout
        preview_layout.setSpacing(5)  # Reduced spacing between label and image

        # Preview label at the top
        self.preview_label = QLabel("Select a Thumbnail to Preview", self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)

        # Preview image section - 50% of the right section's width
        self.preview_image_label = QLabel(self)
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure the preview image scales responsively within the layout
        self.preview_image_label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                               QSizePolicy.Policy.Expanding)  # Ensure it takes space

        preview_layout.addWidget(self.preview_image_label)

        # Create a widget for the top section of the right side and set layout
        top_widget = QWidget(self)
        top_widget.setLayout(preview_layout)

        # Set a thin border for the top widget to separate it from the bottom section
        top_widget.setStyleSheet("border-bottom: 2px solid #cccccc;")  # Thin border between top and bottom sections

        # Bottom half: List and Button section
        selectedImagesLayout = QVBoxLayout()
        selectedImagesLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the button layout

        # Create a list widget to display the preview image text labels
        self.label_list = QListWidget(self)
        selectedImagesLayout.addWidget(self.label_list)

        # Select Button
        self.selectButton = QPushButton("", self)
        self.selectButton.setStyleSheet("border:none")
        self.selectButton.setIcon(QIcon(APPLY_BUTTON_ICON_PATH))

        self.removeButton = QPushButton("",self)
        self.removeButton.setStyleSheet("border:none")
        self.removeButton.setIcon(QIcon(REMOVE_BUTTON_ICON_PATH))

        self.applyButton = QPushButton("",self)
        self.applyButton.setStyleSheet("border:none")
        self.applyButton.setIcon(QIcon(APPLY_BUTTON_ICON_PATH))

        self.buttonLayout = QHBoxLayout()
        selectedImagesLayout.addLayout(self.buttonLayout)

        self.buttonLayout.addWidget(self.selectButton)
        self.buttonLayout.addWidget(self.removeButton)
        self.buttonLayout.addWidget(self.applyButton)
        # Connect the button to the function that adds the preview label to the list
        self.selectButton.clicked.connect(self.add_preview_to_list)
        self.removeButton.clicked.connect(self.remove_preview_from_list)
        self.applyButton.clicked.connect(self.on_apply)

        # Create a widget for the bottom section of the right side and set layout
        bottom_widget = QWidget(self)
        bottom_widget.setLayout(selectedImagesLayout)

        # Add the top and bottom widgets to the horizontal splitter in the right layout
        right_splitter.addWidget(top_widget)
        right_splitter.addWidget(bottom_widget)

        # Set the initial sizes of the top and bottom sections to 50% each
        right_splitter.setSizes([self.height() // 2, self.height() // 2])

        # Add the splitter to the right layout
        right_layout.addWidget(right_splitter)

        # Create two widgets for the left and right sections
        left_widget = QWidget(self)
        left_widget.setLayout(left_layout)

        right_widget = QWidget(self)
        right_widget.setLayout(right_layout)

        # Add the widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Set the initial sizes of both sections to be 50% each
        splitter.setSizes([self.width() // 2, self.width() // 2])

        # Add the splitter to the main layout
        main_layout.addWidget(splitter)

        # Connect date pickers' dateChanged signal to filter thumbnails
        self.from_date_picker.dateChanged.connect(self.filter_thumbnails_by_date)
        self.to_date_picker.dateChanged.connect(self.filter_thumbnails_by_date)

    def create_thumbnail_widget(self):
        """Creates and returns the widget that holds the thumbnails"""
        thumbnail_widget = QWidget(self)
        thumbnail_widget.setLayout(self.thumbnail_layout)
        return thumbnail_widget

    def show_preview(self, index, timestamp):
        """Handles the display of the large preview of the clicked thumbnail"""
        # Display the label for the clicked thumbnail using timestamp
        self.preview_label.setText(f"Preview of {timestamp}")

        # Store the corresponding image reference and timestamp in the list
        self.preview_images.append(self.placeholder_pixmap)
        self.timestamps.append(timestamp)

        # Update the preview image
        self.update_preview_image()

    def filter_thumbnails_by_date(self):
        """Filters thumbnails based on the selected date range."""
        print("Filtering thumbnails by date...")  # Debugging statement

        # Get the selected date range
        from_date = self.from_date_picker.date()
        to_date = self.to_date_picker.date()
        print(f"From: {from_date} To: {to_date}")


    def get_thumbnail_timestamp(self, index):
        """Returns the timestamp of the thumbnail at the given index"""
        return self.timestamps[index]

    def add_preview_to_list(self):
        """Adds the preview image label to the list when the Select button is clicked"""
        if self.preview_images and self.timestamps:
            timestamp = self.timestamps[-1]
            item = QListWidgetItem(f"Image {len(self.preview_images)} - {timestamp}")
            self.label_list.addItem(item)

        # Connect list item clicked signal to display corresponding image
        self.label_list.itemClicked.connect(self.display_selected_image)

    def remove_preview_from_list(self):
        """Removes the selected preview image from the list."""
        # Get the selected item from the list widget
        selected_item = self.label_list.currentItem()

        if selected_item:
            # Remove the item from the list
            row = self.label_list.row(selected_item)
            self.label_list.takeItem(row)  # Remove item from the list

            # Remove the corresponding image from the preview_images and timestamps list
            if 0 <= row < len(self.preview_images):
                del self.preview_images[row]  # Remove image from the list of preview images
                del self.timestamps[row]  # Remove timestamp from the list of timestamps

            # Update the preview image to show the last remaining image or clear it
            if self.preview_images:
                self.update_preview_image()
            else:
                self.preview_label.setText("Select a Thumbnail to Preview")
                self.preview_image_label.clear()

    def on_apply(self):
        print("Apply Button Pressed")

    def display_selected_image(self, item):
        """Displays the corresponding image for the clicked list item"""
        index = self.label_list.row(item)
        if index < len(self.preview_images):
            timestamp = self.timestamps[index]
            self.preview_label.setText(f"Preview of {timestamp}")
            self.update_preview_image()

    def update_preview_image(self):
        """Updates the preview image to ensure it resizes responsively"""
        if self.preview_images:
            pixmap = self.preview_images[-1].scaled(self.preview_image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
            self.preview_image_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        """Handle the resizing of the window to adjust thumbnail sizes, preview image, and select button."""
        super().resizeEvent(event)

        # Resize the preview image dynamically to take 50% of the right layout width
        right_layout_width = int(self.width() * 0.25)  # Ensure it's an integer for the scaled method

        # Resize the preview image based on the updated width
        pixmap = self.placeholder_pixmap.scaled(
            right_layout_width,
            self.preview_image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.preview_image_label.setPixmap(pixmap)

        # Get the available width for the thumbnails section
        available_width = self.width() * 0.4  # Use 40% of the window width for thumbnails
        num_columns = 4  # Number of columns in the grid layout

        # Calculate the new thumbnail size based on available width
        thumbnail_width = (available_width - (num_columns + 1) * 10) / num_columns  # Subtracting the spacing
        self.thumbnail_size = (thumbnail_width, thumbnail_width)  # Set width and height equal for square thumbnails

        # Update the size of the thumbnail buttons
        for row in range(self.thumbnail_layout.rowCount()):
            for col in range(self.thumbnail_layout.columnCount()):
                # Get the layout item in the grid and check if it exists
                item = self.thumbnail_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if isinstance(widget, QPushButton):
                        widget.setFixedSize(QSize(*self.thumbnail_size))  # Convert tuple to QSize

        # Resize the select button dynamically
        buttonSize = int(self.width() * 0.05)  # Set the size to 5% of the window width
        self.selectButton.setIconSize(QSize(buttonSize, buttonSize))  # Adjust icon size
        self.selectButton.setFixedSize(QSize(buttonSize, buttonSize))  # Adjust button size


        self.removeButton.setIconSize(QSize(buttonSize, buttonSize))  # Adjust icon size
        self.removeButton.setFixedSize(QSize(buttonSize, buttonSize))  # Adjust button size

        self.applyButton.setIconSize(QSize(buttonSize, buttonSize))
        self.applyButton.setFixedSize(QSize(buttonSize,buttonSize))

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ThumbnailWidget()
    widget.show()
    sys.exit(app.exec())
