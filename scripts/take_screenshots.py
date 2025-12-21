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
        print("  Creating QApplication...")
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("SCUM Server Browser")
        self.screenshots_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        print(f"  Screenshots directory: {self.screenshots_dir}")
        
        # Determine platform prefix
        self.platform_prefix = "win" if platform.system() == "Windows" else "linux"
        print(f"  Platform prefix: {self.platform_prefix}")
        
        self.themes_to_capture = [
            (Theme.DARK, "dark"),
            (Theme.LIGHT, "light")
        ]
        self.current_theme_index = 0
        print("  ScreenshotCapture initialized")
    
    def capture_screenshots(self):
        """Capture screenshots for all themes."""
        print("\nCreating MainWindow...")
        
        try:
            # Set screenshot mode
            os.environ['SCREENSHOT_MODE'] = '1'
            
            # Create window once
            self.window = MainWindow()
            self.window.show()
            
            # Wait for initial load, then start capturing
            print("Waiting for window to render and load...")
            QTimer.singleShot(5000, self._capture_current_theme)
            
        except Exception as e:
            print(f"✗ Error creating window: {e}")
            import traceback
            traceback.print_exc()
            self.app.exit(1)
    
    def _capture_current_theme(self):
        """Capture screenshot for current theme."""
        try:
            theme, theme_name = self.themes_to_capture[self.current_theme_index]
            print(f"\nCapturing {theme_name} theme screenshot...")
            
            # Apply theme by calling the window's theme setter
            print(f"  Applying {theme_name} theme...")
            self.window._set_theme(theme)
            
            # Wait a moment for theme to apply, then take screenshot
            QTimer.singleShot(1000, lambda: self._take_screenshot(theme_name))
            
        except Exception as e:
            print(f"✗ Error in _capture_current_theme: {e}")
            import traceback
            traceback.print_exc()
            self.app.exit(1)
    
    def _take_screenshot(self, theme_name: str):
        """Take the actual screenshot after window is rendered."""
        try:
            # Check if we're running offscreen (headless)
            is_offscreen = os.environ.get('QT_QPA_PLATFORM', '') in ['offscreen', 'minimal']
            
            if is_offscreen:
                # For offscreen rendering, render to pixmap directly
                from PyQt6.QtGui import QPixmap, QPainter
                
                # Get window size
                size = self.window.size()
                pixmap = QPixmap(size)
                
                # Render window to pixmap
                self.window.render(pixmap)
                print(f"  Rendered offscreen: {size.width()}x{size.height()}")
            else:
                # Normal window grab for platforms with display
                pixmap = self.window.grab()
            
            # Save screenshot with platform-specific name
            filename = f"screenshot-{self.platform_prefix}-{theme_name}.png"
            filepath = self.screenshots_dir / filename
            
            if pixmap.save(str(filepath)):
                print(f"✓ Saved: {filepath}")
            else:
                print(f"✗ Failed to save: {filepath}")
                raise Exception(f"Failed to save pixmap to {filepath}")
            
            # Move to next theme or quit
            self.current_theme_index += 1
            if self.current_theme_index < len(self.themes_to_capture):
                # Capture next theme on same window
                QTimer.singleShot(500, self._capture_current_theme)
            else:
                print("\n✓ All screenshots captured successfully!")
                # Close window and quit app
                self.window.close()
                QTimer.singleShot(100, self.app.quit)
                
        except Exception as e:
            print(f"✗ Error capturing screenshot: {e}")
            import traceback
            traceback.print_exc()
            self.app.exit(1)
    
    def run(self):
        """Run the screenshot capture process."""
        print(f"SCUM Server Browser Screenshot Capture")
        print(f"Platform: {platform.system()}")
        print(f"QT_QPA_PLATFORM: {os.environ.get('QT_QPA_PLATFORM', 'default')}")
        print(f"Output directory: {self.screenshots_dir}")
        print(f"Capturing {len(self.themes_to_capture)} screenshots...\n")
        
        # Start capturing
        self.capture_screenshots()
        
        # Run application
        return self.app.exec()


def main():
    """Main entry point."""
    print("Starting screenshot capture script...")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()}")
    print(f"QT_QPA_PLATFORM: {os.environ.get('QT_QPA_PLATFORM', 'not set')}")
    
    try:
        print("\nInitializing ScreenshotCapture...")
        capture = ScreenshotCapture()
        print("Running capture...")
        result = capture.run()
        print(f"Capture completed with result: {result}")
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n\nScreenshot capture cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
