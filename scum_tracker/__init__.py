"""
SCUM Server Tracker - Main Application
"""
import sys
import os
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from scum_tracker.ui.main_window import MainWindow
from scum_tracker.services.theme_service import ThemeService


def _init_windows_optimizations():
    """Initialize Windows-specific optimizations for better performance"""
    if platform.system() == 'Windows':
        try:
            # Enable DPI awareness for sharper rendering on high-DPI displays
            import ctypes
            try:
                # Try to set DPI awareness (Windows 8.1+)
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                try:
                    # Fallback for older Windows versions
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            # Optimize socket performance on Windows
            import socket
            if hasattr(socket, 'setdefaulttimeout'):
                # Set a reasonable default timeout for all sockets
                socket.setdefaulttimeout(10)
                
        except Exception as e:
            print(f"Windows optimization warning: {e}")


def main():
    # Apply Windows-specific optimizations early
    _init_windows_optimizations()
    
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
