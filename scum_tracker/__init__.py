"""
SCUM Server Tracker - Main Application
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from scum_tracker.ui.main_window import MainWindow
from scum_tracker.services.theme_service import ThemeService


def main():
    app = QApplication(sys.argv)
    
    # Set application name and icon for taskbar and window manager
    app.setApplicationName("SCUM Server Browser")
    app.setApplicationDisplayName("SCUM Server Browser")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon for taskbar
    icon_path = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "app_icon.png"
    )
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    # Initialize and apply theme
    theme_service = ThemeService()
    theme_service.apply_theme(app)
    
    window = MainWindow()
    
    # Set window class for Linux window manager (fixes taskbar metadata)
    if hasattr(window, 'winId'):
        window.setWindowTitle("SCUM Server Browser")
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
