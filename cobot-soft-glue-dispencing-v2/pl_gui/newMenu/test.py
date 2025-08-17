import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGridLayout, QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect,
                             QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, QMimeData, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QFont, QPalette, QColor, QIcon


# PL Project Industrial Design System - Purple & Light Blue Edition
# Inspired by luxury leather machinery manufacturing with modern purple gradients
# Professional, technological, and sophisticated design with purple-blue harmony

class PLProjectDesignTokens:
    """PL Project Design System Tokens - Purple & Light Blue Theme

    Modern industrial design system that perfectly complements purple gradient icons
    while maintaining professional sophistication for luxury leather machinery
    """

    # Primary Brand Colors - Purple Innovation
    PRIMARY_PURPLE = "#6B46C1"  # Rich purple (matches icon gradients)
    PRIMARY_PURPLE_HOVER = "#8B5CF6"  # Lighter purple for hover states
    PRIMARY_PURPLE_PRESSED = "#553C9A"  # Darker purple for pressed states

    # Secondary Colors - Light Blue Precision
    LIGHT_BLUE = "#3B82F6"  # Professional light blue
    LIGHT_BLUE_HOVER = "#60A5FA"  # Lighter blue for hover states
    LIGHT_BLUE_PRESSED = "#2563EB"  # Medium blue for pressed states

    # Accent Colors - Purple Gradients
    LAVENDER_LIGHT = "#A78BFA"  # Light lavender accent
    VIOLET_MEDIUM = "#8B5CF6"  # Medium violet
    INDIGO_DEEP = "#4F46E5"  # Deep indigo

    # Luxury Tones - Updated for Purple Theme
    PURPLE_GRAY = "#6B7280"  # Purple-tinted gray
    SILVER_PURPLE = "#C7D2FE"  # Purple-tinted silver
    COPPER_PURPLE = "#A855F7"  # Purple-copper blend

    # Surface Colors - Modern Purple-Blue Theme
    SURFACE_WHITE = "#FEFEFE"  # Pure white surface
    SURFACE_LIGHT = "#F8FAFC"  # Light purple-blue tinted surface
    SURFACE_MEDIUM = "#E2E8F0"  # Medium gray surface
    SURFACE_PURPLE = "#F3F4F6"  # Purple-tinted surface
    SURFACE_DARK = "#1E293B"  # Dark surface with blue undertones

    # Text Colors - Purple-Blue Harmony
    TEXT_PRIMARY = "#1E1B4B"  # Deep purple-blue text
    TEXT_SECONDARY = "#6B7280"  # Purple-gray secondary text
    TEXT_TERTIARY = "#9CA3AF"  # Light gray tertiary text
    TEXT_WHITE = "#FFFFFF"  # White text for dark backgrounds
    TEXT_PURPLE = "#6B46C1"  # Purple accent text

    # Status Colors - Purple-Blue System
    SUCCESS_GREEN = "#10B981"  # Success/operational status
    WARNING_AMBER = "#F59E0B"  # Warning/maintenance status
    ERROR_ROSE = "#EF4444"  # Error/fault status
    INFO_PURPLE = "#8B5CF6"  # Information status (purple theme)

    # Typography - Industrial & Technical
    FONT_PRIMARY = "Roboto Condensed"  # Technical, industrial feel
    FONT_SECONDARY = "Open Sans"  # Clean, readable
    FONT_MONO = "Roboto Mono"  # Technical specifications

    # Spacing Scale - Precision Manufacturing
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 16
    SPACE_LG = 24
    SPACE_XL = 32
    SPACE_XXL = 48

    # Border Radius - Industrial Aesthetics
    RADIUS_SM = 4  # Small components
    RADIUS_MD = 8  # Standard components
    RADIUS_LG = 12  # Large components
    RADIUS_XL = 16  # Container components

    # Shadows - Modern Purple-Blue Depth
    SHADOW_SM = "0px 1px 3px rgba(107, 70, 193, 0.12)"
    SHADOW_MD = "0px 4px 12px rgba(107, 70, 193, 0.15)"
    SHADOW_LG = "0px 8px 24px rgba(107, 70, 193, 0.18)"
    SHADOW_XL = "0px 16px 48px rgba(107, 70, 193, 0.20)"


class PLProjectMenuIcon(QPushButton):
    """PL Project styled app icon for industrial machinery interface"""

    button_clicked = pyqtSignal(str)

    def __init__(self, icon_label, icon_path, icon_text="⚙️", callback=None, style_variant="primary", parent=None):
        super().__init__(parent)
        self.icon_label = icon_label
        self.icon_path = icon_path
        self.icon_text = icon_text
        self.callback = callback
        self.style_variant = style_variant

        # Industrial machinery standard size
        self.setFixedSize(120, 120)
        self.setup_ui()
        self.setup_animations()

        if self.callback is not None:
            self.button_clicked.connect(self.callback)

    def setup_ui(self):
        """Setup PL Project industrial styling"""

        style_variants = {
            "primary": {
                "background": PLProjectDesignTokens.PRIMARY_PURPLE,
                "hover": PLProjectDesignTokens.PRIMARY_PURPLE_HOVER,
                "pressed": PLProjectDesignTokens.PRIMARY_PURPLE_PRESSED,
                "text_color": PLProjectDesignTokens.TEXT_WHITE,
                "border": "none"
            },
            "light_blue": {
                "background": PLProjectDesignTokens.LIGHT_BLUE,
                "hover": PLProjectDesignTokens.LIGHT_BLUE_HOVER,
                "pressed": PLProjectDesignTokens.LIGHT_BLUE_PRESSED,
                "text_color": PLProjectDesignTokens.TEXT_WHITE,
                "border": "none"
            },
            "lavender": {
                "background": PLProjectDesignTokens.LAVENDER_LIGHT,
                "hover": PLProjectDesignTokens.VIOLET_MEDIUM,
                "pressed": PLProjectDesignTokens.PRIMARY_PURPLE,
                "text_color": PLProjectDesignTokens.TEXT_WHITE,
                "border": "none"
            },
            "outlined": {
                "background": PLProjectDesignTokens.SURFACE_WHITE,
                "hover": PLProjectDesignTokens.SURFACE_PURPLE,
                "pressed": PLProjectDesignTokens.SURFACE_MEDIUM,
                "text_color": PLProjectDesignTokens.PRIMARY_PURPLE,
                "border": f"2px solid {PLProjectDesignTokens.PRIMARY_PURPLE}"
            }
        }

        scheme = style_variants.get(self.style_variant, style_variants["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background: {scheme['background']};
                color: {scheme['text_color']};
                {scheme['border']};
                border-radius: {PLProjectDesignTokens.RADIUS_LG}px;
                font-size: 13px;
                font-weight: 600;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                text-align: center;
                padding: {PLProjectDesignTokens.SPACE_MD}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: {scheme['hover']};
            }}
            QPushButton:pressed {{
                background: {scheme['pressed']};
            }}
            QPushButton:disabled {{
                background: {PLProjectDesignTokens.SURFACE_MEDIUM};
                color: {PLProjectDesignTokens.TEXT_TERTIARY};
                border: 1px solid {PLProjectDesignTokens.SURFACE_MEDIUM};
            }}
        """)

        # Modern purple-tinted shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(107, 70, 193, 40))  # Purple shadow
            shadow.setOffset(0, 4)
            self.setGraphicsEffect(shadow)
        except:
            pass

        self.setup_icon_content()
        self.setToolTip(self.icon_label)

    def setup_icon_content(self):
        """Setup icon with industrial machinery focus"""

        if self.icon_path and os.path.exists(self.icon_path):
            try:
                icon = QIcon(self.icon_path)
                if not icon.isNull():
                    self.setIcon(icon)
                    icon_size = int(self.width() * 0.55)  # Larger for machinery icons
                    self.setIconSize(QSize(icon_size, icon_size))
                    self.setText("")
                    return
            except Exception as e:
                print(f"Error loading icon: {e}")

        # Fallback with industrial iconography
        self.setup_fallback_text()

    def setup_fallback_text(self):
        """Setup fallback with industrial abbreviations"""

        if self.icon_text and self.icon_text not in ["⚙️", ""]:
            display_text = self.icon_text
        else:
            # Create industrial-style abbreviations
            words = self.icon_label.split()
            if len(words) >= 2:
                display_text = ''.join(word[0].upper() for word in words[:2])
            else:
                display_text = self.icon_label[:2].upper()

        self.setText(display_text)

        # Adjust font for industrial feel
        font_size = 18 if len(display_text) <= 2 else 14

        self.setStyleSheet(self.styleSheet() + f"""
            QPushButton {{
                font-size: {font_size}px;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
        """)

    def setup_animations(self):
        """Setup precision industrial animations"""
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(120)  # Precise, quick response
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def mousePressEvent(self, event):
        """Industrial press feedback"""
        if event.button() == Qt.MouseButton.LeftButton:
            current_rect = self.geometry()
            scale_factor = 0.96  # Subtle industrial feedback

            new_width = int(current_rect.width() * scale_factor)
            new_height = int(current_rect.height() * scale_factor)
            new_x = current_rect.x() + (current_rect.width() - new_width) // 2
            new_y = current_rect.y() + (current_rect.height() - new_height) // 2

            scaled_rect = QRect(new_x, new_y, new_width, new_height)

            self.scale_animation.setStartValue(current_rect)
            self.scale_animation.setEndValue(scaled_rect)
            self.scale_animation.start()

            self.button_clicked.emit(self.icon_label)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Restore with precision timing"""
        if event.button() == Qt.MouseButton.LeftButton:
            original_rect = self.geometry()
            scale_factor = 1.0 / 0.96

            new_width = int(original_rect.width() * scale_factor)
            new_height = int(original_rect.height() * scale_factor)
            new_x = original_rect.x() - (new_width - original_rect.width()) // 2
            new_y = original_rect.y() - (new_height - original_rect.height()) // 2

            restored_rect = QRect(new_x, new_y, new_width, new_height)

            self.scale_animation.setStartValue(original_rect)
            self.scale_animation.setEndValue(restored_rect)
            self.scale_animation.start()

        super().mouseReleaseEvent(event)


class PLProjectFolder(QFrame):
    """PL Project industrial machinery folder container"""

    folder_opened = pyqtSignal(object)
    folder_closed = pyqtSignal()
    app_selected = pyqtSignal(str)

    def __init__(self, folder_name="Industrial Apps", parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.buttons = []
        self.setup_ui()

    def setup_ui(self):
        """Setup industrial folder styling"""
        self.setFixedSize(340, 400)

        # Modern purple-blue industrial aesthetic
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PLProjectDesignTokens.SURFACE_WHITE},
                    stop:1 {PLProjectDesignTokens.SURFACE_PURPLE});
                border: 2px solid {PLProjectDesignTokens.PRIMARY_PURPLE};
                border-radius: {PLProjectDesignTokens.RADIUS_LG}px;
            }}
        """)

        # Professional purple-tinted shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(107, 70, 193, 25))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG
        )
        main_layout.setSpacing(PLProjectDesignTokens.SPACE_MD)

        # Industrial preview area
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background: {PLProjectDesignTokens.SURFACE_WHITE};
                border: 1px solid {PLProjectDesignTokens.SURFACE_MEDIUM};
                border-radius: {PLProjectDesignTokens.RADIUS_MD}px;
            }}
        """)

        preview_shadow = QGraphicsDropShadowEffect()
        preview_shadow.setBlurRadius(8)
        preview_shadow.setColor(QColor(107, 70, 193, 15))
        preview_shadow.setOffset(0, 2)
        self.preview_frame.setGraphicsEffect(preview_shadow)

        self.preview_layout = QGridLayout(self.preview_frame)
        self.preview_layout.setSpacing(PLProjectDesignTokens.SPACE_SM)
        self.preview_layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_MD,
            PLProjectDesignTokens.SPACE_MD,
            PLProjectDesignTokens.SPACE_MD,
            PLProjectDesignTokens.SPACE_MD
        )

        # Modern purple typography for title
        self.title_label = QLabel(self.folder_name)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {PLProjectDesignTokens.PRIMARY_PURPLE};
                font-size: 20px;
                font-weight: 700;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                background: transparent;
                padding: {PLProjectDesignTokens.SPACE_SM}px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)

        main_layout.addWidget(self.preview_frame, 1)
        main_layout.addWidget(self.title_label, 0)

        self.update_preview()

    def add_app(self, app_name, icon_path="", callback=None, style_variant="primary"):
        """Add app with PL Project industrial styling"""
        app_icon = PLProjectMenuIcon(app_name, icon_path, "", callback, style_variant)
        self.buttons.append(app_icon)
        self.update_preview()

    def update_preview(self):
        """Update preview with industrial mini icons"""
        # Clear existing
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Show up to 4 apps in industrial grid
        preview_apps = self.buttons[:4]
        for i, app in enumerate(preview_apps):
            row = i // 2
            col = i % 2

            # Industrial mini icon
            mini_icon = QLabel()
            mini_icon.setFixedSize(70, 70)
            mini_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            mini_icon.setStyleSheet(f"""
                QLabel {{
                    background: {PLProjectDesignTokens.PRIMARY_PURPLE};
                    border: 1px solid {PLProjectDesignTokens.PRIMARY_PURPLE_HOVER};
                    border-radius: {PLProjectDesignTokens.RADIUS_SM}px;
                    font-size: 11px;
                    font-weight: 600;
                    color: {PLProjectDesignTokens.TEXT_WHITE};
                    font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            """)

            # Load icon or use abbreviation
            if hasattr(app, 'icon_path') and app.icon_path and os.path.exists(app.icon_path):
                try:
                    pixmap = QPixmap(app.icon_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)
                        mini_icon.setPixmap(scaled_pixmap)
                    else:
                        mini_icon.setText(app.icon_label[:2].upper())
                except:
                    mini_icon.setText(app.icon_label[:2].upper())
            else:
                mini_icon.setText(app.icon_label[:2].upper())

            self.preview_layout.addWidget(mini_icon, row, col)


class PLProjectNavigationBar(QFrame):
    """PL Project industrial navigation bar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup industrial navigation styling"""
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PLProjectDesignTokens.PRIMARY_PURPLE},
                    stop:1 {PLProjectDesignTokens.LIGHT_BLUE});
                border-bottom: 3px solid {PLProjectDesignTokens.PURPLE_GRAY};
            }}
        """)

        # Modern purple-blue shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(107, 70, 193, 30))
            shadow.setOffset(0, 4)
            self.setGraphicsEffect(shadow)
        except:
            pass

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_MD,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_MD
        )

        # Company branding
        title_layout = QVBoxLayout()

        main_title = QLabel("PL PROJECT")
        main_title.setStyleSheet(f"""
            QLabel {{
                color: {PLProjectDesignTokens.TEXT_WHITE};
                font-size: 28px;
                font-weight: 900;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                background: transparent;
                border: none;
                letter-spacing: 2px;
                text-transform: uppercase;
            }}
        """)

        subtitle = QLabel("Industrial Machinery Control System")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {PLProjectDesignTokens.SILVER_PURPLE};
                font-size: 12px;
                font-weight: 500;
                font-family: '{PLProjectDesignTokens.FONT_SECONDARY}', 'Open Sans', sans-serif;
                background: transparent;
                border: none;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: -5px;
            }}
        """)

        title_layout.addWidget(main_title)
        title_layout.addWidget(subtitle)
        title_layout.setSpacing(0)

        layout.addLayout(title_layout)
        layout.addStretch()


class PLProjectAppWidget(QWidget):
    """PL Project industrial application widget"""

    app_closed = pyqtSignal()

    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.setup_ui()

    def setup_ui(self):
        """Setup industrial app interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Industrial app header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QFrame {{
                background: {PLProjectDesignTokens.SURFACE_DARK};
                border-bottom: 2px solid {PLProjectDesignTokens.PURPLE_GRAY};
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_MD,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_MD
        )

        # App title
        app_title = QLabel(f"{self.app_name} - Industrial Control Interface")
        app_title.setStyleSheet(f"""
            QLabel {{
                color: {PLProjectDesignTokens.TEXT_WHITE};
                font-size: 20px;
                font-weight: 600;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)

        # Back button with new purple styling
        back_button = QPushButton("← RETURN TO MAIN")
        back_button.setFixedSize(160, 40)
        back_button.setStyleSheet(f"""
            QPushButton {{
                background: {PLProjectDesignTokens.PURPLE_GRAY};
                color: {PLProjectDesignTokens.TEXT_WHITE};
                border: 1px solid {PLProjectDesignTokens.SILVER_PURPLE};
                border-radius: {PLProjectDesignTokens.RADIUS_SM}px;
                font-size: 12px;
                font-weight: 600;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: {PLProjectDesignTokens.PRIMARY_PURPLE};
                border: 1px solid {PLProjectDesignTokens.PRIMARY_PURPLE_HOVER};
            }}
            QPushButton:pressed {{
                background: {PLProjectDesignTokens.PRIMARY_PURPLE_PRESSED};
            }}
        """)
        back_button.clicked.connect(self.app_closed.emit)

        header_layout.addWidget(app_title)
        header_layout.addStretch()
        header_layout.addWidget(back_button)

        # Main application content
        content = QLabel(
            f"PL PROJECT - {self.app_name}\n\n"
            "INDUSTRIAL MACHINERY CONTROL SYSTEM\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• Advanced edge dyeing process control\n"
            "• Magnetic drive technology interface\n"
            "• Smart energy management system\n"
            "• Real-time operational monitoring\n"
            "• Quality assurance protocols\n\n"
            "STATUS: OPERATIONAL\n"
            "SYSTEM: READY\n\n"
            "Click RETURN TO MAIN to exit this application interface."
        )
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setStyleSheet(f"""
            QLabel {{
                background: {PLProjectDesignTokens.SURFACE_WHITE};
                border: 1px solid {PLProjectDesignTokens.SURFACE_MEDIUM};
                border-radius: {PLProjectDesignTokens.RADIUS_MD}px;
                padding: {PLProjectDesignTokens.SPACE_XXL}px;
                font-size: 16px;
                color: {PLProjectDesignTokens.TEXT_PRIMARY};
                font-family: '{PLProjectDesignTokens.FONT_MONO}', 'Roboto Mono', monospace;
                line-height: 1.6;
            }}
        """)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_LG
        )
        content_layout.addWidget(content)

        layout.addWidget(header)
        layout.addWidget(content_container)


class PLProjectDemo(QWidget):
    """PL Project industrial machinery interface demo"""

    def __init__(self):
        super().__init__()
        self.folders = []
        self.current_running_app = None
        self.current_app_folder = None
        self.stacked_widget = None
        self.folder_page = None
        self.setup_ui()

    def setup_ui(self):
        """Setup industrial interface"""
        self.setWindowTitle("PL PROJECT - Industrial Machinery Control System")
        self.resize(1400, 1000)
        self.center_on_screen()

        # Modern purple-blue background
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PLProjectDesignTokens.SURFACE_LIGHT},
                    stop:1 {PLProjectDesignTokens.SURFACE_PURPLE});
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Industrial navigation
        self.nav_bar = PLProjectNavigationBar()
        main_layout.addWidget(self.nav_bar)

        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.create_folder_page()

    def create_folder_page(self):
        """Create industrial folder interface"""
        self.folder_page = QWidget()
        self.folder_page.setStyleSheet("background: transparent;")

        page_layout = QVBoxLayout(self.folder_page)
        page_layout.setContentsMargins(
            PLProjectDesignTokens.SPACE_XXL,
            PLProjectDesignTokens.SPACE_LG,
            PLProjectDesignTokens.SPACE_XXL,
            PLProjectDesignTokens.SPACE_XXL
        )
        page_layout.setSpacing(PLProjectDesignTokens.SPACE_LG)

        # System status header
        status_label = QLabel("INDUSTRIAL MACHINERY CONTROL SYSTEMS")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {PLProjectDesignTokens.PRIMARY_PURPLE};
                font-size: 32px;
                font-weight: 700;
                font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
                background: transparent;
                margin-bottom: {PLProjectDesignTokens.SPACE_MD}px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """)
        page_layout.addWidget(status_label)

        # Industrial folder grid
        self.create_industrial_folders(page_layout)

        self.stacked_widget.addWidget(self.folder_page)

    def create_industrial_folders(self, parent_layout):
        """Create industrial machinery folders"""

        # Production Line Control
        production_folder = PLProjectFolder("Production Line")
        production_folder.add_app("Edge Dyeing Control", "", self.on_app_selected, "primary")
        production_folder.add_app("Magnetic Drive System", "", self.on_app_selected, "light_blue")
        production_folder.add_app("Smart Energy Manager", "", self.on_app_selected, "lavender")
        production_folder.add_app("Quality Control", "", self.on_app_selected, "outlined")

        # Maintenance Systems
        maintenance_folder = PLProjectFolder("Maintenance")
        maintenance_folder.add_app("Preventive Maintenance", "", self.on_app_selected, "light_blue")
        maintenance_folder.add_app("Diagnostic Tools", "", self.on_app_selected, "primary")
        maintenance_folder.add_app("Calibration System", "", self.on_app_selected, "lavender")

        # Operations Management
        operations_folder = PLProjectFolder("Operations")
        operations_folder.add_app("Production Planning", "", self.on_app_selected, "primary")
        operations_folder.add_app("Inventory Management", "", self.on_app_selected, "light_blue")
        operations_folder.add_app("Order Processing", "", self.on_app_selected, "lavender")
        operations_folder.add_app("Reporting System", "", self.on_app_selected, "outlined")

        # System Administration
        admin_folder = PLProjectFolder("Administration")
        admin_folder.add_app("User Management", "", self.on_app_selected, "light_blue")
        admin_folder.add_app("System Settings", "", self.on_app_selected, "primary")
        admin_folder.add_app("Security Control", "", self.on_app_selected, "lavender")

        self.folders = [production_folder, maintenance_folder, operations_folder, admin_folder]

        # Configure folders
        for folder in self.folders:
            folder.app_selected.connect(self.on_app_selected)

        # Grid layout for folders
        grid_layout = QGridLayout()
        grid_layout.setSpacing(PLProjectDesignTokens.SPACE_LG)

        grid_layout.addWidget(self.folders[0], 0, 0)  # Production
        grid_layout.addWidget(self.folders[1], 0, 1)  # Maintenance
        grid_layout.addWidget(self.folders[2], 1, 0)  # Operations
        grid_layout.addWidget(self.folders[3], 1, 1)  # Administration

        grid_container = QWidget()
        grid_container.setLayout(grid_layout)

        parent_layout.addWidget(grid_container, 0, Qt.AlignmentFlag.AlignCenter)
        parent_layout.addStretch()

    def on_app_selected(self, app_name):
        """Handle industrial app selection"""
        print(f"PL Project: {app_name} system activated")

        self.current_running_app = app_name

        # Create industrial app widget
        app_widget = PLProjectAppWidget(app_name)
        app_widget.app_closed.connect(self.close_current_app)

        # Update stacked widget
        if self.stacked_widget.count() > 1:
            old_app = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(old_app)
            old_app.deleteLater()

        self.stacked_widget.addWidget(app_widget)
        self.stacked_widget.setCurrentIndex(1)

    def close_current_app(self):
        """Close industrial app and return to main"""
        if self.current_running_app:
            print(f"PL Project: Closing {self.current_running_app} system")

            self.stacked_widget.setCurrentIndex(0)

            if self.stacked_widget.count() > 1:
                app_widget = self.stacked_widget.widget(1)
                self.stacked_widget.removeWidget(app_widget)
                app_widget.deleteLater()

            self.current_running_app = None

    def center_on_screen(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def keyPressEvent(self, event):
        """Handle key events"""
        if event.key() == Qt.Key.Key_Escape and self.current_running_app:
            self.close_current_app()
        super().keyPressEvent(event)


def main():
    """Main function for PL Project industrial interface"""
    app = QApplication(sys.argv)

    app.setStyle('Fusion')

    # Industrial typography
    font = QFont(PLProjectDesignTokens.FONT_PRIMARY, 10)
    if not font.exactMatch():
        font = QFont("Roboto", 10)
    app.setFont(font)

    # Industrial application styling with purple theme
    app.setStyleSheet(f"""
        QApplication {{
            background: {PLProjectDesignTokens.SURFACE_LIGHT};
            color: {PLProjectDesignTokens.TEXT_PRIMARY};
            font-family: '{PLProjectDesignTokens.FONT_PRIMARY}', 'Roboto', sans-serif;
        }}

        QToolTip {{
            background: {PLProjectDesignTokens.SURFACE_DARK};
            color: {PLProjectDesignTokens.TEXT_WHITE};
            border: 1px solid {PLProjectDesignTokens.PURPLE_GRAY};
            border-radius: {PLProjectDesignTokens.RADIUS_SM}px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: '{PLProjectDesignTokens.FONT_SECONDARY}', 'Open Sans', sans-serif;
        }}
    """)

    # Create and show PL Project demo
    demo = PLProjectDemo()
    demo.show()

    print("PL PROJECT - Industrial Machinery Control System")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("• Click any folder to access industrial systems")
    print("• Select applications to launch control interfaces")
    print("• Use RETURN TO MAIN to exit applications")
    print("• Press ESC for emergency system shutdown")
    print("• Professional industrial interface design")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()