"""
Desktop integration for Linux systems
Creates .desktop files and installs icons for application menu integration
"""
import os
import sys
import platform
import shutil
from pathlib import Path


class DesktopIntegration:
    """Handle desktop environment integration on Linux"""
    
    def __init__(self):
        self.home = Path.home()
        self.local_share = self.home / ".local" / "share"
        self.bin_dir = self.home / ".local" / "bin"
        self.desktop_dir = self.local_share / "applications"
        self.icon_dir = self.local_share / "icons" / "hicolor"
        
    def is_linux(self):
        """Check if running on Linux"""
        return platform.system() == "Linux"
    
    def is_installed(self):
        """Check if desktop entry already exists"""
        desktop_file = self.desktop_dir / "scum-server-browser.desktop"
        return desktop_file.exists()
    
    def get_executable_path(self):
        """Get the path to the current executable or script"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            return Path(sys.executable).resolve()
        else:
            # Running as script
            return Path(sys.argv[0]).resolve()
    
    def get_icon_path(self):
        """Get the path to the application icon"""
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle - icon is in _internal
            base_path = Path(sys._MEIPASS)
        else:
            # Running from source
            base_path = Path(__file__).parent.parent
        
        icon_path = base_path / "scum_tracker" / "assets" / "app_icon.png"
        return icon_path if icon_path.exists() else None
    
    def install_desktop_entry(self):
        """Create desktop entry and install icon"""
        if not self.is_linux():
            return False, "Desktop integration is only supported on Linux"
        
        try:
            # Create necessary directories
            self.desktop_dir.mkdir(parents=True, exist_ok=True)
            self.bin_dir.mkdir(parents=True, exist_ok=True)
            
            exe_path = self.get_executable_path()
            icon_path = self.get_icon_path()
            
            # Install icon if available
            if icon_path and icon_path.exists():
                icon_sizes = [48, 64, 128, 256]
                for size in icon_sizes:
                    icon_dest_dir = self.icon_dir / f"{size}x{size}" / "apps"
                    icon_dest_dir.mkdir(parents=True, exist_ok=True)
                    icon_dest = icon_dest_dir / "scum-server-browser.png"
                    
                    # Copy icon (we'll use the same icon for all sizes for now)
                    shutil.copy2(icon_path, icon_dest)
            
            # Create symlink in bin directory for command-line access
            bin_link = self.bin_dir / "scum-server-browser"
            if bin_link.exists() or bin_link.is_symlink():
                bin_link.unlink()
            bin_link.symlink_to(exe_path)
            
            # Create .desktop file
            # Set working directory to executable's directory
            working_dir = exe_path.parent
            
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SCUM Server Browser
Comment=Track and ping SCUM game servers with real-time latency monitoring
Exec={exe_path}
Path={working_dir}
Icon=scum-server-browser
Terminal=false
Categories=Game;Network;
Keywords=scum;server;browser;game;ping;
StartupWMClass=scum_tracker
"""
            desktop_file = self.desktop_dir / "scum-server-browser.desktop"
            desktop_file.write_text(desktop_content)
            # Desktop files should be readable, not executable (0o644)
            desktop_file.chmod(0o644)
            
            # Update desktop database
            self._update_desktop_database()
            self._update_icon_cache()
            
            return True, "Desktop entry created successfully!\n\nThe application is now available in your application menu (Games category).\nYou can also run 'scum-server-browser' from the terminal."
            
        except Exception as e:
            return False, f"Failed to create desktop entry: {str(e)}"
    
    def uninstall_desktop_entry(self):
        """Remove desktop entry and icon"""
        if not self.is_linux():
            return False, "Desktop integration is only supported on Linux"
        
        try:
            # Remove desktop file
            desktop_file = self.desktop_dir / "scum-server-browser.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            
            # Remove symlink
            bin_link = self.bin_dir / "scum-server-browser"
            if bin_link.exists() or bin_link.is_symlink():
                bin_link.unlink()
            
            # Remove icons
            icon_sizes = [48, 64, 128, 256]
            for size in icon_sizes:
                icon_file = self.icon_dir / f"{size}x{size}" / "apps" / "scum-server-browser.png"
                if icon_file.exists():
                    icon_file.unlink()
            
            # Update desktop database
            self._update_desktop_database()
            self._update_icon_cache()
            
            return True, "Desktop entry removed successfully!"
            
        except Exception as e:
            return False, f"Failed to remove desktop entry: {str(e)}"
    
    def _update_desktop_database(self):
        """Update the desktop database cache"""
        try:
            import subprocess
            subprocess.run(
                ['update-desktop-database', str(self.desktop_dir)],
                capture_output=True,
                timeout=5
            )
            # KDE-specific: rebuild system configuration cache
            # Try KDE6 first, then KDE5
            for cmd in ['kbuildsycoca6', 'kbuildsycoca5']:
                try:
                    subprocess.run([cmd], capture_output=True, timeout=10)
                    break
                except:
                    continue
        except:
            pass  # Not critical if this fails
    
    def _update_icon_cache(self):
        """Update the icon cache"""
        try:
            import subprocess
            subprocess.run(
                ['gtk-update-icon-cache', '-f', '-t', str(self.icon_dir)],
                capture_output=True,
                timeout=5
            )
        except:
            pass  # Not critical if this fails
