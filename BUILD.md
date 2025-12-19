# Building SCUM Server Browser Standalone Executables

This guide explains how to create self-contained, cross-platform executables of SCUM Server Browser that require no Python installation.

## Prerequisites

- Python 3.9+
- Virtual environment created: `python3 -m venv .venv`
- Dependencies installed: `pip install -r requirements.txt`

## Building for Linux

### Quick Build

```bash
chmod +x build_linux.sh
./build_linux.sh
```

This creates a standalone executable at `dist/SCUM_Server_Browser` that works on most Linux systems.

### Manual Build

```bash
source .venv/bin/activate
pip install PyInstaller
python -m PyInstaller SCUM_Server_Browser.spec
```

### Distribution

To distribute the Linux version:

```bash
# Create a distributable package
zip -r SCUM_Server_Browser-Linux.zip dist/
```

Users can then extract and run:
```bash
./SCUM_Server_Browser-Linux/dist/SCUM_Server_Browser
```

## Building for Windows

### Quick Build

1. Open Command Prompt or PowerShell in the project directory
2. Run: `build_windows.bat`

This creates a standalone executable at `dist\SCUM_Server_Browser.exe`

### Manual Build

```cmd
.venv\Scripts\activate.bat
pip install PyInstaller
python -m PyInstaller SCUM_Server_Browser.spec
```

### Distribution

To distribute the Windows version:

```cmd
REM Create a distributable package using Windows Explorer
REM Right-click dist folder → Send to → Compressed (zipped) folder
REM OR use 7-Zip/WinRAR for better compression
```

Windows users can then extract and run:
```
SCUM_Server_Browser-Windows\dist\SCUM_Server_Browser.exe
```

## Cross-Platform Building

### Building on Linux for Both Platforms

To build Windows executables on Linux, you can use Wine:

```bash
# Install Wine (on Ubuntu/Debian)
sudo apt-get install wine wine32 wine64

# Then use the Windows build approach with Wine-based Python
```

However, the easiest approach is to build on the target platform.

### GitHub Actions for Automated Builds

For truly automated cross-platform builds, consider setting up GitHub Actions (ask for help if needed).

## File Size and Optimization

- Linux executable: ~200-300 MB (includes Python runtime)
- Windows executable: ~200-300 MB (includes Python runtime)

This is normal for PyInstaller bundles. For distribution, the zip files compress to ~60-100 MB.

## Troubleshooting

### "Module not found" errors during build

Add the missing module to the `hiddenimports` list in `SCUM_Server_Browser.spec`

### Executable won't start

Check for dependency issues:
- Run `python -m scum_tracker` from the venv to verify the app works
- Check if all requirements are properly installed: `pip list`

### Icon not showing in taskbar

This is a window manager limitation on some Linux desktop environments. The app still functions correctly.

## Post-Build

The executable will:
- ✅ Run without needing Python installed
- ✅ Include all dependencies (PyQt6, requests, etc.)
- ✅ Work on any system with compatible architecture
- ✅ Preserve all settings/cache in `~/.scum_tracker/`

## Users Running the Executable

For end users receiving the executable:

### Linux
```bash
# Make executable
chmod +x SCUM_Server_Browser

# Run it
./SCUM_Server_Browser
```

### Windows
```cmd
# Just double-click SCUM_Server_Browser.exe
REM Or run from command line:
SCUM_Server_Browser.exe
```

No additional installation required!
