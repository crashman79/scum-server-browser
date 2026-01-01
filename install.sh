#!/bin/bash
# SCUM Server Browser - Linux Installer
# Installs the application to ~/.local/share/scum-server-browser
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

# Check if running from the source directory
if [ ! -f "scum_tracker/__init__.py" ]; then
    echo -e "${RED}Error: This script must be run from the SCUM Server Browser directory${NC}"
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
mkdir -p "$ICON_DIR/256x256/apps"
mkdir -p "$ICON_DIR/64x64/apps"
mkdir -p "$ICON_DIR/32x32/apps"
mkdir -p "$ICON_DIR/16x16/apps"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓${NC} Found Python $PYTHON_VERSION"

# Copy application files
echo ""
echo "Installing application files..."
cp -r scum_tracker "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"
cp CHANGELOG.md "$INSTALL_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Application files copied"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if [ -d ".venv" ]; then
    echo "  Using existing virtual environment..."
    cp -r .venv "$INSTALL_DIR/"
    echo -e "${GREEN}✓${NC} Virtual environment copied"
else
    echo "  Creating virtual environment..."
    python3 -m venv "$INSTALL_DIR/.venv"
    
    echo "  Installing dependencies..."
    "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip > /dev/null 2>&1
    "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" > /dev/null 2>&1
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi

# Create launcher script
cat > "$INSTALL_DIR/scum-server-browser" << 'EOF'
#!/bin/bash
# SCUM Server Browser Launcher
cd "$(dirname "$0")"
exec .venv/bin/python -m scum_tracker "$@"
EOF
chmod +x "$INSTALL_DIR/scum-server-browser"
echo -e "${GREEN}✓${NC} Launcher script created"

# Create symlink in bin directory
ln -sf "$INSTALL_DIR/scum-server-browser" "$BIN_DIR/scum-server-browser"
echo -e "${GREEN}✓${NC} Binary symlink created"

# Copy icons
if [ -f "scum_tracker/assets/app_icon.png" ]; then
    cp "scum_tracker/assets/app_icon.png" "$ICON_DIR/256x256/apps/scum-server-browser.png"
    echo -e "${GREEN}✓${NC} Icon installed (256x256)"
fi
if [ -f "scum_tracker/assets/app_icon_64.png" ]; then
    cp "scum_tracker/assets/app_icon_64.png" "$ICON_DIR/64x64/apps/scum-server-browser.png"
    echo -e "${GREEN}✓${NC} Icon installed (64x64)"
fi
if [ -f "scum_tracker/assets/app_icon_32.png" ]; then
    cp "scum_tracker/assets/app_icon_32.png" "$ICON_DIR/32x32/apps/scum-server-browser.png"
    echo -e "${GREEN}✓${NC} Icon installed (32x32)"
fi
if [ -f "scum_tracker/assets/app_icon_16.png" ]; then
    cp "scum_tracker/assets/app_icon_16.png" "$ICON_DIR/16x16/apps/scum-server-browser.png"
    echo -e "${GREEN}✓${NC} Icon installed (16x16)"
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
if command -v gtk-update-icon-cache &> /dev/null; then
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

# Remove icons
rm -f "$ICON_DIR/256x256/apps/scum-server-browser.png"
rm -f "$ICON_DIR/64x64/apps/scum-server-browser.png"
rm -f "$ICON_DIR/32x32/apps/scum-server-browser.png"
rm -f "$ICON_DIR/16x16/apps/scum-server-browser.png"
echo "✓ Icons removed"

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
