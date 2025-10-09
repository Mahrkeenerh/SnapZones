# SnapZones

<p align="center">
  <img src="assets/logo.png" alt="SnapZones Logo" width="400"/>
</p>

**Powerful window management for Linux** - Snap windows to predefined zones using keyboard modifiers and visual overlays. Inspired by Windows PowerToys FancyZones.

## Features

- 🎯 **Zone-based window snapping** - Hold Alt + drag to snap windows to custom zones
- 🎨 **Visual zone editor** - Create and edit layouts with live preview on your desktop
- 📐 **Preset layouts** - Quick layouts: halves, thirds, quarters, and 3x3 grid
- 🗂️ **Multiple layouts** - Different layouts for different workspaces
- 📦 **Snap app support** - Works with snap-confined apps like Slack (with Window Calls extension)
- ⚡ **Fast & lightweight** - Minimal resource usage, runs silently in background

## System Requirements

- **Linux with X11** (Wayland not currently supported)
- **Python 3.10+**
- **GNOME Desktop Environment** (for keyboard shortcuts)

## Installation

### Quick Install

```bash
git clone https://github.com/yourusername/SnapZones.git
cd SnapZones
./install.sh
```

The installer will:
- ✅ Install required system packages (with your permission)
- ✅ Set up Python virtual environment
- ✅ Install SnapZones to `~/.local/bin/`
- ✅ Configure keyboard shortcut (Super+Shift+Tab)
- ✅ Set up autostart on login
- ✅ Start the daemon

That's it! SnapZones is ready to use.

### Optional: Snap Application Support

If you use snap-confined applications (like Slack, Discord, Spotify) and want to snap them to zones, install the Window Calls GNOME extension:

**Option 1: From GNOME Extensions (recommended)**
1. Visit https://extensions.gnome.org/extension/4724/window-calls/
2. Click "Install"
3. Restart SnapZones: `snapzones-status restart`

**Option 2: From source**
```bash
git clone https://github.com/ickyicky/window-calls.git /tmp/window-calls
cd /tmp/window-calls
make install
gnome-extensions enable window-calls@domandoman.xyz
snapzones-status restart
```

**Why?** Snap-confined apps have security restrictions that prevent direct window manipulation. Window Calls provides a safe interface for SnapZones to move these windows. Regular (non-snap) applications work perfectly without it.

## Usage

### Quick Start

1. **Press Alt + Drag a window** - Zone overlay appears
2. **Drag to a zone** - Zone highlights
3. **Release mouse** - Window snaps to zone

That's it! No clicking, no extra keys.

### Opening the Zone Editor

Press **Super + Shift + Tab** to open the zone editor

### Zone Editor Controls

**Creating Zones:**
- **Click & Drag** empty space to draw a new zone

**Editing Zones:**
- **Click zone** to select it
- **Drag zone** to move it
- **Drag handles** to resize (8 handles: corners + edges)
- **Delete** key to remove selected zone

**Quick Actions:**
- **1, 2, 3, 4** - Apply preset layouts (halves, thirds, quarters, grid)
- **H** - Show/hide help
- **D** - Toggle dimension labels
- **ESC** - Exit editor

**Layout Manager:**
- **Double-click layout** - Switch to that layout for current workspace
- **Create New** button - Create a new layout
- **F2** or slow-click - Rename layout
- **Delete** button - Delete selected layout

### Managing Layouts

SnapZones automatically maps layouts to workspaces. When you double-click a layout or create a new one, it's assigned to your current workspace.

**Example workflow:**
1. Switch to workspace 1
2. Open zone editor (Super+Shift+Tab)
3. Double-click "Coding" layout
4. Zone editor shows "Coding" zones
5. Exit editor - workspace 1 now uses "Coding" layout
6. Alt+Drag windows - they snap to "Coding" zones

## Managing SnapZones

### Check Status
```bash
snapzones-status
```

### Restart Daemon
```bash
snapzones-status restart
```

Restart is needed after:
- Installing/updating Window Calls extension
- Configuration changes
- Troubleshooting issues

### Stop Daemon
```bash
snapzones-status stop
```

### View Logs
```bash
snapzones-status logs
```

### Uninstall
```bash
cd SnapZones
./uninstall.sh
```

## Configuration

Configuration files are stored in `~/.config/snapzones/`:

- `layouts/` - Your custom zone layouts
- `workspace_layouts.json` - Workspace-to-layout mappings
- `daemon.pid` - Daemon process ID (managed automatically)

**Note:** Zones are automatically constrained to your usable screen area, excluding panels and docks. Windows won't be placed under your top panel.

## Troubleshooting

### Snap apps won't move
Install the Window Calls extension (see installation section above). SnapZones will automatically detect and use it.

### Keyboard shortcut doesn't work
Check if Super+Shift+Tab is already used by another application:
```bash
gsettings get org.gnome.desktop.wm.keybindings switch-group-backward
```

### Daemon not starting
Check logs for error messages:
```bash
snapzones-status logs
```

### Zone editor won't open
Make sure the daemon is running:
```bash
snapzones-status
```

If stopped, restart it:
```bash
snapzones-status restart
```

## How It Works

SnapZones works by:
1. **Monitoring** Alt key state and mouse movements
2. **Detecting** when you start dragging a window
3. **Showing** a transparent overlay with your zones
4. **Snapping** the window when you release it over a zone

**Smart Detection:**
- Uses X11 for window management
- Window Calls extension for snap-confined apps (optional)
- Automatically falls back to X11 if Window Calls isn't available
- Respects panel and dock areas

## License

[To be determined]

## Credits

Inspired by Microsoft PowerToys FancyZones.

Built with Python, GTK3, Cairo, and python-xlib.

Optional integration with [Window Calls](https://github.com/ickyicky/window-calls) GNOME extension.
