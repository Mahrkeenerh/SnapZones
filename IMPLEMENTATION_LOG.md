# SnapZones Implementation Log

Linux window management tool inspired by Windows PowerToys FancyZones.

## Project Setup ✅

- Python venv with `python-xlib>=0.33`, `pynput>=1.7.6`
- Config directory: `~/.config/snapzones/`

---

## Phase 1: Core Window Management ✅

**Date:** 2025-10-07 | **File:** `src/snap_zones/window_manager.py`

### Implemented
- **WindowManager**: List windows, get active window, move/resize windows
- **Zone**: Geometric zones with overlap detection, JSON persistence
- **ZoneManager**: CRUD operations, preset layouts (halves/thirds/quarters/grid3x3)

### CLI
```bash
python src/snap_zones/window_manager.py --list
python src/snap_zones/window_manager.py --move-active X Y W H
python src/snap_zones/zone.py --create-preset quarters --save FILE
```

### Key Features
- X11 `_NET_*` protocols for window management
- UTF-8 window titles, automatic unmaximize
- JSON zone persistence with version field
- Smallest-zone-first priority for overlapping zones

---

## Phase 2: Input Monitoring System ✅

**Date:** 2025-10-07 | **File:** `src/snap_zones/input_monitor.py`

### Implemented
- **MouseTracker**: Position, drag detection, button states
- **KeyboardTracker**: Modifier keys (Shift/Ctrl/Alt/Super)
- **InputMonitor**: Combined mouse+keyboard with modifier-aware drag
- **HotkeyManager**: Global hotkey registration and triggering

### CLI
```bash
python src/snap_zones/input_monitor.py --track-drag --duration 10
python src/snap_zones/input_monitor.py --track-shift-drag --duration 15
python src/snap_zones/input_monitor.py --test-hotkeys --duration 15
```

### Key Features
- `pynput` for global input monitoring
- Drag operations with modifier detection
- Hotkey registration with arbitrary modifier combinations
- Non-blocking listeners in separate threads

---

## Phase 3: Overlay Rendering System ✅

**Date:** 2025-10-07 | **File:** `src/snap_zones/overlay.py`

### Implemented
- **OverlayWindow**: Full-screen transparent GTK window with zone display
- **Zone Visualization**: Semi-transparent colored zones with borders and labels
- **Hit Detection**: Mouse hover highlighting, click selection
- **OverlayManager**: Lifecycle management for overlay window

### CLI
```bash
python src/snap_zones/overlay.py --show --preset quarters --duration 10
python src/snap_zones/overlay.py --show --load FILE --duration 30
python src/snap_zones/overlay.py --show --preset grid3x3
```

### Key Features
- GTK3/Cairo for transparent overlay rendering
- Real-time mouse hover highlighting
- Click-to-select zone functionality
- Escape key to cancel
- Smallest-zone-first priority for overlapping zones

---

## Phase 4: Core Snapping Logic ✅

**Date:** 2025-10-07 | **File:** `src/snap_zones/snapper.py`

### Implemented
- **WindowSnapper**: Core snapping orchestration with window management integration
- **Workspace Support**: Load/save workspace-specific zone configurations
- **Snap-to-Zone**: Move and resize active window to selected zone
- **Shift+Drag Integration**: Complete workflow with InputMonitor and OverlayManager

### CLI
```bash
# Snap active window to preset
python src/snap_zones/snapper.py --snap-active quarters

# Interactive Shift+drag workflow
python src/snap_zones/snapper.py --interactive

# List workspaces with zone counts
python src/snap_zones/snapper.py --list-workspaces
```

### Key Features
- WindowSnapper orchestrates all components (WindowManager, ZoneManager, OverlayManager, InputMonitor)
- Workspace-aware zone loading: `zones_ws0.json`, `zones_ws1.json`, etc.
- Fallback to default `zones.json` if workspace-specific zones not found
- Original window geometry tracking for restore functionality
- Shift+drag callbacks in InputMonitor trigger overlay display
- Zone selection triggers snap-to-zone operation

---

## Phase 5: Zone Editor ✅

**Date:** 2025-10-07 | **File:** `src/snap_zones/zone_editor.py`

### Implemented
- **ZoneEditorOverlay**: Fullscreen transparent overlay for zone editing
- **In-Place Editing**: Draw and edit zones directly over desktop (WYSIWYG)
- **Zone Manipulation**: Select, move, resize, and delete zones
- **Visual Feedback**: Resize handles, selection highlighting, zone labels
- **Preset Integration**: Apply built-in layout presets via keyboard shortcuts
- **Keyboard Controls**: Complete keyboard-driven workflow

### CLI
```bash
# Launch fullscreen zone editor overlay
python -m src.snap_zones.zone_editor

# Load existing layout
python -m src.snap_zones.zone_editor --load ~/.config/snapzones/zones.json
```

### Key Features (Block 5.1: Basic Canvas Editor)
- Fullscreen transparent GTK overlay (not a window)
- Draw zones directly over actual desktop for precise positioning
- Semi-transparent zone rendering with borders and labels
- Real-time visual feedback during drawing
- Auto-load existing zones from `~/.config/snapzones/zones.json`

### Key Features (Block 5.2: Zone Manipulation)
- Click to select zones (smallest zone priority for overlaps)
- Drag selected zone to move (orange highlight when selected)
- Resize via 8 handles (corners + edges): nw, ne, sw, se, n, s, e, w
- Delete selected zone with Delete key
- Canvas bounds enforcement and minimum zone size (3%)
- Status bar at bottom shows current operation

### Key Features (Block 5.3: Preset System)
- Number key shortcuts for presets: 1=halves, 2=thirds, 3=quarters, 4=grid3x3
- Integration with existing ZoneManager preset system
- Status bar shows applied preset and zone count

### Keyboard Controls
- **ESC**: Exit editor
- **H**: Toggle help panel
- **S**: Save zones to `~/.config/snapzones/zones.json`
- **L**: Load zones from file
- **N**: New (clear all zones)
- **Delete**: Delete selected zone
- **1-4**: Apply preset layouts

### Visual Design
- Blue zones (unselected): semi-transparent for desktop visibility
- Orange zones (selected): shows 8 white resize handles
- Help panel: centered dark overlay with all controls listed
- Status bar: bottom of screen with operation feedback

### System Requirements
- GTK3 development libraries: `libgirepository1.0-dev`, `libcairo2-dev`, `pkg-config`, `python3-dev`
- Python packages: `PyGObject>=3.42,<3.50`, `pycairo>=1.20.0`

---

## Phase 6: Keyboard Navigation ⏸️

**Status:** Pending

---

## Phase 7: Polish & System Integration ⏸️

**Status:** Pending

---

## Version History

- **v0.1.0** (2025-10-07) - Phase 1: Core Window Management
- **v0.2.0** (2025-10-07) - Phase 2: Input Monitoring System
- **v0.3.0** (2025-10-07) - Phase 3: Overlay Rendering System
- **v0.4.0** (2025-10-07) - Phase 4: Core Snapping Logic
- **v0.5.0** (2025-10-07) - Phase 5: Zone Editor
