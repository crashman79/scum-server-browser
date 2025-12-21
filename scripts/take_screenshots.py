#!/usr/bin/env python3
"""
Automated screenshot capture for SCUM Server Browser.
Captures screenshots in both light and dark themes for documentation.
"""
import sys
import os
import platform
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
from scum_tracker.ui.main_window import MainWindow
from scum_tracker.services.theme_service import ThemeService, Theme


class ScreenshotCapture:
    """Captures application screenshots in different themes."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("SCUM Server Browser")
        self.window = None
        self.screenshots_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Determine platform prefix
        self.platform_prefix = "win" if platform.system() == "Windows" else "linux"
        
        self.themes_to_capture = [
            (Theme.DARK, "dark"),
            (Theme.LIGHT, "light")
        ]
        self.current_theme_index = 0
    
    def capture_screenshot(self, theme: Theme, theme_name: str):
        """Capture a screenshot with the given theme."""
        print(f"Capturing {theme_name} theme screenshot...")
        
        # Apply theme
        theme_service = ThemeService()
        theme_service.save_theme(theme)
        self.app.setStyleSheet(theme_service.get_stylesheet())
        
        # Create and show window
        self.window = MainWindow()
        self.window.show()
        
        # Wait for window to render, then capture
        QTimer.singleShot(2000, lambda: self._take_screenshot(theme_name))
    
    def _take_screenshot(self, theme_name: str):
        """Take the actual screenshot after window is rendered."""
        try:
            # Grab the window contents
            pixmap = self.window.grab()
            
            # Save screenshot with platform-specific name
            filename = f"screenshot-{self.platform_prefix}-{theme_name}.png"
            filepath = self.screenshots_dir / filename
            
            if pixmap.save(str(filepath)):
                print(f"✓ Saved: {filepath}")
            else:
                print(f"✗ Failed to save: {filepath}")
            
            # Close window
            self.window.close()
            
            # Move to next theme or quit
            self.current_theme_index += 1
            if self.current_theme_index < len(self.themes_to_capture):
                QTimer.singleShot(500, self._capture_next)
            else:
                print("\n✓ All screenshots captured successfully!")
                QTimer.singleShot(100, self.app.quit)
                
        except Exception as e:
            print(f"✗ Error capturing screenshot: {e}")
            self.app.quit()
    
    def _capture_next(self):
        """Capture the next theme."""
        theme, theme_name = self.themes_to_capture[self.current_theme_index]
        self.capture_screenshot(theme, theme_name)
    
    def run(self):
        """Run the screenshot capture process."""
        print(f"SCUM Server Browser Screenshot Capture")
        print(f"Platform: {platform.system()}")
        print(f"Output directory: {self.screenshots_dir}")
        print(f"Capturing {len(self.themes_to_capture)} screenshots...\n")
        
        # Start with first theme
        theme, theme_name = self.themes_to_capture[self.current_theme_index]
        self.capture_screenshot(theme, theme_name)
        
        # Run application
        return self.app.exec()


def main():
    """Main entry point."""
    try:
        capture = ScreenshotCapture()
        sys.exit(capture.run())
    except KeyboardInterrupt:
        print("\n\nScreenshot capture cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
