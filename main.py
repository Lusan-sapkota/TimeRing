import sys
import json
import os
import subprocess
import threading
import time
import argparse
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QHBoxLayout, QLabel, QTextEdit, QDialog, QDialogButtonBox,
                             QFileDialog, QGroupBox, QCheckBox, QTabWidget, QComboBox,
                             QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGridLayout,
                             QMessageBox, QDesktopWidget)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette
import vlc

# Application metadata
APP_NAME = "TimeRing"
APP_VERSION = "1.0.0"
APP_DEVELOPER = "Lusan Sapkota"


def detect_system_theme():
    """Detect if the system is using dark theme"""
    try:
        # Try to detect theme using Qt's palette
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.Window)
            # If background is darker, assume dark theme
            return bg_color.lightness() < 128
        
        # Fallback: check environment variables
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'gnome' in desktop:
            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                      capture_output=True, text=True, timeout=2)
                return 'dark' in result.stdout.lower()
            except:
                pass
        elif 'kde' in desktop:
            try:
                # Check KDE theme
                result = subprocess.run(['kreadconfig5', '--group', 'General', '--key', 'ColorScheme'], 
                                      capture_output=True, text=True, timeout=2)
                return 'dark' in result.stdout.lower()
            except:
                pass
    except:
        pass
    
    return False  # Default to light theme


def apply_theme_to_widget(widget, is_dark=None):
    """Apply theme property to widget and its children"""
    if is_dark is None:
        is_dark = detect_system_theme()
    
    widget.setProperty("darkTheme", is_dark)
    
    # Apply to all child widgets
    for child in widget.findChildren(QWidget):
        child.setProperty("darkTheme", is_dark)
    
    # Refresh styles
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - A lightweight desktop timer application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {APP_NAME.lower()}                    # Launch GUI normally
  {APP_NAME.lower()} --set-sound /path/to/sound.mp3  # Set default sound and launch
  {APP_NAME.lower()} --version          # Show version information
  {APP_NAME.lower()} --help             # Show this help message

For more information, visit the Help section in the application drawer.
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'{APP_NAME} {APP_VERSION}\nDeveloper: {APP_DEVELOPER}'
    )
    
    parser.add_argument(
        '--set-sound',
        metavar='PATH',
        help='Set default alarm sound file path'
    )
    
    return parser.parse_args()


class SettingsModalDialog(QDialog):
    """Modal settings dialog with proper responsive design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Settings")
        header.setObjectName("titleLabel")
        header.setStyleSheet("font-size: 20pt; font-weight: 700; margin-bottom: 16px;")
        layout.addWidget(header)
        
        # Sound settings section
        sound_frame = QFrame()
        sound_frame.setObjectName("settingsFrame")
        sound_layout = QVBoxLayout(sound_frame)
        
        sound_label = QLabel("Default Sound")
        sound_label.setObjectName("subtitleLabel")
        sound_layout.addWidget(sound_label)
        
        # Current sound display
        current_sound = ""
        if self.parent_window:
            current_sound = self.parent_window.settings.get("default_sound", "")
        
        self.sound_path_label = QLabel(current_sound or "Built-in default sound")
        self.sound_path_label.setWordWrap(True)
        self.sound_path_label.setObjectName("statusLabel")
        sound_layout.addWidget(self.sound_path_label)
        
        # Sound buttons
        sound_buttons = QHBoxLayout()
        
        browse_btn = QPushButton("Browse Files")
        browse_btn.setIcon(self.get_icon("folder"))
        browse_btn.clicked.connect(self.browse_sound)
        sound_buttons.addWidget(browse_btn)
        
        preview_btn = QPushButton("Preview")
        preview_btn.setIcon(self.get_icon("play"))
        preview_btn.clicked.connect(self.preview_sound)
        sound_buttons.addWidget(preview_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self.reset_sound)
        sound_buttons.addWidget(reset_btn)
        
        sound_layout.addLayout(sound_buttons)
        layout.addWidget(sound_frame)
        
        # Quick settings
        quick_frame = QFrame()
        quick_layout = QVBoxLayout(quick_frame)
        
        quick_label = QLabel("Quick Settings")
        quick_label.setObjectName("subtitleLabel")
        quick_layout.addWidget(quick_label)
        
        self.notifications_check = QCheckBox("Enable desktop notifications")
        if self.parent_window:
            self.notifications_check.setChecked(self.parent_window.settings.get("show_notifications", True))
        quick_layout.addWidget(self.notifications_check)
        
        self.auto_start_check = QCheckBox("Auto-start timers on launch")
        if self.parent_window:
            self.auto_start_check.setChecked(self.parent_window.settings.get("auto_start_timers", True))
        quick_layout.addWidget(self.auto_start_check)
        
        layout.addWidget(quick_frame)
        
        # Advanced settings button
        advanced_btn = QPushButton("Advanced Settings")
        advanced_btn.setObjectName("secondaryButton")
        advanced_btn.clicked.connect(self.open_advanced_settings)
        layout.addWidget(advanced_btn)
        
        layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Media player for preview
        self.preview_player = vlc.MediaPlayer()
        
    def get_icon(self, name):
        """Get icon by name with fallback"""
        try:
            # Try to get system icon first
            icon = self.style().standardIcon(getattr(self.style(), f'SP_{name.title()}Icon', None))
            if not icon.isNull():
                return icon
        except:
            pass
        
        # Fallback to Unicode symbols
        icon_map = {
            "folder": "📁",
            "play": "▶️",
            "settings": "⚙️",
            "help": "❓",
            "info": "ℹ️"
        }
        return QIcon()  # Return empty icon, text will show
    
    def browse_sound(self):
        """Browse for sound file"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg *.m4a)")
        file_dialog.setWindowTitle("Select Default Sound")
        
        if file_dialog.exec_() == QFileDialog.Accepted:
            sound_path = file_dialog.selectedFiles()[0]
            self.sound_path_label.setText(sound_path)
            
    def preview_sound(self):
        """Preview the selected sound"""
        sound_path = self.sound_path_label.text()
        if sound_path == "Built-in default sound":
            sound_path = self.parent_window.alarm_sound if self.parent_window else ""
            
        if sound_path and os.path.exists(sound_path):
            if self.preview_player:
                self.preview_player.stop()
                self.preview_player.set_mrl(sound_path)
                self.preview_player.play()
    
    def reset_sound(self):
        """Reset to default sound"""
        self.sound_path_label.setText("Built-in default sound")
        
    def open_advanced_settings(self):
        """Open the advanced settings dialog"""
        if self.parent_window:
            dialog = SettingsDialog(self.parent_window.settings, self.parent_window)
            if dialog.exec_() == QDialog.Accepted:
                self.parent_window.settings.update(dialog.get_settings())
                self.parent_window.save_settings()
    
    def save_and_close(self):
        """Save settings and close"""
        if self.parent_window:
            # Update sound setting
            sound_text = self.sound_path_label.text()
            if sound_text == "Built-in default sound":
                self.parent_window.settings["default_sound"] = ""
            else:
                self.parent_window.settings["default_sound"] = sound_text
                self.parent_window.alarm_sound = sound_text
            
            # Update other settings
            self.parent_window.settings["show_notifications"] = self.notifications_check.isChecked()
            self.parent_window.settings["auto_start_timers"] = self.auto_start_check.isChecked()
            
            self.parent_window.save_settings()
        
        self.accept()
    
    def closeEvent(self, event):
        if self.preview_player:
            self.preview_player.stop()
        event.accept()


class HelpModalDialog(QDialog):
    """Modal help dialog with user guide"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help & Guide")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QLabel("Help & User Guide")
        header.setObjectName("titleLabel")
        header.setStyleSheet("font-size: 20pt; font-weight: 700; margin-bottom: 16px;")
        layout.addWidget(header)
        
        # Scrollable help content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        help_content = QLabel("""
<h2 style="color: #3b82f6; margin-top: 24px;">🚀 Quick Start</h2>
<p><strong>Creating Your First Timer:</strong></p>
<ol>
<li>Enter a descriptive name in the "Timer Name" field</li>
<li>Set the duration in minutes</li>
<li>Optionally add a description by clicking "Add Description"</li>
<li>Choose a custom sound with "Select Sound" (optional)</li>
<li>Click "Start Timer" to begin</li>
</ol>

<h2 style="color: #3b82f6; margin-top: 24px;">⏱️ Managing Active Timers</h2>
<p>Each timer shows:</p>
<ul>
<li><strong>Timer name and remaining time</strong></li>
<li><strong>Status:</strong> Running ▶️, Paused ⏸️, or Ringing 🔔</li>
<li><strong>Description preview</strong> (if added)</li>
</ul>

<p><strong>Available Actions:</strong></p>
<ul>
<li><strong>✏️ Edit:</strong> Modify timer description</li>
<li><strong>🔊 Sound:</strong> Change notification sound</li>
<li><strong>⏸️/▶️ Pause/Resume:</strong> Control timer execution</li>
<li><strong>🛑 Stop:</strong> Remove timer completely</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">🔔 Notifications</h2>
<p>When a timer completes:</p>
<ul>
<li>Desktop notification appears (KDE/GNOME compatible)</li>
<li>Sound alert plays continuously until stopped</li>
<li>Timer status changes to "Ringing"</li>
<li>Description included in notification (if enabled)</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">⚙️ Settings & Customization</h2>
<p><strong>Sound Settings:</strong></p>
<ul>
<li>Set global default notification sound</li>
<li>Per-timer custom sounds</li>
<li>Preview sounds before applying</li>
<li>Support for MP3, WAV, OGG formats</li>
</ul>

<p><strong>Behavior Settings:</strong></p>
<ul>
<li>Auto-start timers on app launch</li>
<li>Save timer states between sessions</li>
<li>Notification urgency levels</li>
<li>Loop sound until manually stopped</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">⌨️ Command Line Usage</h2>
<p>TimeRing supports command line arguments:</p>
<ul>
<li><code>timering --help</code> - Show help</li>
<li><code>timering --version</code> - Show version</li>
<li><code>timering --set-sound /path/to/sound.mp3</code> - Set default sound</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">🎨 Theming</h2>
<p>TimeRing automatically adapts to your system theme:</p>
<ul>
<li><strong>Light Mode:</strong> Clean, bright interface</li>
<li><strong>Dark Mode:</strong> Easy on the eyes for low-light use</li>
<li>Automatic detection of KDE and GNOME themes</li>
<li>Responsive design that scales with window size</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">💡 Tips & Tricks</h2>
<ul>
<li><strong>Multiple Timers:</strong> Run as many timers as needed simultaneously</li>
<li><strong>Descriptions:</strong> Use descriptions for context (up to 200 words)</li>
<li><strong>Custom Sounds:</strong> Different sounds help identify timer purpose</li>
<li><strong>Persistence:</strong> Timers resume after app restart (if enabled)</li>
<li><strong>Keyboard Navigation:</strong> Use Tab key to navigate between fields</li>
</ul>

<h2 style="color: #3b82f6; margin-top: 24px;">🔧 Troubleshooting</h2>
<p><strong>Sound not playing:</strong></p>
<ul>
<li>Check VLC is installed: <code>sudo apt install vlc</code></li>
<li>Verify audio file format and permissions</li>
<li>Test with preview button in sound settings</li>
</ul>

<p><strong>Notifications not appearing:</strong></p>
<ul>
<li>Install notification service: <code>sudo apt install libnotify-bin</code></li>
<li>Check desktop environment notification settings</li>
<li>Verify urgency level in advanced settings</li>
</ul>
        """)
        help_content.setWordWrap(True)
        help_content.setTextFormat(Qt.RichText)
        help_content.setStyleSheet("line-height: 1.6; padding: 16px;")
        scroll_area.setWidget(help_content)
        
        layout.addWidget(scroll_area)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class InfoModalDialog(QDialog):
    """Modal info dialog with app information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("About TimeRing")
        self.setModal(True)
        self.resize(400, 350)
        self.setup_ui()
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # App logo
        logo_label = QLabel()
        if self.parent_window:
            logo_path = os.path.join(self.parent_window.app_dir, "images", "logo.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # App info
        app_info = QLabel(f"""
<div style="text-align: center;">
<h1 style="color: #3b82f6; margin: 16px 0; font-size: 24pt;">{APP_NAME}</h1>
<p style="color: #6b7280; margin: 8px 0; font-size: 12pt;"><strong>Version:</strong> {APP_VERSION}</p>
<p style="color: #6b7280; margin: 8px 0; font-size: 12pt;"><strong>Developer:</strong> {APP_DEVELOPER}</p>
<p style="color: #374151; margin: 16px 0; font-size: 11pt; line-height: 1.5;">
A modern, lightweight timer application designed for Linux desktop environments.
Features multiple concurrent timers, custom notifications, and seamless 
integration with KDE and GNOME.
</p>
</div>
        """)
        app_info.setWordWrap(True)
        app_info.setTextFormat(Qt.RichText)
        app_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_info)
        
        # System info
        system_info = QLabel(f"""
<div style="text-align: center; margin-top: 16px;">
<p style="color: #6b7280; font-size: 10pt;">
<strong>System Theme:</strong> {'Dark' if detect_system_theme() else 'Light'}<br>
<strong>Desktop:</strong> {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}<br>
<strong>Python:</strong> {sys.version.split()[0]}
</p>
</div>
        """)
        system_info.setTextFormat(Qt.RichText)
        system_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(system_info)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class TimerDescriptionDialog(QDialog):
    def __init__(self, description="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timer Description")
        self.setMinimumWidth(400)
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        layout = QVBoxLayout(self)
        
        # Description text edit
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter timer description (max 200 words)")
        self.description_edit.setText(description)
        apply_theme_to_widget(self.description_edit, is_dark)
        layout.addWidget(self.description_edit)
        
        # Word count label
        self.word_count_label = QLabel("0/200 words")
        apply_theme_to_widget(self.word_count_label, is_dark)
        layout.addWidget(self.word_count_label)
        
        # Update word count when text changes
        self.description_edit.textChanged.connect(self.update_word_count)
        self.update_word_count()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        apply_theme_to_widget(button_box, is_dark)
        layout.addWidget(button_box)
    
    def update_word_count(self):
        text = self.description_edit.toPlainText().strip()
        word_count = len(text.split()) if text else 0
        self.word_count_label.setText(f"{word_count}/200 words")
        
        # Disable OK button if over word limit
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            ok_button = button_box.button(QDialogButtonBox.Ok)
            if ok_button:
                ok_button.setEnabled(word_count <= 200)
    
    def get_description(self):
        return self.description_edit.toPlainText().strip()


class SoundSelectionDialog(QDialog):
    def __init__(self, current_sound="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Notification Sound")
        self.setMinimumWidth(400)
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.current_sound = current_sound
        
        layout = QVBoxLayout(self)
        
        # Sound path display
        self.sound_path_label = QLabel(current_sound or "Default sound")
        self.sound_path_label.setWordWrap(True)
        apply_theme_to_widget(self.sound_path_label, is_dark)
        layout.addWidget(self.sound_path_label)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_sound)
        apply_theme_to_widget(self.browse_button, is_dark)
        layout.addWidget(self.browse_button)
        
        # Preview button
        self.preview_button = QPushButton("Preview Sound")
        self.preview_button.clicked.connect(self.preview_sound)
        apply_theme_to_widget(self.preview_button, is_dark)
        layout.addWidget(self.preview_button)
        
        # Use default button
        self.default_button = QPushButton("Use Default Sound")
        self.default_button.clicked.connect(self.use_default_sound)
        apply_theme_to_widget(self.default_button, is_dark)
        layout.addWidget(self.default_button)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        apply_theme_to_widget(button_box, is_dark)
        layout.addWidget(button_box)
        
        # Media player for preview
        self.preview_player = vlc.MediaPlayer()
    
    def browse_sound(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg)")
        file_dialog.setWindowTitle("Select Notification Sound")
        
        if file_dialog.exec_() == QFileDialog.Accepted:
            self.current_sound = file_dialog.selectedFiles()[0]
            self.sound_path_label.setText(self.current_sound)
    
    def preview_sound(self):
        sound_to_play = self.current_sound
        if not sound_to_play or not os.path.exists(sound_to_play):
            # Use default sound from parent window
            parent_app = self.parent()
            if parent_app and isinstance(parent_app, TimerApp) and hasattr(parent_app, "alarm_sound"):
                sound_to_play = parent_app.alarm_sound
        
        if sound_to_play and os.path.exists(sound_to_play):
            if self.preview_player:
                self.preview_player.stop()
                self.preview_player.set_mrl(sound_to_play)
                self.preview_player.play()
    
    def use_default_sound(self):
        self.current_sound = ""
        self.sound_path_label.setText("Default sound")
    
    def get_sound_path(self):
        return self.current_sound
    
    def closeEvent(self, event):
        if self.preview_player:
            self.preview_player.stop()
        event.accept()


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TimeRing Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.settings = settings.copy()  # Make a copy to work with
        
        layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.general_tab = QWidget()
        self.notifications_tab = QWidget()
        self.sounds_tab = QWidget()
        
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.notifications_tab, "Notifications")
        self.tabs.addTab(self.sounds_tab, "Sounds")
        
        # Apply theme to tabs and tab widgets
        apply_theme_to_widget(self.tabs, is_dark)
        apply_theme_to_widget(self.general_tab, is_dark)
        apply_theme_to_widget(self.notifications_tab, is_dark)
        apply_theme_to_widget(self.sounds_tab, is_dark)
        
        layout.addWidget(self.tabs)
        
        # Set up each tab
        self.setup_general_tab()
        self.setup_notifications_tab()
        self.setup_sounds_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        apply_theme_to_widget(button_box, is_dark)
        layout.addWidget(button_box)
        
        # Media player for sound preview
        self.preview_player = vlc.MediaPlayer()
    
    def setup_general_tab(self):
        layout = QVBoxLayout(self.general_tab)
        
        # Auto-start timers on app launch
        self.auto_start_check = QCheckBox("Auto-start timers on application launch")
        self.auto_start_check.setChecked(self.settings.get("auto_start_timers", True))
        layout.addWidget(self.auto_start_check)
        
        # Save timer state on exit
        self.save_state_check = QCheckBox("Save timer state on exit")
        self.save_state_check.setChecked(self.settings.get("save_state", True))
        layout.addWidget(self.save_state_check)
        
        # Add spacer
        layout.addStretch()
    
    def setup_notifications_tab(self):
        layout = QVBoxLayout(self.notifications_tab)
        
        # Show desktop notifications
        self.show_notifications_check = QCheckBox("Show desktop notifications")
        self.show_notifications_check.setChecked(self.settings.get("show_notifications", True))
        layout.addWidget(self.show_notifications_check)
        
        # Include description in notifications
        self.include_desc_check = QCheckBox("Include timer description in notifications")
        self.include_desc_check.setChecked(self.settings.get("include_description", True))
        layout.addWidget(self.include_desc_check)
        
        # Notification urgency
        urgency_layout = QHBoxLayout()
        urgency_layout.addWidget(QLabel("Notification urgency:"))
        
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(["Low", "Normal", "Critical"])
        current_urgency = self.settings.get("notification_urgency", "Normal")
        self.urgency_combo.setCurrentText(current_urgency)
        urgency_layout.addWidget(self.urgency_combo)
        
        layout.addLayout(urgency_layout)
        
        # Add spacer
        layout.addStretch()
    
    def setup_sounds_tab(self):
        layout = QVBoxLayout(self.sounds_tab)
        
        # Default sound selection
        sound_group = QGroupBox("Default Sound")
        sound_layout = QVBoxLayout(sound_group)
        
        # Current default sound
        self.default_sound_path = self.settings.get("default_sound", "")
        display_path = self.default_sound_path or "Built-in default sound"
        self.sound_path_label = QLabel(display_path)
        self.sound_path_label.setWordWrap(True)
        sound_layout.addWidget(self.sound_path_label)
        
        # Sound selection buttons
        buttons_layout = QHBoxLayout()
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_sound)
        buttons_layout.addWidget(self.browse_button)
        
        # Preview button
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_sound)
        buttons_layout.addWidget(self.preview_button)
        
        # Reset to default button
        self.reset_button = QPushButton("Use Built-in")
        self.reset_button.clicked.connect(self.use_default_sound)
        buttons_layout.addWidget(self.reset_button)
        
        sound_layout.addLayout(buttons_layout)
        layout.addWidget(sound_group)
        
        # Sound options
        options_group = QGroupBox("Sound Options")
        options_layout = QVBoxLayout(options_group)
        
        # Loop sound
        self.loop_sound_check = QCheckBox("Loop sound until stopped")
        self.loop_sound_check.setChecked(self.settings.get("loop_sound", True))
        options_layout.addWidget(self.loop_sound_check)
        
        layout.addWidget(options_group)
        
        # Add spacer
        layout.addStretch()
    
    def browse_sound(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg)")
        file_dialog.setWindowTitle("Select Default Sound")
        
        if file_dialog.exec_() == QFileDialog.Accepted:
            self.default_sound_path = file_dialog.selectedFiles()[0]
            self.sound_path_label.setText(self.default_sound_path)
    
    def preview_sound(self):
        sound_to_play = self.default_sound_path
        if not sound_to_play or not os.path.exists(sound_to_play):
            # Use built-in sound
            parent_app = self.parent()
            if parent_app and isinstance(parent_app, TimerApp) and hasattr(parent_app, "alarm_sound"):
                sound_to_play = parent_app.alarm_sound
        
        if sound_to_play and os.path.exists(sound_to_play):
            if self.preview_player:
                self.preview_player.stop()
                self.preview_player.set_mrl(sound_to_play)
                self.preview_player.play()
    
    def use_default_sound(self):
        self.default_sound_path = ""
        self.sound_path_label.setText("Built-in default sound")
    
    def get_settings(self):
        # Update settings from UI
        self.settings["auto_start_timers"] = self.auto_start_check.isChecked()
        self.settings["save_state"] = self.save_state_check.isChecked()
        self.settings["show_notifications"] = self.show_notifications_check.isChecked()
        self.settings["include_description"] = self.include_desc_check.isChecked()
        self.settings["notification_urgency"] = self.urgency_combo.currentText()
        self.settings["default_sound"] = self.default_sound_path
        self.settings["loop_sound"] = self.loop_sound_check.isChecked()
        
        return self.settings
    
    def closeEvent(self, event):
        if self.preview_player:
            self.preview_player.stop()
        event.accept()


class TimerApp(QMainWindow):
    def __init__(self, cli_args=None):
        super().__init__()
        self.cli_args = cli_args
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 600, 700)
        self.setMinimumSize(500, 600)  # Set minimum size for scalability
        
        # Configuration
        self.config_dir = os.path.expanduser(f"~/.config/{APP_NAME}")
        self.state_file = os.path.join(self.config_dir, "timers.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # Get the application directory
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.alarm_sound = os.path.join(self.app_dir, "sounds", "timesup.mp3")
        
        # Set application icon
        icon_path = os.path.join(self.app_dir, "images", "logo.png")
        self.setWindowIcon(QIcon(icon_path))
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load settings
        self.settings = self.load_settings()
        
        # Handle CLI arguments
        self.handle_cli_args()
        
        # Active timers and media players
        self.timers = []
        self.media_players = {}
        self.timer_threads = {}
        self.timer_events = {}
        
        # Initialize UI
        self.init_ui()
        
        # Load saved timers
        self.load_timers()
        
        # Update timer display every second
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_timers_display)
        self.update_timer.start(1000)
    
    def handle_cli_args(self):
        """Handle command line arguments"""
        if self.cli_args and self.cli_args.set_sound:
            sound_path = self.cli_args.set_sound
            if os.path.exists(sound_path):
                self.settings["default_sound"] = sound_path
                self.alarm_sound = sound_path
                self.save_settings()
                print(f"Default sound set to: {sound_path}")
            else:
                print(f"Error: Sound file not found: {sound_path}")
                sys.exit(1)
    
    def init_ui(self):
        # Main widget container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(main_widget, is_dark)
        
        # Header with menu buttons and title
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # App Title
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Menu buttons
        menu_layout = QHBoxLayout()
        menu_layout.setSpacing(8)
        
        # Settings button
        settings_btn = QPushButton("⚙️")
        settings_btn.setObjectName("menuButton")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self.open_settings_modal)
        menu_layout.addWidget(settings_btn)
        
        # Help button
        help_btn = QPushButton("❓")
        help_btn.setObjectName("menuButton")
        help_btn.setToolTip("Help & Guide")
        help_btn.clicked.connect(self.open_help_modal)
        menu_layout.addWidget(help_btn)
        
        # Info button
        info_btn = QPushButton("ℹ️")
        info_btn.setObjectName("menuButton")
        info_btn.setToolTip("About TimeRing")
        info_btn.clicked.connect(self.open_info_modal)
        menu_layout.addWidget(info_btn)
        
        header_layout.addLayout(menu_layout)
        main_layout.addWidget(header_widget)
        
        # Prominent Add Timer button - full width
        self.add_timer_button = QPushButton("➕ Add Timer")
        self.add_timer_button.setObjectName("addTimerButton")
        self.add_timer_button.clicked.connect(self.open_timer_creation_dialog)
        main_layout.addWidget(self.add_timer_button)

        # Large active timer display
        self.active_timer_frame = QFrame()
        self.active_timer_frame.setVisible(False)  # Hidden initially
        self.active_timer_frame.setObjectName("activeTimerFrame")
        active_timer_layout = QVBoxLayout(self.active_timer_frame)
        
        # Active timer title
        active_timer_title = QLabel("Active Timer")
        active_timer_title.setObjectName("subtitleLabel")
        active_timer_layout.addWidget(active_timer_title)
        
        # Large timer display
        self.large_timer_name = QLabel("Timer Name")
        self.large_timer_name.setObjectName("timerNameLabel")
        self.large_timer_name.setAlignment(Qt.AlignCenter)
        active_timer_layout.addWidget(self.large_timer_name)
        
        self.large_timer_time = QLabel("00:00:00")
        self.large_timer_time.setObjectName("largeTimerDisplay")
        self.large_timer_time.setAlignment(Qt.AlignCenter)
        active_timer_layout.addWidget(self.large_timer_time)
        
        self.large_timer_status = QLabel("Running")
        self.large_timer_status.setObjectName("statusLabel")
        self.large_timer_status.setAlignment(Qt.AlignCenter)
        active_timer_layout.addWidget(self.large_timer_status)
        
        # Large timer controls
        large_timer_controls = QHBoxLayout()
        
        self.large_pause_button = QPushButton("⏸️ Pause")
        self.large_pause_button.setObjectName("warningButton")
        self.large_pause_button.clicked.connect(lambda: self.toggle_timer(self.get_primary_timer_index()))
        large_timer_controls.addWidget(self.large_pause_button)
        
        self.large_stop_button = QPushButton("⏹️ Stop")
        self.large_stop_button.setObjectName("dangerButton")
        self.large_stop_button.clicked.connect(lambda: self.stop_timer(self.get_primary_timer_index()))
        large_timer_controls.addWidget(self.large_stop_button)
        
        active_timer_layout.addLayout(large_timer_controls)
        
        main_layout.addWidget(self.active_timer_frame)

        # Active timers section
        active_timers_label = QLabel("All Timers")
        active_timers_label.setObjectName("subtitleLabel")
        main_layout.addWidget(active_timers_label)

        # All timers list
        self.timers_list = QListWidget()
        main_layout.addWidget(self.timers_list)
        
        # Store the current description and sound
        self.current_description = ""
        self.current_sound = ""
    
    def set_preset_time(self, hours, minutes, seconds):
        """Set preset time values"""
        self.hours_input.setText(str(hours))
        self.minutes_input.setText(str(minutes))
        self.seconds_input.setText(str(seconds))
    
    def open_settings_modal(self):
        """Open settings modal dialog"""
        dialog = SettingsModalDialog(self)
        dialog.exec_()
    
    def open_help_modal(self):
        """Open help modal dialog"""
        dialog = HelpModalDialog(self)
        dialog.exec_()
    
    def open_info_modal(self):
        """Open info modal dialog"""
        dialog = InfoModalDialog(self)
        dialog.exec_()
    
    def toggle_drawer(self):
        """Legacy method - no longer used"""
        pass
    
    def add_description(self):
        dialog = TimerDescriptionDialog(self.current_description, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_description = dialog.get_description()
            status_text = "Description added" if self.current_description else "No description"
            self.description_status.setText(status_text)
    
    def select_sound(self):
        dialog = SoundSelectionDialog(self.current_sound, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_sound = dialog.get_sound_path()
            status_text = os.path.basename(self.current_sound) if self.current_sound else "Default sound"
            self.sound_status.setText(status_text)
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.save_settings()
            
            # Update default sound if changed
            if self.settings.get("default_sound"):
                self.alarm_sound = self.settings["default_sound"]
    
    def edit_timer_description(self, timer_index):
        if timer_index < len(self.timers):
            timer = self.timers[timer_index]
            dialog = TimerDescriptionDialog(timer.get("description", ""), self)
            if dialog.exec_() == QDialog.Accepted:
                timer["description"] = dialog.get_description()
                self.save_timers()
    
    def edit_timer_sound(self, timer_index):
        if timer_index < len(self.timers):
            timer = self.timers[timer_index]
            current_sound = timer.get("sound_path", "")
            dialog = SoundSelectionDialog(current_sound, self)
            if dialog.exec_() == QDialog.Accepted:
                timer["sound_path"] = dialog.get_sound_path()
                self.save_timers()
                
                # If timer is ringing, update the sound
                if timer["is_ringing"] and timer_index in self.media_players:
                    self.media_players[timer_index].stop()
                    self.play_alarm(timer_index)
    
    def add_timer(self, timer_data):
        """Adds a new timer to the application"""
        
        timer = {
            "name": timer_data["name"],
            "total_seconds": timer_data["total_seconds"],
            "remaining_seconds": timer_data["total_seconds"],
            "is_ringing": False,
            "sound_path": timer_data["sound_path"],
            "description": timer_data["description"],
            "is_paused": False
        }
        
        self.timers.append(timer)
        self.save_timers()
        
        # Create a threading event for this timer
        timer_index = len(self.timers) - 1
        self.timer_events[timer_index] = threading.Event()
        
        # Start timer thread
        timer_thread = threading.Thread(
            target=self.run_timer,
            args=(timer_index,),
            daemon=True
        )
        self.timer_threads[timer_index] = timer_thread
        timer_thread.start()

    def open_timer_creation_dialog(self):
        """Open the timer creation dialog"""
        dialog = TimerCreationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            timer_data = dialog.get_timer_data()
            self.add_timer(timer_data)

    def run_timer(self, timer_index):
        timer = self.timers[timer_index]
        event = self.timer_events[timer_index]
        
        while timer["remaining_seconds"] > 0:
            # Check if we should pause
            if timer.get("is_paused", False):
                event.wait()  # Wait until resumed
                event.clear()
                
                # Check if the timer was removed while paused
                if timer_index not in self.timer_events:
                    return
            
            time.sleep(1)
            timer["remaining_seconds"] -= 1
            self.save_timers()
        
        # Timer finished
        timer["is_ringing"] = True
        self.save_timers()
        
        # Send notification if enabled
        if self.settings.get("show_notifications", True):
            notification_text = f"Timer '{timer['name']}' completed!"
            
            # Add description to notification if enabled
            if self.settings.get("include_description", True) and timer.get("description"):
                notification_text += f"\n{timer['description'][:50]}..."
            
            # Set urgency level
            urgency = self.settings.get("notification_urgency", "Normal").lower()
            
            # Send notification with appropriate urgency
            subprocess.run([
                "notify-send",
                "--urgency=" + urgency,
                "TimeRing",
                notification_text
            ])
        
        # Play alarm sound in loop
        self.play_alarm(timer_index)
    
    def pause_resume_timer(self, timer_index):
        if timer_index < len(self.timers):
            timer = self.timers[timer_index]
            
            # Don't pause if already completed
            if timer["is_ringing"]:
                return
            
            # Toggle pause state
            timer["is_paused"] = not timer.get("is_paused", False)
            
            # If resuming, signal the thread to continue
            if not timer["is_paused"] and timer_index in self.timer_events:
                self.timer_events[timer_index].set()
            
            self.save_timers()

    def toggle_timer(self, timer_index):
        """Toggle timer pause/resume state"""
        if timer_index >= 0:
            self.pause_resume_timer(timer_index)
    
    def play_alarm(self, timer_index):
        # Create new media player if one doesn't exist for this timer
        if timer_index not in self.media_players:
            self.media_players[timer_index] = vlc.MediaPlayer()
            
        # Get sound path from timer, fallback to default
        sound_path = self.timers[timer_index].get("sound_path", "")
        if not sound_path or not os.path.exists(sound_path):
            # Use custom default if set, otherwise use built-in
            if self.settings.get("default_sound") and os.path.exists(self.settings["default_sound"]):
                sound_path = self.settings["default_sound"]
            else:
                sound_path = self.alarm_sound
        
        player = self.media_players[timer_index]
        
        # Create media from path
        media = vlc.Media(sound_path)
        
        # Set up looping if enabled
        if self.settings.get("loop_sound", True):
            media.add_option('input-repeat=-1')

        player.set_media(media)
        
        # Start playback
        player.play()
    
    def stop_timer(self, timer_index):
        if timer_index < len(self.timers):
            timer = self.timers[timer_index]
            
            # Stop alarm if ringing
            if timer["is_ringing"] and timer_index in self.media_players:
                self.media_players[timer_index].stop()
                del self.media_players[timer_index]
            
            timer['is_ringing'] = False
            timer['is_paused'] = True
            
            # Clean up thread resources
            if timer_index in self.timer_events:
                # Signal thread to exit if paused
                if timer.get("is_paused", False):
                    self.timer_events[timer_index].set()
                del self.timer_events[timer_index]
            
            if timer_index in self.timer_threads:
                del self.timer_threads[timer_index]
            
            self.save_timers()
    
    def get_system_icon(self, icon_name):
        """Get system icon with fallback to Unicode"""
        try:
            # Try to get system icons first
            style = self.style()
            icon_map = {
                'edit': style.standardIcon(style.SP_FileDialogDetailView),
                'sound': style.standardIcon(style.SP_MediaVolume),
                'play': style.standardIcon(style.SP_MediaPlay),
                'pause': style.standardIcon(style.SP_MediaPause),
                'stop': style.standardIcon(style.SP_MediaStop),
            }
            
            if icon_name in icon_map and not icon_map[icon_name].isNull():
                return icon_map[icon_name]
        except:
            pass
        
        # Fallback to Unicode symbols
        return QIcon()
    
    def update_timers_display(self):
        # Update large timer display first
        self.update_large_timer_display()
        
        self.timers_list.clear()
        
        # Apply theme to list
        is_dark = detect_system_theme()
        apply_theme_to_widget(self.timers_list, is_dark)
        
        for i, timer in enumerate(self.timers):
            item = QListWidgetItem()
            widget = QWidget()
            widget.setProperty("timerCard", True)
            apply_theme_to_widget(widget, is_dark)
            
            layout = QHBoxLayout()
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(16)
            widget.setLayout(layout)
            
            # Timer info container
            info_container = QVBoxLayout()
            info_container.setSpacing(8)
            
            # Timer name
            name_label = QLabel(timer['name'])
            name_label.setObjectName("timerNameLabel")
            info_container.addWidget(name_label)
            
            # Time and status container
            time_status_layout = QHBoxLayout()
            time_status_layout.setSpacing(12)
            
            # Time display
            total_seconds = timer["remaining_seconds"]
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_text = f"{minutes:02d}:{seconds:02d}"
                
            time_label = QLabel(time_text)
            time_label.setObjectName("timerTimeLabel")
            time_status_layout.addWidget(time_label)
            
            # Status indicator
            if timer["is_ringing"]:
                status_text = "RINGING"
                status_style = "color: #ef4444; font-weight: 600; font-size: 11pt;"
            elif timer.get("is_paused", False):
                status_text = "PAUSED"
                status_style = "color: #f59e0b; font-weight: 600; font-size: 11pt;"
            else:
                status_text = "RUNNING"
                status_style = "color: #10b981; font-weight: 600; font-size: 11pt;"
                
            status_label = QLabel(status_text)
            status_label.setStyleSheet(status_style)
            time_status_layout.addWidget(status_label)
            time_status_layout.addStretch()
            
            info_container.addLayout(time_status_layout)
            
            # Description preview
            if timer.get("description"):
                desc_preview = timer["description"][:60] + "..." if len(timer["description"]) > 60 else timer["description"]
                desc_label = QLabel(f"{desc_preview}")
                desc_label.setObjectName("statusLabel")
                desc_label.setWordWrap(True)
                info_container.addWidget(desc_label)
            
            layout.addLayout(info_container)
            layout.addStretch()
            
            # Action buttons container
            buttons_container = QVBoxLayout()
            buttons_container.setSpacing(8)
            
            # Top row buttons
            top_buttons = QHBoxLayout()
            top_buttons.setSpacing(6)
            
            # Edit description button
            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit Description")
            edit_btn.setFixedSize(40, 40)
            edit_btn.setObjectName("secondaryButton")
            edit_btn.clicked.connect(lambda _, idx=i: self.edit_timer_description(idx))
            top_buttons.addWidget(edit_btn)
            
            # Sound button
            sound_btn = QPushButton("Sound")
            sound_btn.setToolTip("Change Sound")
            sound_btn.setFixedSize(40, 40)
            sound_btn.setObjectName("secondaryButton")
            sound_btn.clicked.connect(lambda _, idx=i: self.edit_timer_sound(idx))
            top_buttons.addWidget(sound_btn)
            
            buttons_container.addLayout(top_buttons)
            
            # Bottom row buttons
            bottom_buttons = QHBoxLayout()
            bottom_buttons.setSpacing(6)
            
            # Pause/Resume button (only for active timers)
            if not timer["is_ringing"]:
                if timer.get("is_paused", False):
                    control_btn = QPushButton("Resume")
                    control_btn.setToolTip("Resume Timer")
                    control_btn.setObjectName("successButton")
                else:
                    control_btn = QPushButton("Pause")
                    control_btn.setToolTip("Pause Timer")
                    control_btn.setObjectName("warningButton")
                
                control_btn.setFixedSize(40, 40)
                control_btn.clicked.connect(lambda _, idx=i: self.pause_resume_timer(idx))
                bottom_buttons.addWidget(control_btn)
            
            # Stop button
            stop_btn = QPushButton("Stop")
            stop_btn.setToolTip("Stop Timer")
            stop_btn.setFixedSize(40, 40)
            stop_btn.setObjectName("dangerButton")
            stop_btn.clicked.connect(lambda _, idx=i: self.stop_timer(idx))
            bottom_buttons.addWidget(stop_btn)
            
            buttons_container.addLayout(bottom_buttons)
            layout.addLayout(buttons_container)
            
            # Set size hint based on content
            widget.adjustSize()
            item.setSizeHint(widget.sizeHint())
            self.timers_list.addItem(item)
            self.timers_list.setItemWidget(item, widget)
    
    def save_timers(self):
        if self.settings.get("save_state", True):
            with open(self.state_file, "w") as f:
                json.dump(self.timers, f)
    
    def load_timers(self):
        if os.path.exists(self.state_file) and self.settings.get("auto_start_timers", True):
            with open(self.state_file, "r") as f:
                self.timers = json.load(f)
                
            # Restart any running timers
            for i, timer in enumerate(self.timers):
                # Create threading event for each timer
                self.timer_events[i] = threading.Event()
                
                # Resume paused timers in paused state
                if timer.get("is_paused", False):
                    pass  # Keep it paused
                elif timer["remaining_seconds"] > 0 and not timer["is_ringing"]:
                    # Start running timers
                    timer_thread = threading.Thread(
                        target=self.run_timer,
                        args=(i,),
                        daemon=True
                    )
                    self.timer_threads[i] = timer_thread
                    timer_thread.start()
                elif timer["is_ringing"]:
                    # Restart ringing timers
                    self.play_alarm(i)
    
    def load_settings(self):
        default_settings = {
            "auto_start_timers": True,
            "save_state": True,
            "show_notifications": True,
            "include_description": True,
            "notification_urgency": "Normal",
            "default_sound": "",
            "loop_sound": True
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except:
                return default_settings
        else:
            return default_settings
    
    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f)
    
    def closeEvent(self, event):
        # Clean up VLC players
        for player in self.media_players.values():
            player.stop()
        
        # Resume any paused threads so they can exit
        for i, timer_event in self.timer_events.items():
            timer_event.set()
        
        # Save timers
        self.save_timers()
        
        # Save settings
        self.save_settings()
        
        event.accept()

    def get_primary_timer_index(self):
        """Get the index of the primary active timer (first running timer)"""
        for i, timer in enumerate(self.timers):
            if not timer["is_ringing"] and timer["remaining_seconds"] > 0:
                return i
        return -1

    def update_large_timer_display(self):
        """Update the large timer display with the primary active timer"""
        primary_index = self.get_primary_timer_index()
        
        if primary_index >= 0:
            timer = self.timers[primary_index]
            self.active_timer_frame.setVisible(True)
            
            # Update display
            self.large_timer_name.setText(timer["name"])
            
            # Format time display
            remaining = timer["remaining_seconds"]
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            
            if hours > 0:
                time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_text = f"{minutes:02d}:{seconds:02d}"
            
            self.large_timer_time.setText(time_text)
            
            # Update status and controls
            if timer["is_ringing"]:
                self.large_timer_status.setText("ALARM!")
                self.large_pause_button.setText("Stop Alarm")
            elif timer.get("is_paused", False):
                self.large_timer_status.setText("Paused")
                self.large_pause_button.setText("Resume")
            else:
                self.large_timer_status.setText("Running")
                self.large_pause_button.setText("Pause")
        else:
            self.active_timer_frame.setVisible(False)
        

class TimerCreationDialog(QDialog):
    """Modal dialog for creating new timers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Timer")
        self.setModal(True)
        self.resize(450, 600)
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.current_description = ""
        self.current_sound = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Create New Timer")
        header.setObjectName("titleLabel")
        layout.addWidget(header)
        
        # Timer name input
        name_label = QLabel("Timer Name:")
        layout.addWidget(name_label)
        
        self.timer_name_input = QLineEdit()
        self.timer_name_input.setPlaceholderText("Enter timer name")
        layout.addWidget(self.timer_name_input)
        
        # Duration inputs
        duration_label = QLabel("Duration:")
        layout.addWidget(duration_label)
        
        duration_container = QWidget()
        duration_layout = QGridLayout(duration_container)
        duration_layout.setSpacing(12)
        
        # Hours
        hours_label = QLabel("Hours:")
        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText("0")
        self.hours_input.setText("0")
        self.hours_input.setMaximumWidth(80)
        duration_layout.addWidget(hours_label, 0, 0)
        duration_layout.addWidget(self.hours_input, 0, 1)
        
        # Minutes
        minutes_label = QLabel("Minutes:")
        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText("0")
        self.minutes_input.setText("0")
        self.minutes_input.setMaximumWidth(80)
        duration_layout.addWidget(minutes_label, 0, 2)
        duration_layout.addWidget(self.minutes_input, 0, 3)
        
        # Seconds
        seconds_label = QLabel("Seconds:")
        self.seconds_input = QLineEdit()
        self.seconds_input.setPlaceholderText("0")
        self.seconds_input.setText("0")
        self.seconds_input.setMaximumWidth(80)
        duration_layout.addWidget(seconds_label, 1, 0)
        duration_layout.addWidget(self.seconds_input, 1, 1)
        
        duration_layout.setColumnStretch(4, 1)
        layout.addWidget(duration_container)
        
        # Quick preset buttons
        presets_label = QLabel("Quick Presets:")
        presets_label.setObjectName("subtitleLabel")
        layout.addWidget(presets_label)
        
        presets_layout = QGridLayout()
        presets_layout.setSpacing(8)
        
        # Common timer presets
        presets = [
            ("5 min", 0, 5, 0), ("10 min", 0, 10, 0), ("15 min", 0, 15, 0),
            ("30 min", 0, 30, 0), ("1 hour", 1, 0, 0), ("2 hours", 2, 0, 0)
        ]
        
        for i, (label, hours, minutes, seconds) in enumerate(presets):
            preset_btn = QPushButton(label)
            preset_btn.setObjectName("secondaryButton")
            preset_btn.clicked.connect(lambda checked, h=hours, m=minutes, s=seconds: self.set_preset_time(h, m, s))
            row, col = divmod(i, 3)
            presets_layout.addWidget(preset_btn, row, col)
        
        layout.addLayout(presets_layout)
        
        # Options section
        options_label = QLabel("Timer Options:")
        options_label.setObjectName("subtitleLabel")
        layout.addWidget(options_label)
        
        # Description button
        description_layout = QHBoxLayout()
        self.description_button = QPushButton("Add Description")
        self.description_button.clicked.connect(self.add_description)
        description_layout.addWidget(self.description_button)
        
        self.description_status = QLabel("No description")
        self.description_status.setObjectName("statusLabel")
        description_layout.addWidget(self.description_status)
        layout.addLayout(description_layout)
        
        # Sound selection
        sound_layout = QHBoxLayout()
        self.sound_button = QPushButton("Select Sound")
        self.sound_button.clicked.connect(self.select_sound)
        sound_layout.addWidget(self.sound_button)
        
        self.sound_status = QLabel("Default sound")
        self.sound_status.setObjectName("statusLabel")
        sound_layout.addWidget(self.sound_status)
        layout.addLayout(sound_layout)
        
        layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Create Timer")
        button_box.button(QDialogButtonBox.Ok).setObjectName("successButton")
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def set_preset_time(self, hours, minutes, seconds):
        """Set preset time values"""
        self.hours_input.setText(str(hours))
        self.minutes_input.setText(str(minutes))
        self.seconds_input.setText(str(seconds))
    
    def add_description(self):
        dialog = TimerDescriptionDialog(self.current_description, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_description = dialog.get_description()
            status_text = "Description added" if self.current_description else "No description"
            self.description_status.setText(status_text)
    
    def select_sound(self):
        dialog = SoundSelectionDialog(self.current_sound, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_sound = dialog.get_sound_path()
            status_text = os.path.basename(self.current_sound) if self.current_sound else "Default sound"
            self.sound_status.setText(status_text)
    
    def validate_and_accept(self):
        """Validate input and accept dialog"""
        name = self.timer_name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a timer name.")
            return
        
        try:
            hours = int(self.hours_input.text() or "0")
            minutes = int(self.minutes_input.text() or "0")
            seconds = int(self.seconds_input.text() or "0")
            
            # Validate inputs
            if hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError("Negative values not allowed")
            if minutes >= 60 or seconds >= 60:
                raise ValueError("Minutes and seconds must be less than 60")
            
            # Calculate total duration in seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            if total_seconds <= 0:
                QMessageBox.warning(self, "Invalid Duration", "Please enter a duration greater than 0.")
                return
                
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for hours, minutes, and seconds.")
            return
        
        self.accept()
    
    def get_timer_data(self):
        """Get the timer data from the dialog"""
        hours = int(self.hours_input.text() or "0")
        minutes = int(self.minutes_input.text() or "0")
        seconds = int(self.seconds_input.text() or "0")
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        return {
            "name": self.timer_name_input.text().strip(),
            "total_seconds": total_seconds,
            "remaining_seconds": total_seconds,
            "is_ringing": False,
            "sound_path": self.current_sound,
            "description": self.current_description,
            "is_paused": False
        }


def load_and_apply_styles():
    """Load and apply CSS styles"""
    try:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        style_file = os.path.join(app_dir, "style.qss")
        
        if os.path.exists(style_file):
            with open(style_file, "r") as f:
                return f.read()
    except Exception as e:
        print(f"Warning: Could not load styles: {e}")
    
    return ""


def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_DEVELOPER)
    
    # Load and apply styles
    styles = load_and_apply_styles()
    if styles:
        app.setStyleSheet(styles)
    
    # Create and show main window
    window = TimerApp(args)
    window.show()
    
    # Apply theme to main window
    is_dark = detect_system_theme()
    apply_theme_to_widget(window, is_dark)
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
