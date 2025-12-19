"""Theme management service for light/dark/system theming."""
from enum import Enum
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSettings


class Theme(Enum):
    """Available theme options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeService:
    """Manages application theming."""
    
    LIGHT_STYLESHEET = """
    QMainWindow {
        background-color: #ffffff;
        color: #000000;
    }
    QWidget {
        background-color: #ffffff;
        color: #000000;
    }
    QTableWidget {
        background-color: #ffffff;
        color: #000000;
        gridline-color: #cccccc;
    }
    QTableWidget::item {
        background-color: #ffffff;
        color: #000000;
        padding: 2px;
    }
    QTableWidget::item:selected {
        background-color: #0078d4;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #f0f0f0;
        color: #000000;
        padding: 5px;
        border: 1px solid #cccccc;
    }
    QPushButton {
        background-color: #e1e1e1;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 3px 8px;
    }
    QPushButton:hover {
        background-color: #d0d0d0;
    }
    QPushButton:pressed {
        background-color: #b0b0b0;
    }
    QLineEdit {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 5px;
    }
    QSpinBox {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 5px;
    }
    QCheckBox {
        color: #000000;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    QCheckBox::indicator:unchecked {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 3px;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTUgNUw3IDEzTDMgOSIgc3Ryb2tlPSIjMDBBQTAwIiBzdHJva2Utd2lkdGg9IjIuNSIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
        background-repeat: no-repeat;
        background-position: center;
    }
    QGroupBox {
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    QScrollArea {
        background-color: #ffffff;
    }
    QLabel {
        color: #000000;
    }
    QDialog {
        background-color: #ffffff;
    }
    """
    
    DARK_STYLESHEET = """
    QMainWindow {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    QWidget {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    QTableWidget {
        background-color: #1e1e1e;
        color: #ffffff;
        gridline-color: #444444;
    }
    QTableWidget::item {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 2px;
    }
    QTableWidget::item:selected {
        background-color: #0078d4;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #3d3d3d;
        color: #ffffff;
        padding: 5px;
        border: 1px solid #444444;
    }
    QPushButton {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 3px 8px;
    }
    QPushButton:hover {
        background-color: #4d4d4d;
    }
    QPushButton:pressed {
        background-color: #5d5d5d;
    }
    QLineEdit {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 5px;
    }
    QSpinBox {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 5px;
    }
    QCheckBox {
        color: #ffffff;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    QCheckBox::indicator:unchecked {
        background-color: #3d3d3d;
        border: 1px solid #555555;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #3d3d3d;
        border: 1px solid #555555;
        border-radius: 3px;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTUgNUw3IDEzTDMgOSIgc3Ryb2tlPSIjNENDQTUwIiBzdHJva2Utd2lkdGg9IjIuNSIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
        background-repeat: no-repeat;
        background-position: center;
    }
    QGroupBox {
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    QScrollArea {
        background-color: #2d2d2d;
    }
    QLabel {
        color: #ffffff;
    }
    QDialog {
        background-color: #2d2d2d;
    }
    """
    
    def __init__(self):
        """Initialize theme service."""
        self.settings = QSettings("SCUM", "ServerTracker")
        self.current_theme = self._load_theme()
    
    def _load_theme(self) -> Theme:
        """Load saved theme preference."""
        theme_value = self.settings.value("theme", Theme.SYSTEM.value)
        try:
            return Theme(theme_value)
        except ValueError:
            return Theme.SYSTEM
    
    def save_theme(self, theme: Theme) -> None:
        """Save theme preference."""
        self.settings.setValue("theme", theme.value)
        self.current_theme = theme
    
    def get_stylesheet(self) -> str:
        """Get the appropriate stylesheet based on current theme."""
        if self.current_theme == Theme.LIGHT:
            return self.LIGHT_STYLESHEET
        elif self.current_theme == Theme.DARK:
            return self.DARK_STYLESHEET
        else:  # SYSTEM
            # Detect system theme using darkdetect
            import darkdetect
            try:
                is_dark = darkdetect.isDark()
                return self.DARK_STYLESHEET if is_dark else self.LIGHT_STYLESHEET
            except Exception:
                # Fallback to light if detection fails
                return self.LIGHT_STYLESHEET
    
    def apply_theme(self, app) -> None:
        """Apply theme to the application."""
        stylesheet = self.get_stylesheet()
        app.setStyleSheet(stylesheet)
