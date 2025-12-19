#!/bin/bash
# Quick distribution package creator
# Run this after building to create distribution packages

set -e

echo "================================================"
echo "SCUM Server Browser - Package Creator"
echo "================================================"
echo ""

if [ ! -f "dist/SCUM_Server_Browser" ]; then
    echo "❌ Linux executable not found!"
    echo "Please run ./build_linux.sh first"
    exit 1
fi

# Create distribution packages
echo "📦 Creating distribution packages..."

# Linux tar.gz
echo "  Creating SCUM_Server_Browser-Linux.tar.gz..."
cd dist
tar -czf ../SCUM_Server_Browser-Linux.tar.gz SCUM_Server_Browser
cd ..

# Create checksums
echo "  Creating checksums..."
sha256sum dist/SCUM_Server_Browser > SCUM_Server_Browser-Linux.sha256

echo ""
echo "================================================"
echo "✅ Distribution packages created!"
echo "================================================"
echo ""
echo "📦 Files ready for distribution:"
echo "   - dist/SCUM_Server_Browser (146 MB uncompressed)"
echo "   - SCUM_Server_Browser-Linux.tar.gz (~50-60 MB)"
echo "   - SCUM_Server_Browser-Linux.sha256 (checksum)"
echo ""
echo "🚀 To distribute:"
echo "   1. Upload SCUM_Server_Browser-Linux.tar.gz to your site"
echo "   2. Include SCUM_Server_Browser-Linux.sha256 for verification"
echo "   3. Users can extract and run: tar -xzf *.tar.gz && ./SCUM_Server_Browser"
echo ""
echo "📝 For verification, users can run:"
echo "   sha256sum -c SCUM_Server_Browser-Linux.sha256"
echo ""
