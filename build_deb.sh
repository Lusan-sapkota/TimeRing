#!/bin/bash

# TimeRing .deb Build Script
# This script creates a Debian package for the TimeRing application

set -e  # Exit on any error

# Configuration
APP_NAME="TimeRing"
APP_VERSION="1.0.0"
MAINTAINER="Lusan Sapkota <sapkotalusan@gmail.com>"
DESCRIPTION="A lightweight, modern, and beautiful timer application for your desktop (self-contained)"
SECTION="utils"
PRIORITY="optional"
ARCHITECTURE="amd64"
DEPENDS="python3 (>= 3.8), libc6, libvlc5"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Build directories
BUILD_DIR="$PROJECT_DIR/build"
DEB_DIR="$BUILD_DIR/${APP_NAME}_${APP_VERSION}"
DEBIAN_DIR="$DEB_DIR/DEBIAN"

log_info "Starting TimeRing .deb package build..."
log_info "Project directory: $PROJECT_DIR"
log_info "Build directory: $BUILD_DIR"

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    log_info "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# Create directory structure
log_info "Creating package directory structure..."
mkdir -p "$DEBIAN_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/pixmaps"
mkdir -p "$DEB_DIR/usr/share/$APP_NAME"
mkdir -p "$DEB_DIR/usr/share/$APP_NAME/images"
mkdir -p "$DEB_DIR/usr/share/$APP_NAME/images/icons"
mkdir -p "$DEB_DIR/usr/share/$APP_NAME/sounds"
mkdir -p "$DEB_DIR/usr/share/$APP_NAME/venv"
mkdir -p "$DEB_DIR/usr/share/doc/timering"

# Create virtual environment with all dependencies
log_info "Creating virtual environment and installing dependencies..."
python3 -m venv "$DEB_DIR/usr/share/$APP_NAME/venv"
source "$DEB_DIR/usr/share/$APP_NAME/venv/bin/activate"

# Upgrade pip first
pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    # Install manually if requirements.txt doesn't exist
    pip install PyQt5 python-vlc requests
fi

# Download and bundle VLC components (alternative approach)
log_info "Setting up VLC dependencies..."
pip install python-vlc

deactivate

# Clean up the virtual environment
log_info "Cleaning up virtual environment..."
# Remove __pycache__ directories
find "$DEB_DIR/usr/share/$APP_NAME/venv" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
# Remove .pyc files
find "$DEB_DIR/usr/share/$APP_NAME/venv" -name "*.pyc" -delete 2>/dev/null || true
# Remove .gitignore files
find "$DEB_DIR/usr/share/$APP_NAME/venv" -name ".gitignore" -delete 2>/dev/null || true
# Fix shebang lines in venv scripts
find "$DEB_DIR/usr/share/$APP_NAME/venv/bin" -type f -executable -exec sed -i '1s|^#!.*python.*|#!/usr/share/TimeRing/venv/bin/python|' {} \; 2>/dev/null || true

# Copy application files
log_info "Copying application files..."
cp "$PROJECT_DIR/main.py" "$DEB_DIR/usr/share/$APP_NAME/"
cp "$PROJECT_DIR/version.py" "$DEB_DIR/usr/share/$APP_NAME/"
cp "$PROJECT_DIR/glass_checkbox.py" "$DEB_DIR/usr/share/$APP_NAME/"
cp "$PROJECT_DIR/style.qss" "$DEB_DIR/usr/share/$APP_NAME/"
cp "$PROJECT_DIR/requirements.txt" "$DEB_DIR/usr/share/$APP_NAME/"

# Copy assets
log_info "Copying assets..."
cp "$PROJECT_DIR/images/logo.png" "$DEB_DIR/usr/share/pixmaps/$APP_NAME.png"
cp "$PROJECT_DIR/images/logo.png" "$DEB_DIR/usr/share/$APP_NAME/images/"
cp -r "$PROJECT_DIR/images/icons/"* "$DEB_DIR/usr/share/$APP_NAME/images/icons/"
cp -r "$PROJECT_DIR/sounds/"* "$DEB_DIR/usr/share/$APP_NAME/sounds/"

# Copy documentation
log_info "Copying documentation..."
cp "$PROJECT_DIR/README.md" "$DEB_DIR/usr/share/doc/timering/"
cp "$PROJECT_DIR/LICENSE" "$DEB_DIR/usr/share/doc/timering/" 2>/dev/null || log_warning "LICENSE file not found"

# Create executable launcher script
log_info "Creating launcher script..."
cat > "$DEB_DIR/usr/bin/timering" << 'EOF'
#!/bin/bash
# TimeRing Launcher Script

# Set the application directory
APP_DIR="/usr/share/TimeRing"
VENV_DIR="$APP_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Change to app directory to ensure relative paths work
cd "$APP_DIR"

# Launch the application using the bundled Python environment
exec "$VENV_DIR/bin/python" "$APP_DIR/main.py" "$@"
EOF

chmod +x "$DEB_DIR/usr/bin/timering"

# Create desktop entry
log_info "Creating desktop entry..."
cat > "$DEB_DIR/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=TimeRing
Comment=$DESCRIPTION
Exec=timering
Icon=$APP_NAME
Terminal=false
Categories=Utility;Office;
Keywords=timer;clock;countdown;productivity;
StartupNotify=true
EOF

# Create control file
log_info "Creating Debian control file..."
cat > "$DEBIAN_DIR/control" << EOF
Package: timering
Version: $APP_VERSION
Section: $SECTION
Priority: $PRIORITY
Architecture: $ARCHITECTURE
Depends: $DEPENDS
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 TimeRing is a versatile and user-friendly timer application designed to help
 you manage your time effectively. Whether you're working, studying, or cooking,
 TimeRing provides a clean and intuitive interface to run multiple timers at once.
 .
 Features:
  - Multiple concurrent timers
  - Custom timer names and descriptions
  - Sound notifications
  - Modern Apple-style UI
  - Dark and light theme support
  - Timer persistence and restore
Homepage: https://github.com/Lusan-sapkota/TimeRing
EOF

# Create postinst script
log_info "Creating post-installation script..."
cat > "$DEBIAN_DIR/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/pixmaps 2>/dev/null || true
fi

exit 0
EOF

chmod +x "$DEBIAN_DIR/postinst"

# Create prerm script
log_info "Creating pre-removal script..."
cat > "$DEBIAN_DIR/prerm" << 'EOF'
#!/bin/bash
set -e

# Nothing specific to do before removal
exit 0
EOF

chmod +x "$DEBIAN_DIR/prerm"

# Create postrm script
log_info "Creating post-removal script..."
cat > "$DEBIAN_DIR/postrm" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    remove|purge)
        # Update desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database -q
        fi
        
        # Update icon cache
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            gtk-update-icon-cache -q -t -f /usr/share/pixmaps 2>/dev/null || true
        fi
        ;;
esac

exit 0
EOF

chmod +x "$DEBIAN_DIR/postrm"

# Create changelog
log_info "Creating changelog..."
mkdir -p "$DEB_DIR/usr/share/doc/timering"
cat > "$DEB_DIR/usr/share/doc/timering/changelog.Debian" << EOF
timering ($APP_VERSION-1) unstable; urgency=low

  * Initial release of TimeRing timer application
  * Multiple concurrent timers support
  * Custom timer names and descriptions
  * Sound notifications
  * Modern Apple-style UI with dark/light theme support
  * Timer persistence and restore functionality

 -- $MAINTAINER  $(date -R)
EOF

gzip -9 "$DEB_DIR/usr/share/doc/timering/changelog.Debian"

# Create copyright file
log_info "Creating copyright file..."
cat > "$DEB_DIR/usr/share/doc/timering/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: TimeRing
Source: https://github.com/Lusan-sapkota/TimeRing

Files: *
Copyright: $(date +%Y) Lusan Sapkota
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# Calculate installed size
log_info "Calculating package size..."
INSTALLED_SIZE=$(du -s "$DEB_DIR" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEBIAN_DIR/control"

# Set proper permissions
log_info "Setting file permissions..."
find "$DEB_DIR" -type f -exec chmod 644 {} \;
find "$DEB_DIR" -type d -exec chmod 755 {} \;
chmod +x "$DEB_DIR/usr/bin/timering"
chmod +x "$DEBIAN_DIR/postinst"
chmod +x "$DEBIAN_DIR/prerm"
chmod +x "$DEBIAN_DIR/postrm"
# Fix permissions for venv executables
find "$DEB_DIR/usr/share/$APP_NAME/venv/bin" -type f -exec chmod +x {} \;

# Build the package
log_info "Building .deb package..."
cd "$BUILD_DIR"
dpkg-deb --root-owner-group --build "${APP_NAME}_${APP_VERSION}"

# Check if package was created successfully
PACKAGE_FILE="${BUILD_DIR}/${APP_NAME}_${APP_VERSION}.deb"
if [ -f "$PACKAGE_FILE" ]; then
    log_success "Package built successfully: $PACKAGE_FILE"
    
    # Get package info
    PACKAGE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
    log_info "Package size: $PACKAGE_SIZE"
    
    # Test package
    log_info "Testing package with lintian (if available)..."
    if command -v lintian >/dev/null 2>&1; then
        lintian "$PACKAGE_FILE" || log_warning "Lintian found some issues (non-critical)"
    else
        log_warning "lintian not found, skipping package validation"
    fi
    
    # Show package information
    log_info "Package information:"
    dpkg-deb --info "$PACKAGE_FILE"
    
    echo ""
    log_success "Build completed successfully!"
    log_info "Package location: $PACKAGE_FILE"
    log_info "To install: sudo dpkg -i $PACKAGE_FILE"
    log_info "To install dependencies if missing: sudo apt-get install -f"
    
else
    log_error "Package build failed!"
    exit 1
fi
