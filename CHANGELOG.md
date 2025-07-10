# Changelog

All notable changes to TimeRing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-11

### Added

#### Core Features
- Multiple concurrent timer support
- Custom timer names and descriptions
- Pause, resume, and rerun functionality
- Persistent timer state across application restarts
- Custom notification sounds per timer
- Desktop notifications with configurable urgency
- Modern Qt-based user interface with system theme integration

#### UI/UX Improvements
- **Active Timer Navigation**: Added Previous/Next buttons to navigate between multiple running timers
- **Enhanced Status Display**: Clear visual distinction between "Time's Up", "Paused", and "Running" states
- **Compact Mode**: Responsive design that automatically adapts to displays ≤750px height
- **Improved Typography**: Increased font sizes and weights for better readability
- **Enhanced Visual Hierarchy**: Better contrast and spacing for timer elements
- **Glowing Highlights**: Visual feedback for running timers with CSS animations
- **Scroll Optimization**: Pixel-perfect scrolling with position preservation in timer lists

#### Settings & Configuration
- **Auto Update Check**: Automatic checking for new releases with one-click updates
- Comprehensive settings dialog with tabbed interface
- Auto-start timers on application launch option
- Notification preferences (urgency, description inclusion)
- Sound settings (default sound, loop options)
- Theme-aware UI components

#### Technical Improvements
- **Smooth Scrolling**: Fixed scroll-to-top glitches in timer lists
- **Performance Optimization**: Efficient UI updates that only rebuild when necessary
- **Responsive Design**: Dynamic font sizes and layout adjustments based on window size
- **Memory Management**: Proper cleanup of VLC players and threading resources
- **Error Handling**: Robust error handling for audio playback and file operations

### Technical Details

#### Dependencies
- PyQt5 >= 5.15.0 for the GUI framework
- python-vlc >= 3.0.0 for audio playback
- requests >= 2.25.0 for update checking

#### File Structure
- `main.py` - Main application with timer logic and UI
- `glass_checkbox.py` - Custom glass-style checkbox widget
- `style.qss` - Application styling and responsive design
- `version.py` - Version tracking for auto-updates
- `requirements.txt` - Python dependencies
- `images/` - Application icons and logo
- `sounds/` - Default notification sounds

#### Configuration
- Settings stored in `~/.config/TimeRing/settings.json`
- Timer state persisted in `~/.config/TimeRing/timers.json`
- Automatic migration of settings for missing keys

### Performance

#### Optimizations
- **UI Updates**: Separated timer list rebuilding from label updates
- **Scroll Performance**: Implemented pixel-based scrolling with consistent item sizing
- **Memory Usage**: Proper cleanup of media players and threading resources
- **Responsive Rendering**: Dynamic CSS property updates based on screen size

#### Accessibility
- **Small Screen Support**: Optimized for 720p displays and smaller
- **Keyboard Navigation**: Full keyboard accessibility for all controls
- **Visual Feedback**: Clear status indicators and button states
- **Theme Integration**: Automatic light/dark theme detection and application

### Platform Support

#### Linux (Primary)
- Native desktop notifications via `libnotify`
- System theme integration
- Audio playback via VLC media framework
- File dialog theming for consistent appearance

#### Cross-Platform Considerations
- Qt-based UI for potential Windows/macOS compatibility
- Modular audio system for platform-specific implementations
- Standardized file paths and configuration management

### Security & Privacy
- No network requests except for update checking (user-configurable)
- Local configuration and timer state storage
- No telemetry or usage tracking
- Open source with MIT license for full transparency

---

## Version History

### Development Milestones

- **v1.0.0**: Initial stable release with full feature set
- **v0.9.x**: Beta testing and UI/UX refinements
- **v0.8.x**: Core timer functionality implementation
- **v0.7.x**: Basic GUI and settings framework
- **v0.6.x**: Audio system integration
- **v0.5.x**: Project initialization and architecture design

### Future Roadmap

#### Planned Features (v1.1.0)
- [ ] Timer templates and presets
- [ ] Import/export timer configurations
- [ ] System tray integration
- [ ] Productivity statistics and reporting
- [ ] Multiple alert types (visual, haptic feedback)

#### Planned Features (v1.2.0)
- [ ] Pomodoro timer integration
- [ ] Team/collaborative timers
- [ ] Plugin system for custom extensions
- [ ] Advanced scheduling and recurring timers
- [ ] Cross-platform notification improvements

#### Long-term Goals
- [ ] Mobile companion app
- [ ] Cloud synchronization (optional)
- [ ] Advanced theming system
- [ ] API for third-party integrations
- [ ] Internationalization (i18n) support

---

**Note**: This changelog follows semantic versioning. Breaking changes will increment the major version, new features increment the minor version, and bug fixes increment the patch version.
