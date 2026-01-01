#!/bin/bash
# SCUM Server Browser - Linux Installer (Standalone Build)
# Installs the PyInstaller-built executable to a system location
# and creates a desktop entry for the application menu

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  SCUM Server Browser - Linux Installer"
echo "=============================================="
echo ""

# Check if SCUM_Server_Browser executable exists
if [ ! -f "SCUM_Server_Browser" ]; then
    echo -e "${RED}Error: SCUM_Server_Browser executable not found${NC}"
    echo "Please run this script from the extracted distribution directory"
    exit 1
fi

# Installation directories
INSTALL_DIR="$HOME/.local/share/scum-server-browser"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "Installation directories:"
echo "  Application: $INSTALL_DIR"
echo "  Binary link: $BIN_DIR/scum-server-browser"
echo "  Desktop entry: $DESKTOP_DIR/scum-server-browser.desktop"
echo ""

# Create directories if they don't exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR/48x48/apps"

# Copy executable
echo ""
echo "Installing application..."
cp SCUM_Server_Browser "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/SCUM_Server_Browser"
echo -e "${GREEN}✓${NC} Executable installed"

# Copy documentation if available
if [ -f "README.md" ]; then
    cp README.md "$INSTALL_DIR/"
fi
if [ -f "CHANGELOG.md" ]; then
    cp CHANGELOG.md "$INSTALL_DIR/"
fi

# Create symlink in bin directory
ln -sf "$INSTALL_DIR/SCUM_Server_Browser" "$BIN_DIR/scum-server-browser"
echo -e "${GREEN}✓${NC} Binary symlink created"

# Create a simple icon if none exists (fallback)
ICON_INSTALLED=false
if [ -f "_internal/scum_tracker/assets/app_icon.png" ]; then
    cp "_internal/scum_tracker/assets/app_icon.png" "$ICON_DIR/48x48/apps/scum-server-browser.png"
    ICON_INSTALLED=true
    echo -e "${GREEN}✓${NC} Icon installed"
elif command -v convert &> /dev/null; then
    # Create a simple placeholder icon using ImageMagick if available
    convert -size 48x48 xc:blue -gravity center -pointsize 20 -fill white -annotate +0+0 "SCUM" "$ICON_DIR/48x48/apps/scum-server-browser.png" 2>/dev/null && ICON_INSTALLED=true
fi

# Create .desktop file
cat > "$DESKTOP_DIR/scum-server-browser.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SCUM Server Browser
Comment=Track and ping SCUM game servers with real-time latency monitoring
Exec=$BIN_DIR/scum-server-browser
Path=$INSTALL_DIR
Icon=scum-server-browser
Terminal=false
Categories=Game;Network;
Keywords=scum;server;browser;game;ping;
StartupWMClass=scum_tracker
EOF
chmod 644 "$DESKTOP_DIR/scum-server-browser.desktop"
echo -e "${GREEN}✓${NC} Desktop entry created"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null && [ "$ICON_INSTALLED" = true ]; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

# KDE-specific: rebuild system configuration cache
if command -v kbuildsycoca6 &> /dev/null; then
    kbuildsycoca6 2>/dev/null || true
elif command -v kbuildsycoca5 &> /dev/null; then
    kbuildsycoca5 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}=============================================="
echo "  Installation Complete!"
echo "==============================================  ${NC}"
echo ""
echo "You can now:"
echo "  1. Launch from the application menu (Games category)"
echo "  2. Run 'scum-server-browser' from the terminal"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Note:${NC} $BIN_DIR is not in your PATH."
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "To uninstall, run: $INSTALL_DIR/uninstall.sh"
echo ""

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL_EOF'
#!/bin/bash
# SCUM Server Browser - Uninstaller

set -e

INSTALL_DIR="$HOME/.local/share/scum-server-browser"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "Uninstalling SCUM Server Browser..."

# Remove symlink
rm -f "$BIN_DIR/scum-server-browser"
echo "✓ Binary symlink removed"

# Remove desktop entry
rm -f "$DESKTOP_DIR/scum-server-browser.desktop"
echo "✓ Desktop entry removed"

# Remove icon
rm -f "$ICON_DIR/48x48/apps/scum-server-browser.png"
echo "✓ Icon removed"

# Update caches
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

# Remove installation directory
rm -rf "$INSTALL_DIR"
echo "✓ Application files removed"

echo ""
echo "SCUM Server Browser has been uninstalled."
echo ""
UNINSTALL_EOF
chmod +x "$INSTALL_DIR/uninstall.sh"
