# Windows Build Guide

This guide explains how to build the Windows executable for SCUM Server Browser.

## Prerequisites

1. **Windows PC or Virtual Machine**
   - Windows 7 SP1 or later
   - At least 2 GB RAM free
   - 5 GB disk space for build process

2. **Python Installation**
   - Download Python 3.11 from https://www.python.org/downloads/
   - **IMPORTANT**: Check "Add Python to PATH" during installation
   - Use default installation path

3. **Git (Optional but Recommended)**
   - Download from https://git-scm.com/download/win
   - Use default options

## Step-by-Step Build Instructions

### 1. Get the Source Code

Option A - Clone from GitHub:
```cmd
git clone https://github.com/yourusername/scum-browser.git
cd scum-browser
```

Option B - Download ZIP:
- Download the repository as ZIP from GitHub
- Extract to a folder like `C:\scum-browser`
- Open Command Prompt and navigate to the folder

### 2. Set Up Virtual Environment

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

You should see `(.venv)` at the start of the command line.

### 3. Install Dependencies

```cmd
pip install -r requirements.txt
pip install PyInstaller
```

This will take 2-5 minutes.

### 4. Build the Executable

```cmd
python -m PyInstaller SCUM_Server_Browser.spec
```

This will take 3-5 minutes. You'll see output like:
```
INFO: Analyzing...
INFO: Building...
INFO: Build complete! The results are available in: dist
```

### 5. Test the Executable

```cmd
dist\SCUM_Server_Browser.exe
```

The app should launch! Test basic functionality:
- [ ] Window opens with title "SCUM Server Browser"
- [ ] Servers load in the table
- [ ] Can click on columns to sort
- [ ] Can change theme
- [ ] Search works
- [ ] Can click favorites

### 6. Create Distribution Package (Optional)

For distribution, create a ZIP file:

```cmd
REM Navigate to dist folder
cd dist

REM Create ZIP (using Windows Explorer or 7-Zip)
REM Right-click SCUM_Server_Browser -> Send to -> Compressed (zipped) folder
```

Or from command line (if you have 7-Zip installed):
```cmd
7z a ..\SCUM_Server_Browser-Windows.zip SCUM_Server_Browser.exe
```

## File Locations After Build

After successful build:

```
C:\scum-browser\
├── dist\
│   ├── SCUM_Server_Browser.exe      ← The executable (146 MB)
│   ├── SCUM_Server_Browser\         ← Support libraries folder
│   └── ...
├── build\                           ← Temporary build files
└── ...
```

## Distribution

### For your own hosting:
```cmd
REM Create a folder with the executable
mkdir releases
copy dist\SCUM_Server_Browser.exe releases\

REM Create a ZIP for distribution
cd releases
7z a SCUM_Server_Browser-Windows.zip SCUM_Server_Browser.exe
```

Users can then:
1. Download `SCUM_Server_Browser-Windows.zip`
2. Extract the folder
3. Double-click `SCUM_Server_Browser.exe`

### For GitHub Releases:
1. Go to GitHub releases page
2. Create new release
3. Upload `SCUM_Server_Browser.exe` directly
4. Also upload Linux package from another machine

## Troubleshooting

### "python command not found"
- Python wasn't added to PATH
- Reinstall Python with "Add Python to PATH" checked
- Or use full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`

### "pip: command not found"
- Same as above - Python PATH issue
- Or use: `python -m pip install`

### "No module named PyQt6"
```cmd
pip install PyQt6
```

### Building takes forever or seems stuck
- This is normal for the first build (5-10 minutes)
- Building subsequent times is faster (2-3 minutes)
- Don't interrupt - let it complete

### "PyInstaller not found"
```cmd
pip install PyInstaller
```

### Executable won't start
- Run from command line to see error messages:
```cmd
dist\SCUM_Server_Browser.exe
```
- Check if Python 3.8+ is installed

### Very large file size
- 146 MB is normal for PyInstaller + PyQt6
- This includes the Python runtime (35 MB) + all libraries
- Compression to ZIP reduces to ~50 MB

## Advanced Options

### Code Signing (Optional)
To remove security warnings on some systems:

1. Get a code signing certificate
2. Sign the executable:
```cmd
signtool sign /f certificate.pfx /t http://timestamp.server.com SCUM_Server_Browser.exe
```

### Creating an Installer (Optional)
For professional distribution, use NSIS or InnoSetup:
1. Download Inno Setup from http://www.jrsoftware.org/isinfo.php
2. Create a script to install the executable
3. Build installer executable

## Verification

After building, verify the executable:

```cmd
REM Check file size
dir /s dist\SCUM_Server_Browser.exe

REM Check it's a valid executable
file dist\SCUM_Server_Browser.exe  (if you have Git Bash)
```

Should output: EXE, Windows executable

## Performance Tips

- **First build**: Full compilation (5-10 minutes, normal)
- **Subsequent builds**: Clean rebuild
  ```cmd
  rmdir /s /q build dist
  python -m PyInstaller SCUM_Server_Browser.spec
  ```

- **Faster iteration**: During development, just run from Python:
  ```cmd
  python -m scum_tracker
  ```

## Next Steps

1. ✓ Build successful locally? Great!
2. Test on another Windows machine if possible
3. Upload to GitHub Releases
4. Share the download link
5. Get user feedback!

## Scripted Build (One-Click)

To make it even easier, you can create a batch file:

Create `quick_build.bat`:
```batch
@echo off
.venv\Scripts\activate.bat
rmdir /s /q build dist
python -m PyInstaller SCUM_Server_Browser.spec
echo.
echo Build complete! Executable: dist\SCUM_Server_Browser.exe
pause
```

Then just double-click `quick_build.bat` to rebuild anytime!

---

**You're ready to build for Windows!** 🎉
