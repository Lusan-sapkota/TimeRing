# TimeRing .deb Package Build Guide

This guide explains how to build a self-contained Debian package (.deb) for the TimeRing application.

## Quick Start

### Build the Self-Contained Package
```bash
chmod +x build_deb.sh
./build_deb.sh
```

## Prerequisites

### System Requirements
- Ubuntu/Debian-based Linux distribution
- `dpkg-dev` package for building .deb files
- `python3` (3.8 or higher)
- `python3-venv` for creating virtual environments

### Install Build Dependencies
```bash
sudo apt update
sudo apt install -y dpkg-dev python3 python3-venv python3-pip lintian
```

**Note**: This package is now **self-contained** and does not require users to install PyQt5, VLC, or other Python dependencies on their system. All dependencies are bundled within the package.

## Build Process

The build script creates a **self-contained** Debian package with:

1. **Bundled Virtual Environment**
   - Complete Python virtual environment with all dependencies
   - PyQt5, python-vlc, and other required packages pre-installed
   - No need for users to install Python packages separately

2. **Application Files**
   - Main Python application (`main.py`)
   - Version information (`version.py`)
   - Glass checkbox component (`glass_checkbox.py`)
   - Stylesheet (`style.qss`)
   - Images and icons
   - Sound files

3. **System Integration**
   - Desktop entry file for application launcher
   - Icon for system menus
   - Executable script in `/usr/bin`

4. **Package Metadata**
   - Debian control file with minimal dependencies
   - Installation/removal scripts
   - Documentation and changelog

## Package Structure

After building, the package will install files to:

```
/usr/bin/timering                     # Executable launcher
/usr/share/applications/TimeRing.desktop  # Desktop entry
/usr/share/pixmaps/TimeRing.png       # Application icon
/usr/share/TimeRing/                  # Application files
├── main.py                           # Main application
├── version.py                        # Version information
├── glass_checkbox.py                 # Glass checkbox component
├── style.qss                         # Stylesheet
├── images/                           # Images and icons
├── sounds/                           # Sound files
└── venv/                             # Bundled Python environment
    ├── bin/                          # Python executables
    ├── lib/                          # Python libraries
    └── ...                           # Other venv files
/usr/share/doc/timering/              # Documentation
```

## Installation and Usage

### Install the Package

```bash
# Install the built package
sudo dpkg -i build/TimeRing_1.0.0.deb

# Dependencies are automatically resolved (minimal requirements)
# No need to install PyQt5, VLC, or Python packages separately!
```

### Run the Application

After installation, you can run TimeRing in several ways:

1. **From Application Menu**: Look for "TimeRing" in your application launcher
2. **From Terminal**: `timering`
3. **From Desktop**: Double-click the desktop icon (if created)

### Uninstall

```bash
sudo apt remove timering
```

## Build Script Features

### Self-Contained Packaging

- **No External Dependencies**: All Python packages are bundled within the .deb
- **Isolated Environment**: Uses a virtual environment to avoid conflicts
- **Minimal System Requirements**: Only requires Python 3.8+, libc6, and libvlc5
- **Easy Distribution**: Users don't need to install PyQt5 or other complex dependencies

### Build Process Features

- Comprehensive .deb package creation with virtual environment bundling
- Proper Debian package structure with root ownership
- File permissions and ownership handling
- Package validation with lintian
- Colored output for better readability
- Automatic cleanup of temporary files and cache

## Troubleshooting

### Common Issues

1. **Permission Denied**

   ```bash
   chmod +x build_deb.sh
   ```

2. **Missing Build Tools**

   ```bash
   sudo apt install dpkg-dev python3-venv
   ```

3. **Build Process Fails**

   - Ensure you have sufficient disk space (package is ~50MB)
   - Check that Python 3.8+ is installed
   - Verify internet connection for downloading Python packages

4. **Package Installation Fails**

   ```bash
   # Check package integrity
   dpkg -I build/TimeRing_1.0.0.deb
   
   # Force installation if needed
   sudo dpkg -i --force-depends build/TimeRing_1.0.0.deb
   ```

5. **Application Won't Start**

   - Check if all files were installed: `ls -la /usr/share/TimeRing/`
   - Verify virtual environment: `ls -la /usr/share/TimeRing/venv/bin/`
   - Test launcher script: `cat /usr/bin/timering`

### Testing the Package

Before distributing, test the package:

1. **Install on a clean system**
2. **Verify the application launches**
3. **Test desktop integration**
4. **Check that no external dependencies are required**

```bash
# Test package info
dpkg -I build/TimeRing_1.0.0.deb

# Test package contents
dpkg -c build/TimeRing_1.0.0.deb

# Validate with lintian (if available)
lintian build/TimeRing_1.0.0.deb
```

## Customization

### Modifying Package Information

Edit the variables at the top of `build_deb.sh`:

```bash
APP_NAME="TimeRing"
APP_VERSION="1.0.0"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="Your custom description"
ARCHITECTURE="amd64"  # or "all" for architecture-independent
```

### Adding More Dependencies

Modify the `DEPENDS` variable in `build_deb.sh`:

```bash
DEPENDS="python3 (>= 3.8), libc6, libvlc5, your-additional-package"
```

### Custom Python Packages

Add packages to `requirements.txt` or modify the pip install section:

```bash
# In build_deb.sh, modify this section:
pip install PyQt5 python-vlc requests your-additional-package
```

### Custom Installation Paths

The current structure follows Debian standards. To modify:

1. Edit the directory creation in `build_deb.sh`
2. Update the launcher script paths
3. Modify the desktop file accordingly

## Distribution

### Sharing the Package

After building, you can share the `.deb` file:

```bash
# The package is self-contained - just share this file
cp build/TimeRing_1.0.0.deb /path/to/share/

# Or create a release archive
tar czf TimeRing-1.0.0-deb.tar.gz build/TimeRing_1.0.0.deb README_BUILD.md
```

### Advantages of Self-Contained Package

- **Easy Distribution**: No need to worry about user's Python environment
- **No Conflicts**: Isolated virtual environment prevents library conflicts
- **Cross-System Compatibility**: Works on any Debian/Ubuntu system with minimal requirements
- **Version Control**: Each package has its own dependency versions

## Advanced Options

### Debug Build

To create a debug version with additional logging:

```bash
DEBUG=1 ./build_deb.sh
```

### Custom Build Directory

```bash
BUILD_DIR=/tmp/TimeRing-build ./build_deb.sh
```

### Skip Package Validation

```bash
SKIP_LINTIAN=1 ./build_deb.sh
```

## Support

For build issues:

1. Check the build log output for detailed error messages
2. Ensure you have sufficient disk space (build requires ~200MB temporarily)
3. Verify Python 3.8+ and venv module are available
4. Check internet connectivity for downloading Python packages
5. Ensure you're running on a supported Debian/Ubuntu system

---

**Note**: This self-contained packaging approach makes TimeRing easy to distribute and install without requiring users to manage Python dependencies manually. The package size is larger (~50MB) but provides a much better user experience.
