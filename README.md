# TimeRing - A Modern Desktop Timer Application

<div align="center">
  <img src="images/logo.png" alt="TimeRing Logo" width="128" height="128">
  
  **A lightweight, modern, and beautiful timer application for your desktop.**
  
  [![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Lusan-sapkota/TimeRing)
  [![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)](#platform-compatibility)
  
  [**View on GitHub**](https://github.com/Lusan-sapkota/TimeRing)
</div>

<div align="center">
  <img src="./demo/images/timering.png" alt="TimeRing Screenshot" width="700">
</div>

TimeRing is a versatile and user-friendly timer application designed to help you manage your time effectively. Whether you're working, studying, or cooking, TimeRing provides a clean and intuitive interface to run multiple timers at once. Built with PyQt5, it's designed with a focus on Linux but is architected to be cross-platform.

## ✨ Features

### 🎯 Core Functionality

- **Multiple Concurrent Timers**: Run as many timers as you need simultaneously.
- **Custom Timer Names & Descriptions**: Personalize each timer with a name and a detailed description.
- **Pause, Resume, and Rerun**: Full control over the timer lifecycle, including the ability to rerun a finished timer instantly.
- **Persistent State**: Automatically saves and restores your timers across application restarts.

### 🔊 Audio & Notifications

- **Custom Notification Sounds**: Assign unique sounds for each timer or use a global default.
- **Sound Looping**: Audio alerts play continuously until you stop them.
- **Native Desktop Notifications**: Integrates with Linux desktop environments (like KDE and GNOME) to show system notifications.
- **Configurable Urgency**: Set notification urgency to low, normal, or critical.

### 🎨 Modern User Interface

- **Clean, Modern Design**: A polished UI with a slide-in menu and smooth animations.
- **System-Native Icons**: Uses icons from your system's theme for a consistent and native feel.
- **Responsive Layout**: A non-blocking UI that stays responsive.
- **Clear Status Indicators**: Visual feedback for running, paused, ringing, and finished timers.

### ⚙️ Advanced Features

- **Timer Navigation**: Navigate between multiple running timers with Previous/Next buttons in the active timer display.
- **Enhanced Status Management**: Clear visual distinction between paused, finished, and time's up states.
- **Auto Update Check**: Automatically check for new releases and update with one click.
- **Compact Mode**: Responsive design that adapts to smaller screens (720p displays).
- **Smooth Scrolling**: Optimized timer list with pixel-perfect scrolling and position preservation.
- **CLI Support**: Basic command-line arguments for automation.
- **External Styling**: Customizable appearance via Qt's QSS stylesheets.
- **Settings Management**: Configure default sounds, notifications, and application behavior.

## 📦 Installation

For an easy installation on Debian-based systems (like Ubuntu), a `.deb` package will be available in the [GitHub Releases](https://github.com/Lusan-sapkota/TimeRing/releases) section and on SourceForge. This is the recommended method for most users.

For other systems or for development, you can install from source.

### Prerequisites

Ensure Python 3.11+ and `pip` are installed on your system.

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Fedora/RHEL
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip

```

### Installation from Source

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Lusan-sapkota/TimeRing.git
    cd TimeRing
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, you would use `venv\Scripts\activate`.*

3. **Install dependencies:**

    Inside the activated virtual environment, install the required Python packages.

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the application:**

    ```bash
    python3 main.py
    ```

## 🚀 Usage

### Creating a Timer

1. Enter a name for your timer.
2. Set the duration in minutes.
3. Optionally, click the **description icon** to add more details.
4. Optionally, click the **sound icon** to select a custom alarm sound.
5. Click **"Start Timer"** to begin.

### Managing Active Timers

Each active timer card displays its name, remaining time, and status. The action buttons change based on the timer's state:

- **Running**: Pause, Stop, Edit Description, Change Sound.
- **Paused**: Resume, Stop, Edit Description, Change Sound.
- **Ringing**: A **Stop** button is shown to silence the alarm. The card turns yellow.
- **Finished**: A **Rerun** button appears, allowing you to start the same timer again instantly.

### Active Timer Display

The large active timer display shows the currently selected running timer with enhanced controls:

- **Previous/Next Buttons**: Navigate between multiple running timers.
- **Enhanced Status**: Clear distinction between "Time's Up", "Paused", and "Running" states.
- **Disabled Controls**: Resume button is properly disabled for finished timers.

### Menu Header

Click each menu icon to access:

- **Settings**: Change the default sound and open the preferences dialog.
- **Help**: Quick guides and feature overviews.
- **About**: Information about the application.

## Platform Compatibility

This application is developed and tested primarily on **Linux**. Many features, especially those relying on system libraries like desktop notifications (`libnotify`) and audio (`VLC`), are tailored for a Linux environment.

While it may run on **Windows** or **macOS** with Python and PyQt5 installed, some functionalities might not work as expected out-of-the-box. The notification system, in particular, would require platform-specific implementation to work on other operating systems.

## 🔧 Configuration

TimeRing stores its configuration files in `~/.config/TimeRing/`:

- `settings.json`: Application preferences.
- `timers.json`: The state of all active timers.

## 🎨 Customization

You can customize the application's appearance by editing `style.qss`. This file uses standard Qt CSS syntax. For example, to change the primary button color:

```css
QPushButton#startButton {
    background-color: #4CAF50; /* A nice green */
}
```

## 🤝 Contributing

Contributions are welcome! If you'd like to improve TimeRing, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix.
3. Make your changes and test them thoroughly.
4. Submit a pull request to the `main` branch.

You can find the repository here: [https://github.com/Lusan-sapkota/TimeRing](https://github.com/Lusan-sapkota/TimeRing)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👤 Author

Lusan Sapkota

- GitHub: [@Lusan-sapkota](https://github.com/Lusan-sapkota)

---

<div align="center">
  Made with ❤️.
</div>
