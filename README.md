# SnapZones

<p align="center">
  <img src="assets/logo.png" alt="SnapZones Logo" width="400"/>
</p>

**Window management for Linux** - Snap windows to predefined zones using keyboard modifiers and visual overlays. Inspired by Windows PowerToys FancyZones.

## ⚠️ Disclaimer

This entire application was vibe-coded with Claude. I take no responsibility for it breaking your system. I developed it for myself, I use it regularly, and I applied best practices while developing it with Claude and tested it thoroughly. It works for me - your mileage may vary. Use at your own risk.

## Features

- 🎯 **Zone-based window snapping** - Hold Alt + drag to snap windows to custom zones
- 🔀 **Overlapping zones support** - Not limited to grids - zones can overlap and be positioned freely
- 🎨 **Visual zone editor** - Create and edit layouts with live preview on your desktop
- 📐 **Preset layouts** - Quick layouts: halves, thirds, quarters, and 3x3 grid
- 🗂️ **Multiple layouts** - Different layouts for different workspaces
- ⚡ **Fast & lightweight** - Minimal resource usage, runs silently in background

## System Requirements

- **Linux with X11** (Wayland not currently supported)
- **Python 3.10+**
- **GNOME Desktop Environment** (for keyboard shortcuts)

**Verify your system:**
```bash
echo "X11: $XDG_SESSION_TYPE" && gnome-shell --version 2>/dev/null
```

## Installation

### System Packages

First, install the required system packages:

```bash
sudo apt install python3 python3-pip python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-wnck-3.0 python3-xlib
```

### Optional: Snap Application Support

If you use snap-confined applications (like Slack, Discord, Spotify) and want to snap them to zones, install the Window Calls GNOME extension **before installing SnapZones**:

1. Visit https://extensions.gnome.org/extension/4724/window-calls/
2. Click "Install"

If you install Window Calls after installing SnapZones, run:
```bash
snapzones-status restart
```

### Quick Install

```bash
git clone https://github.com/Mahrkeenerh/SnapZones.git
cd SnapZones
./install.sh
```

The installer will:
- ✅ Set up Python virtual environment
- ✅ Install SnapZones to `~/.local/bin/`
- ✅ Configure keyboard shortcut (Super+Shift+Tab)
- ✅ Set up autostart on login
- ✅ Start the daemon

That's it! SnapZones is ready to use.

## Usage

### Quick Start

1. **Press Alt + Drag a window** - Zone overlay appears
2. **Drag to a zone** - Zone highlights
3. **Release mouse** - Window snaps to zone

That's it! No clicking, no extra keys.

### Opening the Zone Editor

Press **Super + Shift + Tab** to open the zone editor

### Zone Editor Controls

- **H** - Show/hide help

**Creating Zones:**
- **Click & Drag** empty space to draw a new zone

**Precise Movement (1px accuracy):**
- **Arrow Keys** - Move selected zone by 1 pixel
- **Alt + Arrow Keys** - Resize selected zone by 1 pixel

## Planned Features

- 🖱️ **System tray icon** - Quick access to settings and controls
- ⚙️ **Settings and configurations** - Customizable behavior and preferences
- 🧲 **Multi-zone proximity snapping** - Combined area detection when zones are close together
- 📏 **Magnetic edge snapping in editor** - Toggle-able snap-to-grid for precise zone alignment

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Inspired by Microsoft PowerToys FancyZones.

Built with Python, GTK3, Cairo, and python-xlib.

Optional integration with [Window Calls](https://github.com/ickyicky/window-calls) GNOME extension.
