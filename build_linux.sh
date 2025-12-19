#!/bin/bash
# Build script for SCUM Server Browser
# Creates self-contained executables for Linux

set -e

echo "================================================"
echo "SCUM Server Browser - Build Script (Linux)"
echo "================================================"
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv .venv"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install -q -r requirements.txt requirements-build.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec.bak

# Build executable
echo "🔨 Building executable..."
python -m PyInstaller SCUM_Server_Browser.spec

echo ""
echo "================================================"
echo "✅ Build completed successfully!"
echo "================================================"
echo ""
echo "📍 Executable location:"
echo "   ./dist/SCUM_Server_Browser"
echo ""
echo "🚀 To run the app:"
echo "   ./dist/SCUM_Server_Browser"
echo ""
echo "📦 To distribute, zip the entire 'dist' folder:"
echo "   zip -r SCUM_Server_Browser-Linux.zip dist/"
echo ""
