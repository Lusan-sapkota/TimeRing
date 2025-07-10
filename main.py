import sys
import json
import os
import subprocess
import threading
import time
import argparse
import webbrowser
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QHBoxLayout, QLabel, QTextEdit, QDialog, QDialogButtonBox,
                             QFileDialog, QGroupBox, QCheckBox, QTabWidget, QComboBox,
                             QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGridLayout,
                             QMessageBox, QDesktopWidget)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
import vlc
import requests
from version import get_version

# Application metadata
APP_NAME = "TimeRing"
APP_VERSION = get_version()
APP_DEVELOPER = "Lusan Sapkota"


def detect_system_theme():
    """Detect if the system is using dark theme"""
    try:
        # Try to detect theme using Qt's palette
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.Window)
            text_color = palette.color(QPalette.WindowText)
            
            # If background is darker than text, it's likely a dark theme
            bg_lightness = bg_color.lightness()
            text_lightness = text_color.lightness()
            
            if bg_lightness < text_lightness:
                return True
        
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
    
    # Apply to all child widgets recursively
    for child in widget.findChildren(QWidget):
        child.setProperty("darkTheme", is_dark)
    
    # Refresh styles
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    
    # Force refresh for all children
    for child in widget.findChildren(QWidget):
        child.style().unpolish(child)
        child.style().polish(child)
    
    # Force repaint
    widget.update()


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
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Settings")
        header.setObjectName("titleLabel")
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
        
        self.notifications_check = create_glass_checkbox("Enable desktop notifications", parent=quick_frame)
        if self.parent_window:
            self.notifications_check.setChecked(self.parent_window.settings.get("show_notifications", True))
        quick_layout.addWidget(self.notifications_check)
        
        self.auto_start_check = create_glass_checkbox("Auto-start timers on launch", parent=quick_frame)
        if self.parent_window:
            self.auto_start_check.setChecked(self.parent_window.settings.get("auto_start_timers", True))
        quick_layout.addWidget(self.auto_start_check)
        
        layout.addWidget(quick_frame)
        
        # Advanced settings button
        advanced_btn = QPushButton("Advanced Settings")
        advanced_btn.setIcon(self.get_icon("settings"))
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
        """Get icon by name from bundled icons with theme support"""
        icon_path = os.path.join(self.parent_window.app_dir, "images", "icons", f"{name}.svg")
        
        # Determine icon color based on theme
        is_dark = detect_system_theme()
        icon_color = "#ffffff" if is_dark else "#374151"  # White for dark theme, dark gray for light
        
        return load_svg_icon(icon_path, icon_color, 24)
    
    def browse_sound(self):
        """Browse for sound file"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg *.m4a)")
        file_dialog.setWindowTitle("Select Default Sound")
        
        # Apply theme to file dialog
        is_dark = detect_system_theme()
        apply_theme_to_widget(file_dialog, is_dark)
        
        # Force theme application to all child widgets after showing
        file_dialog.show()
        
        # Apply theme recursively to all child widgets
        for child in file_dialog.findChildren(QWidget):
            apply_theme_to_widget(child, is_dark)
        
        # Force style refresh
        file_dialog.style().unpolish(file_dialog)
        file_dialog.style().polish(file_dialog)
        
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
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QLabel("Help & User Guide")
        header.setObjectName("titleLabel")
        layout.addWidget(header)
        
        # Scrollable help content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        help_content = QLabel("""
<h2>Getting Started</h2>
<p><strong>Creating a New Timer:</strong></p>
<ol>
<li>Click the "Add Timer" button at the top of the application</li>
<li>Enter a descriptive name for your timer</li>
<li>Set the duration using hours, minutes, and seconds fields</li>
<li>Optionally add a description to provide context</li>
<li>Choose a custom notification sound if desired</li>
<li>Click "Start Timer" to begin the countdown</li>
</ol>

<h2>Timer Management</h2>
<p>Each active timer displays the following information:</p>
<ul>
<li><strong>Timer Name:</strong> The descriptive title you assigned</li>
<li><strong>Remaining Time:</strong> Current countdown in HH:MM:SS format</li>
<li><strong>Status:</strong> Running, Paused, Completed, or Ringing</li>
<li><strong>Description:</strong> Optional context text (if provided)</li>
</ul>

<p><strong>Timer Control Actions:</strong></p>
<ul>
<li><strong>Edit Description:</strong> Modify the timer's descriptive text</li>
<li><strong>Change Sound:</strong> Select a different notification sound</li>
<li><strong>Pause/Resume:</strong> Temporarily stop or continue the countdown</li>
<li><strong>Rerun:</strong> Restart the timer from its original duration</li>
<li><strong>Stop:</strong> Immediately halt the timer and stop any alarms</li>
<li><strong>Delete:</strong> Permanently remove the timer from the list</li>
</ul>

<h2>Notification System</h2>
<p>When a timer reaches zero, TimeRing provides multiple alerts:</p>
<ul>
<li>Desktop notification with timer name and description</li>
<li>Continuous audio alert until manually stopped</li>
<li>Visual status change to "Ringing" in the timer card</li>
<li>Large timer display shows completed timer prominently</li>
</ul>

<h2>Configuration Options</h2>
<p><strong>Audio Settings:</strong></p>
<ul>
<li>Set a global default notification sound for all new timers</li>
<li>Configure individual timer sounds for specific purposes</li>
<li>Preview audio files before applying them</li>
<li>Support for MP3, WAV, OGG, and M4A audio formats</li>
<li>Option to loop sounds continuously until manually stopped</li>
</ul>

<p><strong>Application Behavior:</strong></p>
<ul>
<li>Auto-start saved timers when launching the application</li>
<li>Preserve timer states between application sessions</li>
<li>Configure desktop notification urgency levels</li>
<li>Enable or disable timer descriptions in notifications</li>
<li>Automatic system theme detection for light and dark modes</li>
</ul>

<h2>Command Line Interface</h2>
<p>TimeRing supports several command line options for automation:</p>
<ul>
<li><code>TimeRing --help</code> - Display usage information and available options</li>
<li><code>TimeRing --version</code> - Show current version and developer information</li>
<li><code>TimeRing --set-sound /path/to/file.mp3</code> - Set default notification sound</li>
</ul>

<h2>Visual Themes</h2>
<p>TimeRing automatically adapts to your system appearance preferences:</p>
<ul>
<li><strong>Light Theme:</strong> Clean interface with bright backgrounds and dark text</li>
<li><strong>Dark Theme:</strong> Reduced eye strain with dark backgrounds and light text</li>
<li>Seamless integration with GNOME and KDE desktop environments</li>
<li>Responsive layout that adapts to different window sizes</li>
<li>Consistent styling across all dialogs and interface elements</li>
</ul>

<h2>Usage Tips</h2>
<ul>
<li><strong>Multiple Timers:</strong> Run unlimited concurrent timers for different tasks</li>
<li><strong>Descriptive Names:</strong> Use clear, specific names to identify timer purposes</li>
<li><strong>Custom Sounds:</strong> Assign unique sounds to distinguish between timer types</li>
<li><strong>Keyboard Navigation:</strong> Use Tab key to move between input fields efficiently</li>
<li><strong>Quick Actions:</strong> Right-click timer cards for context-sensitive options</li>
<li><strong>Large Display:</strong> The prominent timer view shows your most active countdown</li>
</ul>

<h2>Troubleshooting</h2>
<p><strong>Audio Issues:</strong></p>
<ul>
<li>Ensure VLC media player is installed: <code>sudo apt install vlc</code></li>
<li>Verify audio file format compatibility and file permissions</li>
<li>Test notification sounds using the preview button in settings</li>
<li>Check system volume levels and audio device configuration</li>
</ul>

<p><strong>Notification Problems:</strong></p>
<ul>
<li>Install notification daemon: <code>sudo apt install libnotify-bin</code></li>
<li>Verify desktop environment notification settings are enabled</li>
<li>Check notification urgency level configuration in advanced settings</li>
<li>Ensure TimeRing has permission to send desktop notifications</li>
</ul>

<p><strong>Interface Issues:</strong></p>
<ul>
<li>Reset application settings if interface appears corrupted</li>
<li>Verify system theme settings for proper visual integration</li>
<li>Check minimum window size requirements for optimal display</li>
<li>Clear saved timer state if application fails to start properly</li>
</ul>
        """)
        help_content.setWordWrap(True)
        help_content.setTextFormat(Qt.RichText)
        help_content.setObjectName("helpContent")
        
        # Apply proper theme styling to help content
        is_dark = detect_system_theme()
        apply_theme_to_widget(help_content, is_dark)
        
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
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        self.setup_ui()
        
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
<h1>{APP_NAME}</h1>
<p><strong>Version:</strong> {APP_VERSION}</p>
<p><strong>Developer:</strong> {APP_DEVELOPER}</p>
<p>
A modern, lightweight timer application designed for Linux desktop environments.
Features multiple concurrent timers, custom notifications, and seamless 
integration with KDE and GNOME.
</p>
</div>
        """)
        app_info.setWordWrap(True)
        app_info.setTextFormat(Qt.RichText)
        app_info.setAlignment(Qt.AlignCenter)
        app_info.setObjectName("appInfo")
        layout.addWidget(app_info)
        
        # System info
        system_info = QLabel(f"""
<div style="text-align: center;">
<p>
<strong>System Theme:</strong> {'Dark' if detect_system_theme() else 'Light'}<br>
<strong>Desktop:</strong> {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}<br>
<strong>Python:</strong> {sys.version.split()[0]}
</p>
</div>
        """)
        system_info.setTextFormat(Qt.RichText)
        system_info.setAlignment(Qt.AlignCenter)
        system_info.setObjectName("systemInfo")
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
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        layout = QVBoxLayout(self)
        
        # Description text edit
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter timer description (max 50 words)")
        self.description_edit.setText(description)
        layout.addWidget(self.description_edit)
        
        # Word count label
        self.word_count_label = QLabel("0/50 words")
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
        self.word_count_label.setText(f"{word_count}/50 words")
        
        # Disable OK button if over word limit
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            ok_button = button_box.button(QDialogButtonBox.Ok)
            if ok_button:
                ok_button.setEnabled(word_count <= 50)
    
    def get_description(self):
        return self.description_edit.toPlainText().strip()


class SoundSelectionDialog(QDialog):
    def __init__(self, current_sound="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Notification Sound")
        self.setMinimumWidth(400)
        
        self.current_sound = current_sound
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
        layout = QVBoxLayout(self)
        
        # Sound path display
        self.sound_path_label = QLabel(current_sound or "Default sound")
        self.sound_path_label.setWordWrap(True)
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
        
        # Apply theme to file dialog
        is_dark = detect_system_theme()
        apply_theme_to_widget(file_dialog, is_dark)
        
        # Force theme application to all child widgets after showing
        file_dialog.show()
        
        # Apply theme recursively to all child widgets
        for child in file_dialog.findChildren(QWidget):
            apply_theme_to_widget(child, is_dark)
        
        # Force style refresh
        file_dialog.style().unpolish(file_dialog)
        file_dialog.style().polish(file_dialog)
        
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
        
        self.settings = settings.copy()  # Make a copy to work with
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
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
        
        # Get theme info
        is_dark = detect_system_theme()
        
        # General settings group
        general_group = QGroupBox("General Settings")
        apply_theme_to_widget(general_group, is_dark)
        general_layout = QVBoxLayout(general_group)
        
        # Auto-start timers on app launch
        self.auto_start_check = create_glass_checkbox("Auto-start timers on application launch")
        self.auto_start_check.setChecked(self.settings.get("auto_start_timers", True))
        general_layout.addWidget(self.auto_start_check)
        
        # Save timer state on exit
        self.save_state_check = create_glass_checkbox("Save timer state on exit")
        self.save_state_check.setChecked(self.settings.get("save_state", True))
        general_layout.addWidget(self.save_state_check)
        
        layout.addWidget(general_group)
        
        # Update settings group
        update_group = QGroupBox("Update Settings")
        apply_theme_to_widget(update_group, is_dark)
        update_layout = QVBoxLayout(update_group)
        
        # Auto-check for updates
        self.auto_update_check = create_glass_checkbox("Check for updates automatically")
        self.auto_update_check.setChecked(self.settings.get("auto_check_updates", True))
        update_layout.addWidget(self.auto_update_check)
        
        # Manual update check button
        update_button_layout = QHBoxLayout()
        self.check_updates_btn = QPushButton("Check for Updates Now")
        self.check_updates_btn.clicked.connect(self.check_for_updates)
        apply_theme_to_widget(self.check_updates_btn, is_dark)
        update_button_layout.addWidget(self.check_updates_btn)
        update_button_layout.addStretch()
        update_layout.addLayout(update_button_layout)
        
        layout.addWidget(update_group)
        
        # Add spacer
        layout.addStretch()
    
    def setup_notifications_tab(self):
        layout = QVBoxLayout(self.notifications_tab)
        
        # Get theme info
        is_dark = detect_system_theme()
        
        # Notification settings group
        notifications_group = QGroupBox("Notification Settings")
        apply_theme_to_widget(notifications_group, is_dark)
        notifications_layout = QVBoxLayout(notifications_group)
        
        # Show desktop notifications
        self.show_notifications_check = create_glass_checkbox("Show desktop notifications")
        self.show_notifications_check.setChecked(self.settings.get("show_notifications", True))
        notifications_layout.addWidget(self.show_notifications_check)
        
        # Include description in notifications
        self.include_desc_check = create_glass_checkbox("Include timer description in notifications")
        self.include_desc_check.setChecked(self.settings.get("include_description", True))
        notifications_layout.addWidget(self.include_desc_check)
        
        # Notification urgency - inline with proper spacing
        urgency_layout = QHBoxLayout()
        urgency_layout.setContentsMargins(0, 16, 0, 8)
        urgency_layout.setSpacing(12)
        
        urgency_label = QLabel("Notification urgency:")
        urgency_label.setObjectName("settingsLabel")
        urgency_label.setStyleSheet("font-size: 14px; font-weight: 500; margin: 0; padding: 0;")
        apply_theme_to_widget(urgency_label, is_dark)
        urgency_layout.addWidget(urgency_label)
        
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(["Low", "Normal", "Critical"])
        current_urgency = self.settings.get("notification_urgency", "Normal")
        self.urgency_combo.setCurrentText(current_urgency)
        self.urgency_combo.setFixedWidth(120)
        apply_theme_to_widget(self.urgency_combo, is_dark)
        urgency_layout.addWidget(self.urgency_combo)
        
        urgency_layout.addStretch()
        notifications_layout.addLayout(urgency_layout)
        
        layout.addWidget(notifications_group)
        
        # Add spacer
        layout.addStretch()
    
    def setup_sounds_tab(self):
        layout = QVBoxLayout(self.sounds_tab)
        
        # Get theme info
        is_dark = detect_system_theme()
        
        # Default sound selection
        sound_group = QGroupBox("Default Sound")
        apply_theme_to_widget(sound_group, is_dark)
        sound_layout = QVBoxLayout(sound_group)
        
        # Current default sound
        self.default_sound_path = self.settings.get("default_sound", "")
        display_path = self.default_sound_path or "Built-in default sound"
        self.sound_path_label = QLabel(display_path)
        self.sound_path_label.setWordWrap(True)
        apply_theme_to_widget(self.sound_path_label, is_dark)
        sound_layout.addWidget(self.sound_path_label)
        
        # Sound selection buttons
        buttons_layout = QHBoxLayout()
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_sound)
        apply_theme_to_widget(self.browse_button, is_dark)
        buttons_layout.addWidget(self.browse_button)
        
        # Preview button
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_sound)
        apply_theme_to_widget(self.preview_button, is_dark)
        buttons_layout.addWidget(self.preview_button)
        
        # Reset to default button
        self.reset_button = QPushButton("Use Built-in")
        self.reset_button.clicked.connect(self.use_default_sound)
        apply_theme_to_widget(self.reset_button, is_dark)
        buttons_layout.addWidget(self.reset_button)
        
        sound_layout.addLayout(buttons_layout)
        layout.addWidget(sound_group)
        
        # Sound options
        options_group = QGroupBox("Sound Options")
        apply_theme_to_widget(options_group, is_dark)
        options_layout = QVBoxLayout(options_group)
        
        # Loop sound
        self.loop_sound_check = create_glass_checkbox("Loop sound until stopped")
        self.loop_sound_check.setChecked(self.settings.get("loop_sound", True))
        options_layout.addWidget(self.loop_sound_check)
        
        layout.addWidget(options_group)
        
        # Add spacer
        layout.addStretch()
    
    def browse_sound(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg)")
        file_dialog.setWindowTitle("Select Default Sound")
        
        # Apply theme to file dialog
        is_dark = detect_system_theme()
        apply_theme_to_widget(file_dialog, is_dark)
        
        # Force theme application to all child widgets after showing
        file_dialog.show()
        
        # Apply theme recursively to all child widgets
        for child in file_dialog.findChildren(QWidget):
            apply_theme_to_widget(child, is_dark)
        
        # Force style refresh
        file_dialog.style().unpolish(file_dialog)
        file_dialog.style().polish(file_dialog)
        
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
        self.settings["auto_check_updates"] = self.auto_update_check.isChecked()
        
        return self.settings
    
    def check_for_updates(self):
        """Check for updates from GitHub repository"""

        try:
            # Check GitHub releases API for latest version
            response = requests.get("https://api.github.com/repos/Lusan-sapkota/TimeRing/releases/latest", timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                current_version = get_version()
                
                if latest_version != current_version:
                    # Show update dialog
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Update Available")
                    msg_box.setText(f"A new version ({latest_version}) is available!\n\nCurrent version: {current_version}")
                    msg_box.setDetailedText(release_data.get("body", "No release notes available."))
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    
                    download_btn = QPushButton("Download Update")
                    msg_box.addButton(download_btn, QMessageBox.AcceptRole)
                    
                    # Apply theme
                    is_dark = detect_system_theme()
                    apply_theme_to_widget(msg_box, is_dark)
                    
                    result = msg_box.exec_()
                    if msg_box.clickedButton() == download_btn:
                        import webbrowser
                        webbrowser.open(release_data["html_url"])
                else:
                    # No update available
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("No Updates")
                    msg_box.setText("You are running the latest version of TimeRing!")
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    
                    is_dark = detect_system_theme()
                    apply_theme_to_widget(msg_box, is_dark)
                    msg_box.exec_()
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            # Error checking for updates
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Update Check Failed")
            msg_box.setText("Failed to check for updates.")
            msg_box.setDetailedText(f"Error: {str(e)}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            is_dark = detect_system_theme()
            apply_theme_to_widget(msg_box, is_dark)
            msg_box.exec_()
    
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
        self.last_timer_count = 0  # Track timer count to prevent unnecessary rebuilds
        self.current_primary_timer_index = 0  # Track which timer is currently displayed
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

    def get_icon(self, name):
        """Get icon by name from bundled icons with theme support"""
        icon_path = os.path.join(self.app_dir, "images", "icons", f"{name}.svg")
        
        # Determine icon color based on theme
        is_dark = detect_system_theme()
        icon_color = "#ffffff" if is_dark else "#374151"  # White for dark theme, dark gray for light
        
        return load_svg_icon(icon_path, icon_color, 24)
    
    def format_time(self, total_seconds):
        """Formats seconds into HH:MM:SS or MM:SS"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
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
        # Main widget container with scroll area for compact displays
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll_area)
        
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins for compact mode
        main_layout.setSpacing(12)  # Reduced spacing for compact mode
        
        # Apply theme
        is_dark = detect_system_theme()
        apply_theme_to_widget(main_widget, is_dark)
        
        # Header with menu buttons and title
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # App Logo
        logo_label = QLabel()
        logo_path = os.path.join(self.app_dir, "images", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        header_layout.addWidget(logo_label)
        
        # App Title
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("headerTitleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Menu buttons
        menu_layout = QHBoxLayout()
        menu_layout.setSpacing(8)
        
        def create_header_button(icon_name, tooltip):
            btn = QPushButton()
            btn.setIcon(self.get_icon(icon_name))
            btn.setToolTip(tooltip)
            btn.setObjectName("menuButton")
            btn.setFixedSize(40, 40)
            return btn

        # Settings button
        settings_btn = create_header_button("settings", "Settings")
        settings_btn.clicked.connect(self.open_settings_modal)
        menu_layout.addWidget(settings_btn)
        
        # Help button
        help_btn = create_header_button("help", "Help & Guide")
        help_btn.clicked.connect(self.open_help_modal)
        menu_layout.addWidget(help_btn)
        
        # Info button
        info_btn = create_header_button("info", "About TimeRing")
        info_btn.clicked.connect(self.open_info_modal)
        menu_layout.addWidget(info_btn)
        
        header_layout.addLayout(menu_layout)
        main_layout.addWidget(header_widget)
        
        # Prominent Add Timer button - full width
        self.add_timer_button = QPushButton("Add Timer")
        self.add_timer_button.setIcon(self.get_icon('add'))
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
        
        self.large_timer_description = QLabel("Timer Description")
        self.large_timer_description.setObjectName("timerDescriptionLabel")
        self.large_timer_description.setAlignment(Qt.AlignCenter)
        self.large_timer_description.setWordWrap(True)
        active_timer_layout.addWidget(self.large_timer_description)
        
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
        
        # Previous timer button
        self.large_prev_button = QPushButton("Previous")
        self.large_prev_button.setIcon(self.get_icon("play"))  # We'll rotate this icon
        self.large_prev_button.setObjectName("secondaryButton")
        self.large_prev_button.setToolTip("Switch to Previous Timer")
        self.large_prev_button.clicked.connect(self.switch_to_previous_timer)
        large_timer_controls.addWidget(self.large_prev_button)
        
        self.large_pause_button = QPushButton("Pause")
        self.large_pause_button.setIcon(self.get_icon("pause"))
        self.large_pause_button.setObjectName("warningButton")
        self.large_pause_button.clicked.connect(lambda: self.toggle_timer(self.current_primary_timer_index))
        large_timer_controls.addWidget(self.large_pause_button)
        
        self.large_stop_button = QPushButton("Stop")
        self.large_stop_button.setIcon(self.get_icon("stop"))
        self.large_stop_button.setObjectName("dangerButton")
        self.large_stop_button.clicked.connect(lambda: self.stop_timer(self.current_primary_timer_index))
        large_timer_controls.addWidget(self.large_stop_button)
        
        # Next timer button
        self.large_next_button = QPushButton("Next")
        self.large_next_button.setIcon(self.get_icon("play"))
        self.large_next_button.setObjectName("secondaryButton")
        self.large_next_button.setToolTip("Switch to Next Timer")
        self.large_next_button.clicked.connect(self.switch_to_next_timer)
        large_timer_controls.addWidget(self.large_next_button)
        
        active_timer_layout.addLayout(large_timer_controls)
        
        main_layout.addWidget(self.active_timer_frame)

        # Placeholder for empty active timer area (separate from the frame)
        self.active_timer_placeholder = QLabel("⏱️ No Active Timer\n\nCreate a new timer to see it here\nYour timer will appear with a large, easy-to-read display")
        self.active_timer_placeholder.setObjectName("activeTimerPlaceholder")
        self.active_timer_placeholder.setAlignment(Qt.AlignCenter)
        self.active_timer_placeholder.setVisible(True)  # Initially visible when no timers
        main_layout.addWidget(self.active_timer_placeholder)
        
        # Active timers section
        active_timers_label = QLabel("All Timers")
        active_timers_label.setObjectName("subtitleLabel")
        main_layout.addWidget(active_timers_label)

        # All timers list
        self.timers_list = QListWidget()
        self.timers_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.timers_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timers_list.setResizeMode(QListWidget.Adjust)
        
        # Fix scrolling issues with custom widgets
        self.timers_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.timers_list.setMovement(QListWidget.Static)
        self.timers_list.setFlow(QListWidget.TopToBottom)
        self.timers_list.setWrapping(False)
        self.timers_list.setSelectionMode(QListWidget.NoSelection)
        self.timers_list.setFocusPolicy(Qt.NoFocus)
        
        main_layout.addWidget(self.timers_list)
        
        # Apply initial screen size
        self.setProperty("screenSize", "medium")  # Default
        
        # Store the current description and sound
        self.current_description = ""
        self.current_sound = ""

    def create_timer_card(self, timer, timer_index):
        """Creates a widget for a single timer card."""
        card_widget = QWidget()
        card_layout = QGridLayout(card_widget)
        card_widget.setObjectName("timerCard")
        
        # Set proper size policy for consistent sizing
        card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Adjust minimum height based on compact mode
        is_compact = self.property("compactMode")
        if is_compact:
            card_widget.setMinimumHeight(100)
        else:
            card_widget.setMinimumHeight(120)
        
        # Set status property for CSS styling
        if timer["is_ringing"]:
            card_widget.setProperty("status", "ringing")
        elif timer.get("has_finished", False):
            card_widget.setProperty("status", "finished")
        elif timer.get("is_paused", False):
            card_widget.setProperty("status", "paused")
        else:
            card_widget.setProperty("status", "running")

        # Timer name
        name_label = QLabel(timer["name"])
        name_label.setObjectName("timerName")
        card_layout.addWidget(name_label, 0, 0, 1, 4)

        # Timer description
        if timer.get("description"):
            description_label = QLabel(timer["description"])
            description_label.setObjectName("timerDescription")
            description_label.setWordWrap(True)
            card_layout.addWidget(description_label, 1, 0, 1, 4)

        # Time display
        time_label = QLabel(self.format_time(timer["remaining_seconds"]))
        time_label.setObjectName("timerTime")
        card_layout.addWidget(time_label, 2, 0, 1, 2)

        # Status display
        status_label = QLabel()
        status_label.setObjectName("timerStatus")
        card_layout.addWidget(status_label, 2, 2, 1, 2)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 12, 0, 0)
        
        edit_btn = QPushButton()
        edit_btn.setIcon(self.get_icon("edit"))
        edit_btn.setToolTip("Edit Description")
        edit_btn.clicked.connect(lambda: self.edit_timer_description(timer_index))
        buttons_layout.addWidget(edit_btn)

        sound_btn = QPushButton()
        sound_btn.setIcon(self.get_icon("sound"))
        sound_btn.setToolTip("Change Sound")
        sound_btn.clicked.connect(lambda: self.edit_timer_sound(timer_index))
        buttons_layout.addWidget(sound_btn)

        rerun_btn = QPushButton()
        rerun_btn.setIcon(self.get_icon("rerun"))
        rerun_btn.setToolTip("Rerun Timer")
        rerun_btn.clicked.connect(lambda: self.rerun_timer(timer_index))
        buttons_layout.addWidget(rerun_btn)

        pause_btn = QPushButton()
        pause_btn.setIcon(self.get_icon("play")) # Icon changes based on state
        pause_btn.setToolTip("Pause/Resume")
        pause_btn.clicked.connect(lambda: self.toggle_timer(timer_index))
        buttons_layout.addWidget(pause_btn)

        stop_btn = QPushButton()
        stop_btn.setIcon(self.get_icon("stop"))
        stop_btn.setToolTip("Stop Timer")
        stop_btn.clicked.connect(lambda: self.stop_timer(timer_index))
        buttons_layout.addWidget(stop_btn)

        delete_btn = QPushButton()
        delete_btn.setIcon(self.get_icon("delete"))
        delete_btn.setToolTip("Delete Timer")
        delete_btn.clicked.connect(lambda: self.delete_timer(timer_index))
        buttons_layout.addWidget(delete_btn)

        card_layout.addLayout(buttons_layout, 3, 0, 1, 4)

        # Update status
        if timer["is_ringing"]:
            status_label.setText("Ringing")
            status_label.setStyleSheet("color: #ef4444;")
            pause_btn.setEnabled(False)
        elif timer.get("has_finished", False):
            status_label.setText("Time's Up")
            status_label.setStyleSheet("color: #f97316;")
            pause_btn.setIcon(self.get_icon("play"))
            pause_btn.setEnabled(False)
        elif timer.get("is_paused", False):
            status_label.setText("Paused")
            status_label.setStyleSheet("color: #f97316;")
            pause_btn.setIcon(self.get_icon("play"))
        else:
            status_label.setText("Running")
            status_label.setStyleSheet("color: #22c55e;")
            pause_btn.setIcon(self.get_icon("pause"))

        # Force style refresh to apply new properties
        card_widget.style().unpolish(card_widget)
        card_widget.style().polish(card_widget)

        return card_widget, time_label, status_label, pause_btn
    
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
            "is_paused": False,
            "has_finished": False
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
        timer["has_finished"] = True
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
        
        # Mark as finished
        timer["has_finished"] = True
        
        # Play alarm sound in loop
        self.play_alarm(timer_index)
    
    def pause_resume_timer(self, timer_index):
        if timer_index < len(self.timers):
            timer = self.timers[timer_index]
            
            # Don't pause if already completed
            if timer["is_ringing"] or timer.get("has_finished", False):
                return
            
            # Toggle pause state
            timer["is_paused"] = not timer.get("is_paused", False)
            
            # If resuming, signal the thread to continue
            if not timer["is_paused"] and timer_index in self.timer_events:
                self.timer_events[timer_index].set()
            
            self.save_timers()

    def rerun_timer(self, timer_index):
        """Reruns a timer from its original duration."""
        if timer_index < len(self.timers) and self.timers[timer_index]:
            timer = self.timers[timer_index]
            
            # Create styled message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Rerun Timer')
            msg_box.setText(f"Are you sure you want to rerun the timer '{timer['name']}'?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            # Apply theme to message box
            is_dark = detect_system_theme()
            apply_theme_to_widget(msg_box, is_dark)
            
            reply = msg_box.exec_()

            if reply == QMessageBox.No:
                return
            
            # Reset timer properties
            timer["remaining_seconds"] = timer["total_seconds"]
            timer["is_paused"] = False
            timer["is_ringing"] = False
            timer["has_finished"] = False
            
            self.save_timers()
            
            # Stop any previous alarm thread for this timer
            if timer_index in self.timer_threads and hasattr(self.timer_threads[timer_index], 'stop_event'):
                self.timer_threads[timer_index].stop_event.set()

            # Create a new threading event
            self.timer_events[timer_index] = threading.Event()
            
            # Start a new timer thread
            timer_thread = threading.Thread(
                target=self.run_timer,
                args=(timer_index,),
                daemon=True
            )
            self.timer_threads[timer_index] = timer_thread
            timer_thread.start()
            
            self.update_timers_display()

    def toggle_timer(self, timer_index):
        """Toggle timer pause/resume state"""
        if timer_index >= 0:
            self.pause_resume_timer(timer_index)
    
    def play_alarm(self, timer_index):
        if timer_index >= len(self.timers) or self.timers[timer_index] is None:
            return

        timer = self.timers[timer_index]
        sound_path = timer.get("sound_path", "")
        if not sound_path or not os.path.exists(sound_path):
            if self.settings.get("default_sound") and os.path.exists(self.settings["default_sound"]):
                sound_path = self.settings["default_sound"]
            else:
                sound_path = self.alarm_sound

        # Stop any existing alarm thread for this timer
        if timer_index in self.timer_threads and self.timer_threads[timer_index].is_alive():
             if hasattr(self.timer_threads[timer_index], 'stop_event'):
                self.timer_threads[timer_index].stop_event.set()

        # Use a thread to play sound in a loop via subprocess
        stop_event = threading.Event()
        def sound_loop(path, event):
            while not event.is_set():
                try:
                    # Use a short timeout to allow the loop to check the event
                    subprocess.run(["play", "-q", path], timeout=2)
                except subprocess.TimeoutExpired:
                    continue # Continue loop if timeout expires
                except FileNotFoundError:
                    print("Error: 'play' command not found. Please install 'sox'.")
                    break
                except Exception as e:
                    print(f"Error playing sound: {e}")
                    break
        
        alarm_thread = threading.Thread(target=sound_loop, args=(sound_path, stop_event), daemon=True)
        alarm_thread.stop_event = stop_event
        self.timer_threads[timer_index] = alarm_thread
        alarm_thread.start()

    def stop_timer(self, timer_index):
        if timer_index < len(self.timers) and self.timers[timer_index]:
            timer = self.timers[timer_index]

            # Stop the alarm sound thread
            if timer_index in self.timer_threads and hasattr(self.timer_threads[timer_index], 'stop_event'):
                self.timer_threads[timer_index].stop_event.set()

            timer['is_ringing'] = False
            timer['is_paused'] = True  # Mark as stopped
            timer['has_finished'] = True # Mark as finished
            
            self.save_timers()
            self.update_timers_display()

    def delete_timer(self, timer_index):
        """Delete a timer after confirmation."""
        if timer_index < len(self.timers) and self.timers[timer_index]:
            timer = self.timers[timer_index]
            
            # Create styled message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Delete Timer')
            msg_box.setText(f"Are you sure you want to delete the timer '{timer['name']}'?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            # Apply theme to message box
            is_dark = detect_system_theme()
            apply_theme_to_widget(msg_box, is_dark)
            
            reply = msg_box.exec_()

            if reply == QMessageBox.Yes:
                # Stop the alarm sound thread if it's running
                if timer_index in self.timer_threads and hasattr(self.timer_threads[timer_index], 'stop_event'):
                    self.timer_threads[timer_index].stop_event.set()

                # Perform a "soft delete" by setting the timer to None
                self.timers[timer_index] = None
                
                # Clean up resources
                if timer_index in self.media_players:
                    self.media_players[timer_index].stop()
                    del self.media_players[timer_index]
                
                # Use a more robust way to clean up thread-related resources
                event = self.timer_events.pop(timer_index, None)
                if event:
                    event.set() # Signal waiting threads to exit

                thread = self.timer_threads.pop(timer_index, None)
                if thread and thread.is_alive():
                    if hasattr(thread, 'stop_event'):
                        thread.stop_event.set()

                self.save_timers()
                self.update_timers_display()

    def update_timers_display(self):
        """Update the list of timers and the large display."""
        
        # Update the large timer display
        self.update_large_timer_display()

        # Check if we need to rebuild the list (timer count changed)
        current_timer_count = len([t for t in self.timers if t is not None])
        
        if current_timer_count != self.last_timer_count:
            # Only rebuild the list if timer count changed
            self.last_timer_count = current_timer_count
            self.rebuild_timers_list()
        else:
            # Just update the existing time labels without rebuilding
            self.update_timer_labels()

    def rebuild_timers_list(self):
        """Rebuild the entire timers list when timers are added/removed."""
        # Save current scroll position before updating
        scroll_bar = self.timers_list.verticalScrollBar()
        current_scroll_position = scroll_bar.value()

        # Update the list of all timers
        self.timers_list.clear()
        for i, timer in enumerate(self.timers):
            if timer is None:
                continue
            item = QListWidgetItem(self.timers_list)
            card_widget, time_label, status_label, pause_btn = self.create_timer_card(timer, i)
            
            # Ensure proper sizing for smooth scrolling
            card_widget.adjustSize()
            card_widget.updateGeometry()
            
            # Set a more predictable size hint
            size_hint = card_widget.sizeHint()
            if size_hint.height() < 100:  # Minimum height for timer cards
                size_hint.setHeight(120)
            item.setSizeHint(size_hint)
            
            self.timers_list.setItemWidget(item, card_widget)
            
            # Store dynamic labels for updates
            timer["ui_widgets"] = {
                "time_label": time_label,
                "status_label": status_label,
                "pause_btn": pause_btn
            }

        # Process pending events to ensure proper layout
        QApplication.processEvents()
        
        # Use QTimer to restore scroll position after a brief delay
        # This ensures the layout is fully updated before restoring position
        QTimer.singleShot(10, lambda: self.restore_scroll_position(current_scroll_position))

    def restore_scroll_position(self, position):
        """Restore scroll position with additional safety checks."""
        scroll_bar = self.timers_list.verticalScrollBar()
        if scroll_bar.maximum() >= position:
            scroll_bar.setValue(position)

    def update_timer_labels(self):
        """Update only the time labels without rebuilding the list."""
        for timer in self.timers:
            if timer and "ui_widgets" in timer:
                ui_widgets = timer["ui_widgets"]
                if "time_label" in ui_widgets and ui_widgets["time_label"]:
                    try:
                        ui_widgets["time_label"].setText(self.format_time(timer["remaining_seconds"]))
                        
                        # Update status label if available
                        if "status_label" in ui_widgets and ui_widgets["status_label"]:
                            if timer.get("is_ringing", False):
                                ui_widgets["status_label"].setText("Time's up!")
                            elif timer.get("has_finished", False):
                                ui_widgets["status_label"].setText("Time's up!")
                            elif timer.get("is_paused", False):
                                ui_widgets["status_label"].setText("Paused")
                            elif timer["remaining_seconds"] > 0:
                                ui_widgets["status_label"].setText("Running")
                            else:
                                ui_widgets["status_label"].setText("Finished")
                                
                        # Update pause button text and state if available
                        if "pause_btn" in ui_widgets and ui_widgets["pause_btn"]:
                            if timer.get("is_ringing", False) or timer.get("has_finished", False):
                                ui_widgets["pause_btn"].setText("Resume")
                                ui_widgets["pause_btn"].setEnabled(False)  # Disable for finished timers
                            elif timer.get("is_paused", False):
                                ui_widgets["pause_btn"].setText("Resume")
                                ui_widgets["pause_btn"].setEnabled(True)
                            else:
                                ui_widgets["pause_btn"].setText("Pause")
                                ui_widgets["pause_btn"].setEnabled(True)
                    except RuntimeError:
                        # Widget was deleted, remove from ui_widgets
                        timer.pop("ui_widgets", None)

    def get_primary_timer_index(self):
        """Get the index of the first non-finished timer."""
        for i, timer in enumerate(self.timers):
            if not timer.get("has_finished", False):
                return i
        return None

    def get_running_timer_indices(self):
        """Get list of all running (non-finished) timer indices."""
        running_indices = []
        for i, timer in enumerate(self.timers):
            if timer and not timer.get("has_finished", False):
                running_indices.append(i)
        return running_indices

    def switch_to_next_timer(self):
        """Switch to the next running timer in the active display."""
        running_indices = self.get_running_timer_indices()
        if len(running_indices) <= 1:
            return  # No next timer or only one timer
        
        try:
            current_pos = running_indices.index(self.current_primary_timer_index)
            next_pos = (current_pos + 1) % len(running_indices)
            self.current_primary_timer_index = running_indices[next_pos]
        except ValueError:
            # Current index not in running timers, use first one
            self.current_primary_timer_index = running_indices[0]

    def switch_to_previous_timer(self):
        """Switch to the previous running timer in the active display."""
        running_indices = self.get_running_timer_indices()
        if len(running_indices) <= 1:
            return  # No previous timer or only one timer
        
        try:
            current_pos = running_indices.index(self.current_primary_timer_index)
            prev_pos = (current_pos - 1) % len(running_indices)
            self.current_primary_timer_index = running_indices[prev_pos]
        except ValueError:
            # Current index not in running timers, use first one
            self.current_primary_timer_index = running_indices[0]

    def save_timers(self):
        """Save timers to a JSON file, excluding UI widgets."""
        timers_to_save = []
        for timer in self.timers:
            # Create a copy and remove non-serializable items
            t_copy = timer.copy()
            t_copy.pop("ui_widgets", None)
            timers_to_save.append(t_copy)
            
        with open(self.state_file, "w") as f:
            json.dump(timers_to_save, f, indent=4)

    def load_timers(self):
        """Load timers from a JSON file."""
        if os.path.exists(self.state_file) and self.settings.get("auto_start_timers", True):
            with open(self.state_file, "r") as f:
                self.timers = json.load(f)
                
            # Restart any running timers
            for i, timer in enumerate(self.timers):
                if timer is None:
                    continue
                
                # Create threading event for each timer
                self.timer_events[i] = threading.Event()
                
                # If timer has finished, do not restart it automatically
                if timer.get("has_finished", False):
                    continue

                # Resume paused timers in paused state
                if timer.get("is_paused", False):
                    continue
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
            "loop_sound": True,
            "auto_check_updates": True
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
            except Exception:
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
        
        # Stop all alarm threads
        for thread in self.timer_threads.values():
            if hasattr(thread, 'stop_event'):
                thread.stop_event.set()

        # Resume any paused threads so they can exit
        for i, timer_event in self.timer_events.items():
            timer_event.set()
        
        # Save timers
        self.save_timers()
        
        # Save settings
        self.save_settings()
        
        event.accept()

    def resizeEvent(self, event):
        """Adjust font size based on window size and apply responsive design."""
        base_font_size = 10
        width = self.width()
        height = self.height()
        
        # Determine screen size category and font size
        if width < 600:
            font_size = base_font_size * 0.9
            screen_size = "small"
        elif width < 900:
            font_size = base_font_size
            screen_size = "medium"
        else:
            font_size = base_font_size * 1.1
            screen_size = "large"

        # Apply screen size attribute for responsive CSS
        self.setProperty("screenSize", screen_size)
        
        # Apply compact mode for short displays (750px height or less for better accessibility)
        compact_mode = height <= 750
        self.setProperty("compactMode", compact_mode)
        
        # In compact mode, ensure the timers list gets adequate space
        if compact_mode and hasattr(self, 'timers_list'):
            # Calculate remaining space and set minimum height for timers list
            remaining_height = max(200, height - 400)  # Reserve space for header and active timer
            self.timers_list.setMinimumHeight(min(remaining_height, 300))
            self.timers_list.setMaximumHeight(remaining_height)
            
            # Reduce layout margins and spacing in compact mode
            central_widget = self.centralWidget()
            if hasattr(central_widget, 'widget'):
                main_widget = central_widget.widget()
                if main_widget and main_widget.layout():
                    layout = main_widget.layout()
                    layout.setContentsMargins(8, 8, 8, 8)
                    layout.setSpacing(8)
        else:
            # Restore normal margins and spacing
            central_widget = self.centralWidget()
            if hasattr(central_widget, 'widget'):
                main_widget = central_widget.widget()
                if main_widget and main_widget.layout():
                    layout = main_widget.layout()
                    layout.setContentsMargins(12, 12, 12, 12)
                    layout.setSpacing(12)
        
        # Update font
        font = self.font()
        font.setPointSize(int(font_size))
        self.setFont(font)
        
        # Update stylesheet to reflect font size changes for specific widgets
        self.update_timers_display()
        
        # Adjust header title font size
        try:
            title_label = self.findChild(QLabel, "headerTitleLabel")
            if title_label:
                title_font = title_label.font()
                title_font.setPointSize(int(font_size * 1.5))
                title_label.setFont(title_font)
        except AttributeError:
            # This can happen if the widget is not found during shutdown
            pass

        # Force style refresh to apply responsive changes
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Apply responsive styles to child widgets
        self.apply_responsive_styles()

        super().resizeEvent(event)

    def apply_responsive_styles(self):
        """Apply responsive styles to all child widgets"""
        screen_size = self.property("screenSize")
        compact_mode = self.property("compactMode")
        
        # Apply screen size and compact mode properties to all relevant child widgets
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'setProperty'):
                widget.setProperty("screenSize", screen_size)
                widget.setProperty("compactMode", compact_mode)
                # Force style refresh
                widget.style().unpolish(widget)
                widget.style().polish(widget)

    def get_primary_timer_index(self):
        """Get the index of the primary active timer (first running timer)"""
        for i, timer in enumerate(self.timers):
            if timer and not timer.get("has_finished", False):
                return i
        return -1

    def update_large_timer_display(self):
        """Update the large timer display with the current primary timer"""
        running_indices = self.get_running_timer_indices()
        
        # Update current primary timer index if needed
        if not running_indices:
            # No running timers
            self.active_timer_frame.setVisible(False)
            self.active_timer_placeholder.setVisible(True)
            return
        
        # Ensure current_primary_timer_index is valid
        if self.current_primary_timer_index not in running_indices:
            self.current_primary_timer_index = running_indices[0]
        
        timer = self.timers[self.current_primary_timer_index]
        self.active_timer_frame.setVisible(True)
        self.active_timer_placeholder.setVisible(False)
        
        # Update navigation button states
        self.large_prev_button.setEnabled(len(running_indices) > 1)
        self.large_next_button.setEnabled(len(running_indices) > 1)
        
        # Update display
        self.large_timer_name.setText(timer["name"])
        if timer.get("description"):
            self.large_timer_description.setText(timer["description"])
            self.large_timer_description.setVisible(True)
        else:
            self.large_timer_description.setVisible(False)
        
        # Format time display
        remaining = timer["remaining_seconds"]
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        
        if timer["is_ringing"] or timer.get("has_finished", False):
            time_text = "Time's Up"
        elif hours > 0:
            time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_text = f"{minutes:02d}:{seconds:02d}"
        
        self.large_timer_time.setText(time_text)
        
        # Update status and controls
        if timer["is_ringing"]:
            self.large_timer_status.setText("Time's Up (Ringing)")
            self.large_pause_button.setText("Stop")
            self.large_pause_button.setIcon(self.get_icon('stop'))
            self.large_pause_button.setEnabled(True)
        elif timer.get("has_finished", False):
            self.large_timer_status.setText("Time's Up")
            self.large_pause_button.setText("Resume")
            self.large_pause_button.setIcon(self.get_icon('play'))
            self.large_pause_button.setEnabled(False)  # Disable resume for finished timers
        elif timer.get("is_paused", False):
            self.large_timer_status.setText("Paused")
            self.large_pause_button.setText("Resume")
            self.large_pause_button.setIcon(self.get_icon('play'))
            self.large_pause_button.setEnabled(True)
        else:
            self.large_timer_status.setText("Running")
            self.large_pause_button.setText("Pause")
            self.large_pause_button.setIcon(self.get_icon('pause'))
            self.large_pause_button.setEnabled(True)
        

class TimerCreationDialog(QDialog):
    """Modal dialog for creating new timers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Timer")
        self.setModal(True)
        self.resize(450, 600)
        
        self.current_description = ""
        self.current_sound = ""
        
        # Apply theme before setting up UI
        is_dark = detect_system_theme()
        apply_theme_to_widget(self, is_dark)
        
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
        self.description_button = QPushButton(" Add Description")
        self.description_button.setIcon(self.parent().get_icon('edit'))
        self.description_button.clicked.connect(self.add_description)
        description_layout.addWidget(self.description_button)
        
        self.description_status = QLabel("No description")
        self.description_status.setObjectName("statusLabel")
        description_layout.addWidget(self.description_status)
        layout.addLayout(description_layout)
        
        # Sound selection
        sound_layout = QHBoxLayout()
        self.sound_button = QPushButton(" Select Sound")
        self.sound_button.setIcon(self.parent().get_icon('sound'))
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
                
        except (ValueError, TypeError):
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
            "is_paused": False,
            "has_finished": False
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


def load_svg_icon(icon_path, color="#374151", size=24):
    """Load and color an SVG icon"""
    try:
        if os.path.exists(icon_path):
            # Read SVG content and replace colors
            with open(icon_path, 'r') as f:
                svg_content = f.read()
            
            # Replace common fill attributes with the desired color
            svg_content = svg_content.replace('fill="black"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="#000"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')
            
            # Replace stroke attributes (many icons use stroke instead of fill)
            svg_content = svg_content.replace('stroke="black"', f'stroke="{color}"')
            svg_content = svg_content.replace('stroke="#000000"', f'stroke="{color}"')
            svg_content = svg_content.replace('stroke="#000"', f'stroke="{color}"')
            svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
            
            # If no fill or stroke attribute found, add fill to the root SVG element
            if 'fill=' not in svg_content and 'stroke=' not in svg_content:
                svg_content = svg_content.replace('<svg', f'<svg fill="{color}"')
            
            # Create renderer from modified SVG content
            renderer = QSvgRenderer()
            renderer.load(svg_content.encode('utf-8'))
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
           
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
    except Exception as e:
        print(f"Error loading icon {icon_path}: {e}")
    
    # Return empty icon if loading fails
    return QIcon()


def create_glass_checkbox(text="", checked=False, parent=None):
    """Create a checkbox with proper glass styling and tick marks"""
    from PyQt5.QtWidgets import QCheckBox
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QBrush, QLinearGradient
    
    class GlassCheckBox(QCheckBox):
        def __init__(self, text="", parent=None):
            super().__init__(text, parent)
            
        def paintEvent(self, event):
            # Call the parent paint event first to draw the text
            super().paintEvent(event)
            
            # Get the indicator rectangle
            option = self.getStyleOption()
            indicator_rect = self.style().subElementRect(
                self.style().SE_CheckBoxIndicator, option, self
            )
            
            # Create painter
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Determine theme
            is_dark = self.property("darkTheme") == True
            
            # Draw custom indicator background
            if is_dark:
                if self.isChecked():
                    # Dark theme checked
                    gradient = QLinearGradient(indicator_rect.topLeft(), indicator_rect.bottomRight())
                    gradient.setColorAt(0, QColor(92, 170, 197, 242))  # rgba(92, 170, 197, 0.95)
                    gradient.setColorAt(1, QColor(92, 205, 213, 229))  # rgba(92, 205, 213, 0.9)
                    painter.setBrush(QBrush(gradient))
                    painter.setPen(QPen(QColor(92, 170, 197, 204), 2))  # rgba(92, 170, 197, 0.8)
                else:
                    # Dark theme unchecked
                    painter.setBrush(QBrush(QColor(45, 55, 72, 128)))  # rgba(45, 55, 72, 0.5)
                    painter.setPen(QPen(QColor(255, 255, 255, 51), 2))  # rgba(255, 255, 255, 0.2)
            else:
                if self.isChecked():
                    # Light theme checked
                    gradient = QLinearGradient(indicator_rect.topLeft(), indicator_rect.bottomRight())
                    gradient.setColorAt(0, QColor(60, 101, 160, 242))  # rgba(60, 101, 160, 0.95)
                    gradient.setColorAt(1, QColor(92, 170, 197, 229))  # rgba(92, 170, 197, 0.9)
                    painter.setBrush(QBrush(gradient))
                    painter.setPen(QPen(QColor(60, 101, 160, 204), 2))  # rgba(60, 101, 160, 0.8)
                else:
                    # Light theme unchecked
                    painter.setBrush(QBrush(QColor(255, 255, 255, 77)))  # rgba(255, 255, 255, 0.3)
                    painter.setPen(QPen(QColor(255, 255, 255, 102), 2))  # rgba(255, 255, 255, 0.4)
            
            # Draw rounded rectangle
            painter.drawRoundedRect(indicator_rect, 8, 8)
            
            # Draw checkmark if checked
            if self.isChecked():
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                
                # Draw checkmark path
                check_size = min(indicator_rect.width(), indicator_rect.height()) * 0.6
                center_x = indicator_rect.center().x()
                center_y = indicator_rect.center().y()
                
                # Checkmark coordinates (relative to center)
                points = [
                    (center_x - check_size/3, center_y - check_size/6),
                    (center_x - check_size/6, center_y + check_size/6),
                    (center_x + check_size/3, center_y - check_size/3)
                ]
                
                # Draw checkmark lines
                painter.drawLine(int(points[0][0]), int(points[0][1]), 
                               int(points[1][0]), int(points[1][1]))
                painter.drawLine(int(points[1][0]), int(points[1][1]), 
                               int(points[2][0]), int(points[2][1]))
            
            painter.end()
        
        def getStyleOption(self):
            from PyQt5.QtWidgets import QStyleOptionButton
            option = QStyleOptionButton()
            option.initFrom(self)
            option.text = self.text()
            if self.isChecked():
                option.state |= self.style().State_On
            else:
                option.state |= self.style().State_Off
            return option
    
    # Create the custom checkbox
    checkbox = GlassCheckBox(text, parent)
    checkbox.setChecked(checked)
    
    # Apply styling (without the indicator since we're drawing it ourselves)
    checkbox.setStyleSheet("""
        QCheckBox {
            font-weight: 500;
            spacing: 10px;
            color: #1D1D1F;
        }
        
        QCheckBox[darkTheme="true"] {
            color: #F5F5F7;
        }
        
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border: none;
            background: transparent;
        }
    """)
    
    # Apply theme
    is_dark = detect_system_theme()
    apply_theme_to_widget(checkbox, is_dark)
    
    return checkbox

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
