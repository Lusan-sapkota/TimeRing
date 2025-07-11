# TimeRing

<div align="center">
  <img src="images/logo.png" alt="TimeRing Logo" width="128" height="128">
  
  **A lightweight, modern, and beautiful timer application for your desktop.**
  
  <br>
  
  [![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Lusan-sapkota/TimeRing)
  [![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)](#platform-compatibility)

  <br>
  
  [**📥 Download**](https://sourceforge.net/projects/timering/) • 
  [**🐙 GitHub**](https://github.com/Lusan-sapkota/TimeRing) • 
  [**📖 Documentation**](#usage) • 
  [**🐛 Report Issues**](https://github.com/Lusan-sapkota/TimeRing/issues)
</div>

<div align="center">
  <img src="./demo/images/timering.png" alt="TimeRing Screenshot" width="700">
</div>

## 🌟 Why TimeRing?

TimeRing transforms how you manage time on your desktop. Whether you're following the Pomodoro Technique, timing cooking recipes, or managing multiple work sessions, TimeRing provides an intuitive and powerful solution that stays out of your way while keeping you on track.

**Perfect for:**
- 🍅 Pomodoro Technique practitioners
- 👨‍💻 Developers managing sprint tasks
- 🍳 Cooking enthusiasts
- 📚 Students using time-blocking
- 🏃‍♂️ Fitness interval training

## ✨ Features

### 🎯 Core Timer Management
- **Multiple Concurrent Timers** - Run unlimited timers simultaneously without interference
- **Priority Timer System** - Most important timer always displayed prominently at the top
- **Active Timer Block** - Large, dedicated display with enhanced controls for your current focus
- **Smart Timer Navigation** - Seamlessly switch between multiple running timers
- **Custom Names & Descriptions** - Personalize each timer with meaningful labels and detailed notes

### 🔊 Smart Notifications
- **Custom Notification Sounds** - Assign unique audio alerts for different timer types
- **Continuous Audio Alerts** - Sounds loop until acknowledged, ensuring you never miss an alert
- **Native Desktop Integration** - Works seamlessly with KDE, GNOME, and other Linux desktop environments
- **Configurable Urgency Levels** - Set notification priority from low to critical

### 🎨 Modern User Experience
- **Clean, Intuitive Interface** - Thoughtfully designed with smooth animations and slide-in menus
- **System-Native Icons** - Automatically uses your system's icon theme for consistency
- **Responsive Design** - Adapts beautifully to different screen sizes, including 720p displays
- **Real-Time Status Updates** - Clear visual feedback for running, paused, ringing, and finished states

### ⚙️ Advanced Capabilities
- **Persistent State Management** - Automatically saves and restores timers across application restarts
- **Flexible Timer Controls** - Pause, resume, stop, and instantly rerun any timer
- **Auto-Update System** - One-click updates when new versions are available
- **CLI Support** - Basic command-line arguments for automation and scripting
- **Customizable Styling** - Modify appearance using Qt's QSS stylesheet system
- **Smooth Performance** - Optimized scrolling and non-blocking UI for fluid interaction

## 🚀 Quick Start

### Easy Installation (Recommended)

**For Ubuntu/Debian users:**
1. Download the `.deb` package from [GitHub Releases](https://github.com/Lusan-sapkota/TimeRing/releases) or [SourceForge](https://sourceforge.net/projects/timering/)
2. Install with: `sudo dpkg -i timering_1.0.0_all.deb`
3. Launch from your application menu or run `timering` in terminal

### Manual Installation

<details>
<summary>Click to expand manual installation instructions</summary>

#### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip git

# Fedora/RHEL
sudo dnf install python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git
```

#### Installation Steps
```bash
# 1. Clone the repository
git clone https://github.com/Lusan-sapkota/TimeRing.git
cd TimeRing

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 main.py
```

</details>

## 📚 Usage Guide

### Creating Your First Timer

1. **Enter timer details:**
   - Name: Give your timer a meaningful name (e.g., "Work Session", "Tea Brewing")
   - Duration: Set time in minutes
   - Description: Click the icon to add detailed notes (optional)
   - Sound: Click the icon to choose a custom alarm sound (optional)

2. **Start the timer:** Click **"Create Timer"** and watch it appear in your active timers list

### Managing Active Timers

Each timer card displays:

- **Timer Name & Icon:** Always visible, with icon reflecting status (play, pause, bell, alarm)
- **Description:** Optional, shown below the name if provided
- **Time Display:** Shows remaining time and original duration
- **Status Row:** Icon + text for Running, Paused, Ringing, or Time's Up
- **Controls:**  
  - **Edit:** Change both timer name and description  
  - **Change Sound:** Select a custom notification sound  
  - **Pause/Resume:** Toggle timer state  
  - **Rerun:** Restart timer from original duration  
  - **Stop:** Halt timer and silence alarms  
  ### Timer Actions & States

  Below is a modular overview of timer states, their icons, colors, and available actions:

  | **State**   | **Icon**                                   | **Color** | **Available Actions**                  |
  |:------------|:-------------------------------------------|:----------|:---------------------------------------|
  | **Running** | ![](./images/icons/play.svg)               | Green     | Pause, Stop, Edit, Change Sound        |
  | **Paused**  | ![](./images/icons/pause.svg)              | Orange    | Resume, Stop, Edit, Change Sound       |
  | **Ringing** | ![](./images/icons/bell.svg)               | Red       | Stop (to silence)                      |
  | **Time's Up** | ![](./images/icons/alarm.svg)            | Red       | Rerun, Edit, Delete                    |

  > **Tip:**  
  > - **Delete:** Remove timer  
  > - Icons visually indicate each timer state:  
  >   - ![](./images/icons/play.svg) Running  
  >   - ![](./images/icons/pause.svg) Paused  
  >   - ![](./images/icons/bell.svg) Ringing  
  >   - ![](./images/icons/alarm.svg) Time's Up  

### Active Timer Block

A large, dedicated display at the top shows your current focus timer:

- **Timer Name & Description:** Centered, always visible
- **Time Display:** Large, easy-to-read countdown
- **Status Row:** Centered icon and text for Running, Paused, Ringing, or Time's Up
- **Controls:**  
  - **Previous/Next:** Switch between running timers  
  - **Pause/Resume:** Toggle timer state  
  - **Stop:** Halt timer and silence alarms
- **Automatic Priority:** The most important timer (ringing, running, or paused) is always shown here

### Settings & Customization

You will get Icon in right side of the header for each

- **Settings:**  
  - Set global default notification sound  
  - Enable/disable desktop notifications  
  - Auto-start timers on launch  
  - Configure notification urgency  
  - Advanced settings for update checks and sound looping
- **Help:** User guide and troubleshooting tips
- **About:** Version, developer, and system info

## 🛠️ Advanced Configuration

### Configuration Files
TimeRing stores settings in `~/.config/TimeRing/`:
- `settings.json` - Application preferences and defaults
- `timers.json` - Current timer states (auto-saved)

### Custom Styling
Modify `style.qss` to customize the appearance:
```css
/* Example: Change primary button color */
QPushButton#startButton {
    background-color: #4CAF50;
    border-radius: 8px;
}

/* Example: Customize timer cards */
QFrame#timerCard {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
}
```

### Command Line Options
```bash
# Start minimized to system tray
python3 main.py --minimized

# Load custom style sheet
python3 main.py --style custom.qss
```

## 🖥️ Platform Compatibility

**Primary Platform:** Linux (Ubuntu 20.04+, Fedora 34+, Arch Linux)

**Tested Desktop Environments:**
- KDE Plasma 5.20+
- GNOME 3.38+
- XFCE 4.16+
- Cinnamon 5.0+

**Windows/macOS:** While TimeRing may run on other platforms with Python and PyQt5, some features (particularly desktop notifications and audio) are optimized for Linux and may require additional configuration.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Ways to Contribute
- 🐛 **Report bugs** via [GitHub Issues](https://github.com/Lusan-sapkota/TimeRing/issues)
- 💡 **Suggest features** in our [Discussions](https://github.com/Lusan-sapkota/TimeRing/discussions)
- 🔧 **Submit pull requests** with improvements
- 📖 **Improve documentation** and examples
- 🌍 **Add translations** for internationalization

### Development Setup
```bash
# Fork the repository and clone your fork
git clone https://github.com/YOUR_USERNAME/TimeRing.git
cd TimeRing

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run the application
python3 main.py
```

### Pull Request Guidelines
1. Fork the repository and create a feature branch
2. Write clear, commented code following PEP 8
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request with a clear description

## 📈 Roadmap

### Upcoming Features
- [ ] **Cross-platform support** (Windows, macOS)
- [ ] **Timer templates** for common use cases
- [ ] **Statistics and analytics** (time tracking, productivity metrics)
- [ ] **Themes and appearance customization**
- [ ] **Integration with productivity apps** (Todoist, Notion, etc.)
- [ ] **Mobile companion app** for remote control

### Version History
- **v1.0.0** - Initial release with core timer functionality
- **v0.9.0** - Beta release with notification system
- **v0.8.0** - Alpha release with basic timer features

## 🆘 Support

### Getting Help
- 📖 **Documentation**: Check this README and inline help
- 💬 **Community**: Join our [GitHub Discussions](https://github.com/Lusan-sapkota/TimeRing/discussions)
- 🐛 **Bug Reports**: Use our [Issue Tracker](https://github.com/Lusan-sapkota/TimeRing/issues)

### Common Issues
<details>
<summary>Audio notifications not working</summary>

Ensure VLC is installed:
```bash
sudo apt install vlc  # Ubuntu/Debian
sudo dnf install vlc  # Fedora
```
</details>

<details>
<summary>Desktop notifications not showing</summary>

Check that `libnotify` is installed:
```bash
sudo apt install libnotify-bin  # Ubuntu/Debian
```
</details>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Lusan Sapkota**
- GitHub: [@Lusan-sapkota](https://github.com/Lusan-sapkota)
- Email: [Contact via GitHub](sapkotalusan@gmail.com)
- Website: [Contact via Website](www.lusansapkota.com.np)

## 🙏 Acknowledgments

- PyQt5 community for the excellent GUI framework
- Contributors who have helped improve TimeRing
- Beta testers who provided valuable feedback
- Icon designers for beautiful system icons

---

<div align="center">
  
  **⭐ Star this repository if TimeRing helps you manage your time better!**
  
  Made with ❤️ for productivity enthusiasts
  
  [Report Bug](https://github.com/Lusan-sapkota/TimeRing/issues) • 
  [Request Feature](https://github.com/Lusan-sapkota/TimeRing/discussions) • 
  [Contribute](https://github.com/Lusan-sapkota/TimeRing/blob/main/CONTRIBUTING.md)
  
</div>