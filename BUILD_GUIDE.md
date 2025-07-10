# TimeRing .deb Package Build - Quick Guide

## 🚀 One-Command Build

```bash
make build
```

## 📋 Step-by-Step Instructions

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y dpkg-dev python3-pyqt5 python3-vlc vlc
```

### 2. Build the Package
Choose one of these methods:

**Method A: Using Make (Recommended)**
```bash
make build
```

**Method B: Using Quick Script**
```bash
./quick_build.sh
```

**Method C: Full Build Script**
```bash
./build_deb.sh
```

### 3. Install the Package
```bash
sudo dpkg -i build/timering_1.0.0.deb
sudo apt-get install -f  # Fix any missing dependencies
```

### 4. Run TimeRing
```bash
TimeRing
```
Or find "TimeRing" in your application menu.

## 📦 What Gets Built

- **Package**: `build/timering_1.0.0.deb`
- **Size**: ~500KB (estimated)
- **Dependencies**: python3, python3-pyqt5, python3-vlc, vlc

## 🎯 Distribution

The built `.deb` package can be:
- Shared with other Ubuntu/Debian users
- Installed on multiple machines
- Distributed through package repositories

## ❓ Troubleshooting

**Permission denied?**
```bash
chmod +x build_deb.sh quick_build.sh
```

**Missing dpkg-dev?**
```bash
sudo apt install dpkg-dev
```

**Package won't install?**
```bash
sudo apt-get install -f
```

---
*For detailed information, see README_BUILD.md*
