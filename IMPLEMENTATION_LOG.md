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

## Phase 4: Core Snapping Logic ⏸️

**Status:** Pending

---

## Phase 5: Zone Editor ⏸️

**Status:** Pending

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
