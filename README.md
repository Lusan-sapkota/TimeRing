# TimeRing - Modern Desktop Timer Application

<div align="center">
  <img src="images/logo.png" alt="TimeRing Logo" width="128" height="128">
  
  **A lightweight, modern timer application for Linux desktop environments**
  
  ![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
  ![Python](https://img.shields.io/badge/python-3.13-green.svg)
  ![License](https://img.shields.io/badge/license-MIT-green.svg)
  ![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)
</div>

## ✨ Features

### 🎯 Core Functionality
- **Multiple Concurrent Timers**: Run multiple timers simultaneously with different durations
- **Custom Timer Names**: Personalize each timer with descriptive names
- **Timer Descriptions**: Add detailed descriptions up to 200 words per timer
- **Pause/Resume**: Full control over timer execution
- **Persistent State**: Automatically saves and restores timer states across app restarts

### 🔊 Audio & Notifications
- **Custom Notification Sounds**: Set different sounds for each timer or use a global default
- **Sound Looping**: Continuous audio alerts until manually stopped
- **Desktop Notifications**: Native KDE and GNOME notification integration
- **Notification Urgency Levels**: Configure low, normal, or critical urgency

### 🎨 Modern User Interface
- **Clean, Modern Design**: Flat design with soft rounded corners and hover effects
- **Slide-in Drawer**: Accessible side panel with Settings, Help, and Info sections
- **Responsive Layout**: Non-blocking UI with smooth animations
- **Status Indicators**: Visual feedback for running, paused, and ringing timers
- **Emoji Icons**: Intuitive emoji-based action buttons

### ⚙️ Advanced Features
- **CLI Support**: Command-line arguments for automation and scripting
- **External Styling**: Customizable appearance via CSS-like stylesheets
- **Settings Management**: Comprehensive preferences for notifications, sounds, and behavior
- **Auto-start**: Optional automatic timer restoration on application launch

## 📦 Installation

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 python3-vlc

# Fedora/RHEL
sudo dnf install python3 python3-pip python3-qt5 python3-vlc

# Arch Linux
sudo pacman -S python python-pip python-pyqt5 python-vlc
```

### Dependencies
Install Python dependencies:
```bash
pip3 install PyQt5 python-vlc
```

### Quick Setup
1. Clone or download the application:
```bash
git clone <repository-url> TimeRing
cd TimeRing
```

2. Ensure the directory structure is correct:
```
TimeRing/
├── main.py
├── style.qss
├── requirements.txt
├── README.md
├── images/
│   └── logo.png
└── sounds/
    └── timesup.mp3
```

3. Make the main script executable:
```bash
chmod +x main.py
```

4. Run the application:
```bash
python3 main.py
```

## 🚀 Usage

### Basic Usage

#### Creating a Timer
1. Enter a descriptive name in the "Timer Name" field
2. Set the duration in minutes in the "Duration" field
3. Optionally add a description (📝 Add Description button)
4. Optionally select a custom sound (🔊 Select Sound button)
5. Click "🚀 Start Timer" to begin

#### Managing Active Timers
Each active timer displays:
- **Timer name and remaining time**
- **Status indicator** (▶️ Running, ⏸️ Paused, 🔔 Ringing)
- **Description preview** (if available)
- **Action buttons**:
  - ✏️ Edit Description
  - 🔊 Change Sound
  - ⏸️/▶️ Pause/Resume
  - 🛑 Stop Timer

### Command Line Interface

```bash
# Show help
python3 main.py --help

# Show version information
python3 main.py --version

# Set default alarm sound
python3 main.py --set-sound /path/to/custom/sound.mp3

# Normal GUI launch
python3 main.py
```

### Menu Drawer
Access the slide-in drawer by clicking the hamburger menu (☰) button:

#### ⚙️ Settings Section
- **📁 Change Default Sound**: Set global default notification sound
- **🔧 Open Preferences**: Access comprehensive settings dialog

#### ❓ Help Section
- **Quick Start Guide**: Step-by-step usage instructions
- **Feature Overview**: Detailed explanation of all features
- **Tips & Tricks**: Advanced usage tips

#### ℹ️ About Section
- **Application Logo**: TimeRing branding
- **Version Information**: Current app version
- **Developer Credits**: Application author information

### Settings & Preferences

#### General Settings
- **Auto-start timers**: Automatically resume timers on app launch
- **Save timer state**: Persist timer information between sessions

#### Notification Settings
- **Show desktop notifications**: Enable/disable system notifications
- **Include description**: Add timer descriptions to notifications
- **Notification urgency**: Set priority level (Low/Normal/Critical)

#### Sound Settings
- **Default sound file**: Global notification sound
- **Loop sound**: Continuous playback until stopped
- **Sound preview**: Test audio before applying

## 🔧 Configuration

### Configuration Directory
TimeRing stores its configuration in:
```
~/.config/TimeRing/
├── settings.json    # Application preferences
└── timers.json      # Active timer states
```

### Example Timer State Format
```json
[
  {
    "name": "Study Session",
    "description": "Focus on math exercises for 45 minutes without distractions.",
    "total_seconds": 2700,
    "remaining_seconds": 1800,
    "sound_path": "./sounds/timesup.mp3",
    "is_ringing": false,
    "is_paused": false
  },
  {
    "name": "Break Time",
    "description": "Take a short 10-minute break, stretch and relax.",
    "total_seconds": 600,
    "remaining_seconds": 0,
    "sound_path": "/home/user/custom_sounds/bell.mp3",
    "is_ringing": true,
    "is_paused": false
  }
]
```

### Example Settings Format
```json
{
  "auto_start_timers": true,
  "save_state": true,
  "show_notifications": true,
  "include_description": true,
  "notification_urgency": "Normal",
  "default_sound": "/home/user/sounds/custom.mp3",
  "loop_sound": true
}
```

## 🎨 Customization

### Styling
Modify `style.qss` to customize the application's appearance. The stylesheet uses standard Qt CSS syntax:

```css
/* Example: Change primary color */
QPushButton {
    background-color: #your-color;
}

/* Example: Modify timer list appearance */
QListWidget {
    background-color: #your-background;
    border-radius: 10px;
}
```

### Sounds
- Place custom sound files in the `sounds/` directory
- Supported formats: MP3, WAV, OGG
- Set as default through Settings or CLI

### Icons
Replace `images/logo.png` with your custom application icon (recommended: 512x512 PNG).

## 📱 Desktop Integration

### Creating a Desktop Entry
Create `~/.local/share/applications/timering.desktop`:

```desktop
[Desktop Entry]
Name=TimeRing
Comment=Modern Desktop Timer Application
Exec=/path/to/TimeRing/main.py
Icon=/path/to/TimeRing/images/logo.png
Terminal=false
Type=Application
Categories=Utility;Clock;
StartupNotify=true
```

### System Installation
For system-wide installation:

1. Copy to system directories:
```bash
sudo cp -r TimeRing /opt/
sudo ln -s /opt/TimeRing/main.py /usr/local/bin/timering
sudo cp TimeRing/images/logo.png /usr/share/pixmaps/timering.png
```

2. Create system desktop entry:
```bash
sudo cp timering.desktop /usr/share/applications/
```

## 🐛 Troubleshooting

### Common Issues

#### Sound not playing
- Ensure VLC is installed: `sudo apt install vlc python3-vlc`
- Check audio file permissions and formats
- Verify PulseAudio/ALSA configuration

#### Notifications not appearing
- Install notification system: `sudo apt install libnotify-bin`
- Check if notifications are enabled in desktop environment
- Verify notification urgency settings

#### Application won't start
- Check Python and PyQt5 installation
- Verify all dependencies are installed
- Run with `python3 -v main.py` for verbose debugging

#### Timer state not saving
- Check write permissions to `~/.config/TimeRing/`
- Ensure sufficient disk space
- Verify JSON file integrity

### Debug Mode
Run with verbose output:
```bash
python3 -v main.py 2>&1 | tee debug.log
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies:
```bash
pip3 install -r requirements.txt
```
4. Make changes and test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Comment complex logic and algorithms
- Maintain backward compatibility

### Testing
Test on multiple desktop environments:
- KDE Plasma
- GNOME Shell
- XFCE
- Cinnamon

## 📋 Requirements

### System Requirements
- **Operating System**: Linux (any distribution)
- **Python**: 3.7 or higher (3.13 recommended)
- **Desktop Environment**: KDE, GNOME, XFCE, or compatible
- **Memory**: 50MB RAM minimum
- **Storage**: 10MB disk space

### Python Dependencies
```txt
PyQt5>=5.15.0
python-vlc>=3.0.0
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Lusan Sapkota**
- Developer and Maintainer
- Contact: [Your contact information]

## 🙏 Acknowledgments

- Qt Project for the excellent GUI framework
- VLC Media Player for robust audio support
- Linux desktop environment teams for notification standards
- The Python community for comprehensive libraries

## 🗺️ Roadmap

### Version 1.1 (Planned)
- [ ] System tray integration
- [ ] Keyboard shortcuts
- [ ] Timer templates
- [ ] Export/import timer configurations

### Version 1.2 (Future)
- [ ] Multiple notification sound profiles
- [ ] Timer categories and filtering
- [ ] Statistics and usage tracking
- [ ] Themes and advanced customization

### Version 2.0 (Long-term)
- [ ] Cloud synchronization
- [ ] Mobile companion app
- [ ] Team collaboration features
- [ ] Plugin system

---

<div align="center">
  Made with ❤️ for the Linux community
</div>
