@echo off
REM Build script for SCUM Server Browser
REM Creates self-contained executable for Windows

echo.
echo ================================================
echo SCUM Server Browser - Build Script (Windows)
echo ================================================
echo.

REM Check if venv exists
if not exist ".venv" (
    echo.
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install build dependencies
echo Installing build dependencies...
pip install -q -r requirements.txt requirements-build.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build executable
echo Building executable...
python -m PyInstaller --collect-all PyQt6 --collect-all PyQt6-Qt6 --collect-all PyQt6-sip SCUM_Server_Browser.spec

echo.
echo ================================================
echo Build completed successfully!
echo ================================================
echo.
echo Executable location:
echo    dist\SCUM_Server_Browser.exe
echo.
echo To run the app:
echo    dist\SCUM_Server_Browser.exe
echo.
echo To distribute, zip the entire 'dist' folder
echo.
pause
