# SnapZones

Linux window management tool inspired by Windows PowerToys FancyZones. Snap windows to predefined zones using keyboard modifiers and visual overlays.

## Features

- **Zone-based window snapping**: Hold modifier key + drag window to snap to zones
- **Visual zone editor**: Fullscreen WYSIWYG editor for creating custom layouts
- **Multiple layouts**: Global layout library with workspace-specific mappings
- **Preset layouts**: Halves, thirds, quarters, and 3x3 grid
- **Keyboard shortcuts**: Quick access to editor and snapping functionality

## System Requirements

- **Linux with X11** (Wayland not supported due to window manipulation limitations)
- **Python 3.10+**
- **X11 display server** (required - set DISPLAY environment variable)

## Dependencies

### System Packages (Ubuntu/Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                 libcairo2-dev python3-xlib libx11-dev python3-dev
```

### Python Packages

```bash
pip install -r requirements.txt
```

Required packages:
- `python-xlib>=0.33` - X11 window management
- `pynput>=1.7.6` - Global keyboard/mouse monitoring
- `PyGObject>=3.42,<3.50` - GTK3 bindings
- `pycairo>=1.20.0` - Cairo graphics

## Installation

### Quick Install

```bash
git clone <repository-url>
cd SnapZones
./install.sh
```

For non-interactive installation (useful in scripts):
```bash
./install.sh -y
```

The installer will:
- Check and install system dependencies (with your permission)
- Set up Python virtual environment
- Install SnapZones scripts to `~/.local/bin/`
- Register native GNOME keyboard shortcut (Super+Shift+Tab)
- Configure autostart on login
- Start the daemon immediately

### Manual Installation

```bash
# Install system dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                 libcairo2-dev python3-xlib libx11-dev python3-dev

# Create virtual environment and install Python packages
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run manually
python -m snap_zones.daemon          # Start daemon
python -m snap_zones.zone_editor     # Open editor
```

### Uninstallation

```bash
./uninstall.sh
```

For non-interactive uninstallation:
```bash
./uninstall.sh -y
```

Optionally removes configuration and layouts.

## Usage

### Default Shortcuts

- **Alt + Drag Window**: Show zone overlay and snap to zone
- **Super + Shift + Tab**: Open zone editor (native GNOME keyboard shortcut)

### Zone Editor Controls

- **Click & Drag**: Draw new zone
- **Click on zone**: Select zone
- **Drag selected**: Move zone
- **Drag handles**: Resize zone (8 resize handles: corners + edges)
- **ESC**: Exit editor
- **H**: Toggle help panel
- **D**: Toggle dimension display (position and size overlays)
- **S**: Save zones manually (auto-saves on all modifications)
- **N**: Create new layout
- **Delete**: Delete selected zone
- **1-4**: Apply presets (1=halves, 2=thirds, 3=quarters, 4=grid)

### Layout Manager

The layout manager window is always visible when the zone editor is open:

- **Single-click**: Select layout
- **Double-click**: Load layout for editing (automatically maps current workspace to this layout)
- **Slow-click or F2**: Rename selected layout
- **Buttons**: Create New, Rename, Delete, Close Editor

**Auto-Workspace Mapping**: When you double-click a layout or create a new layout, SnapZones automatically maps your current workspace to that layout. The daemon will then show that layout's zones when you Alt+Drag windows on that workspace.

## Configuration

Configuration files stored in `~/.config/snapzones/`:

- `layouts/*.json` - Named layout files
- `workspace_layouts.json` - Workspace-to-layout mappings (auto-updated by editor)
- `daemon.pid` - Daemon process ID

### Workspace-Layout Mapping

SnapZones automatically maps workspaces to layouts when you:
- **Double-click a layout** in the Layout Manager
- **Create a new layout** with the "Create New" button

The mapping is saved to `workspace_layouts.json`. You can also manually edit this file if needed:
```json
{
  "0": "default",
  "1": "coding",
  "2": "design"
}
```

The daemon automatically reloads the mappings, so changes take effect immediately without restarting.

**Native Shortcuts**: SnapZones uses GNOME's native keyboard shortcut system (`gsettings`) rather than capturing all keyboard events. This ensures proper integration with your desktop environment.

## Current Status

**Version**: 0.6.2

**Completed**:
- ✅ Core window management (X11)
- ✅ Global input monitoring
- ✅ Zone overlay system
- ✅ Modifier+drag snapping workflow (Alt+Drag)
- ✅ Fullscreen zone editor with WYSIWYG editing
- ✅ Global layout library system
- ✅ Workspace-to-layout mapping
- ✅ Layout rename functionality
- ✅ Zone dimension display
- ✅ Auto-save on modifications
- ✅ Background daemon with PID locking
- ✅ Native GNOME keyboard shortcut integration (Super+Shift+Tab)
- ✅ Autostart on login
- ✅ Installation and uninstallation scripts
- ✅ Status management utility
- ✅ Auto-map workspace to layout when switching layouts in editor

**Planned**:
- ⏸️ Keyboard navigation (Super+Arrow keys to move windows between zones)
- ⏸️ System tray indicator
- ⏸️ Settings dialog
- ⏸️ Deployment packaging

## Development

### Project Structure

```
src/snap_zones/
├── window_manager.py    # X11 window operations
├── zone.py              # Zone data structures, presets
├── input_monitor.py     # Mouse/keyboard tracking, hotkeys
├── overlay.py           # Transparent zone overlay
├── snapper.py           # Core snapping orchestration
├── zone_editor.py       # Fullscreen zone editor
└── layout_library.py    # Global layout management
```

### Running Tests

```bash
# Test window management
python -m snap_zones.window_manager --list

# Test input monitoring
python -m snap_zones.input_monitor --test-hotkeys

# Test overlay
python -m snap_zones.overlay --show --preset grid3x3

# Interactive snapping
python -m snap_zones.snapper --interactive --modifier alt

# Zone editor
python -m snap_zones.zone_editor
```

## License

[To be determined]

## Credits

Inspired by Microsoft PowerToys FancyZones.
