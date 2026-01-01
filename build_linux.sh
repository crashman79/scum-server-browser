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
pip install -q -r requirements.txt -r requirements-build.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec.bak

# Build executable
echo "🔨 Building executable..."
python -m PyInstaller SCUM_Server_Browser.spec

# Copy installer to dist
echo "📋 Adding installer script..."
cp install-standalone.sh dist/install.sh
cp README.md dist/
cp CHANGELOG.md dist/ 2>/dev/null || true
chmod +x dist/install.sh

echo ""
echo "================================================"
echo "✅ Build completed successfully!"
echo "================================================"
echo ""
echo "📍 Build outputs:"
echo "   ./dist/SCUM_Server_Browser (standalone executable)"
echo "   ./dist/install.sh (Linux installer)"
echo ""
echo "🚀 To run the app directly:"
echo "   ./dist/SCUM_Server_Browser"
echo ""
echo "📦 To install system-wide:"
echo "   cd dist && ./install.sh"
echo ""
echo "📦 To create distribution package:"
echo "   tar -czf SCUM_Server_Browser-Linux.tar.gz -C dist ."
echo ""
