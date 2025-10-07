# SnapZones Implementation Log

This document tracks the implementation progress of SnapZones, a Linux window management tool inspired by Windows PowerToys FancyZones.

## Project Setup

**Date:** 2025-10-07
**Status:** ✅ Complete

- Created Python virtual environment (`venv/`)
- Installed dependencies:
  - `python-xlib>=0.33` - X11 window management
  - `pynput>=1.7.6` - Global input monitoring
- Created project structure:
  ```
  SnapZones/
  ├── venv/
  ├── src/snap_zones/
  │   ├── __init__.py
  │   ├── window_manager.py
  │   └── zone.py
  ├── tests/
  ├── requirements.txt
  ├── .gitignore
  ├── IMPLEMENTATION_PLAN.md
  └── IMPLEMENTATION_LOG.md
  ```

---

## Phase 1: Core Window Management ✅ COMPLETE

### Block 1.1: Window Detection System ✅

**Status:** Complete
**File:** `src/snap_zones/window_manager.py`

**Implemented:**
- `WindowInfo` class - Data structure for window properties (ID, title, geometry)
- `WindowManager` class with methods:
  - `get_all_windows()` - List all normal application windows
  - `get_active_window()` - Get currently focused window
  - `get_window_at_position(x, y)` - Get window under cursor
  - `get_window_title(window)` - Extract window title (UTF-8 support)
  - `get_window_geometry(window)` - Get window position and size
  - `is_normal_window(window)` - Filter out desktop/dock/system windows

**Test Results:**
```bash
$ python src/snap_zones/window_manager.py --list
# Successfully detected 11 windows with accurate titles and geometry

$ python src/snap_zones/window_manager.py --active
# Correctly identified active window
```

**Key Features:**
- Uses X11 `_NET_CLIENT_LIST` for window enumeration
- Filters non-application windows (desktop, dock, toolbar, etc.)
- Handles UTF-8 window titles via `_NET_WM_NAME`
- Translates window coordinates to root window space

---

### Block 1.2: Window Manipulation ✅

**Status:** Complete
**File:** `src/snap_zones/window_manager.py`

**Implemented:**
- `move_resize_window(window_id, x, y, width, height)` - Move and resize windows
- `_unmaximize_window(window)` - Remove maximized state before moving
- `get_window_by_id(window_id)` - Query window by ID
- Command-line interface with `--move-active` flag

**Test Results:**
```bash
$ python src/snap_zones/window_manager.py --move-active 100 100 800 600
# Window successfully moved and resized
# Verified new geometry after operation
```

**Key Features:**
- Uses `_NET_MOVERESIZE_WINDOW` for proper window manager integration
- Automatically unmaximizes windows before repositioning
- Respects window manager hints and protocols
- Synchronous operation with display flush/sync

**Known Behavior:**
- Window coordinates may show negative offsets due to window decorations (expected X11 behavior)

---

### Block 1.3: Zone Data Structure ✅

**Status:** Complete
**File:** `src/snap_zones/zone.py`

**Implemented:**

#### `Zone` Class (dataclass)
- Properties: `x`, `y`, `width`, `height`, `name`, `color`
- Computed properties:
  - `x2`, `y2` - Right/bottom edges
  - `center` - Center point
  - `area` - Zone area in pixels
- Methods:
  - `contains_point(x, y)` - Point-in-zone detection
  - `overlaps(other)` - Zone overlap detection
  - `overlap_area(other)` - Calculate overlap area
  - `to_dict()` / `from_dict()` - JSON serialization

#### `ZoneManager` Class
- Zone collection management with CRUD operations:
  - `add_zone(zone)` - Add new zone
  - `remove_zone(index)` - Remove by index
  - `remove_zone_at_point(x, y)` - Remove by point
  - `get_zone_at_point(x, y)` - Find zone at point (smallest area priority)
  - `get_all_zones_at_point(x, y)` - Get all overlapping zones
  - `get_overlapping_zones(zone)` - Find overlapping zones
  - `clear_all()` - Remove all zones
- Persistence:
  - `save_to_file(filepath)` - Save zones to JSON
  - `load_from_file(filepath)` - Load zones from JSON
  - Default location: `~/.config/snapzones/zones.json`

#### Preset Layouts
`create_preset_layout(preset_name, width, height)` supports:
- `halves` - Two vertical halves
- `thirds` - Three vertical thirds
- `quarters` - Four quadrants
- `grid3x3` - 3×3 grid with 9 zones

**Test Results:**
```bash
# Create and list preset
$ python src/snap_zones/zone.py --create-preset halves --list
# Generated 2 zones successfully

# Save/load with custom screen size
$ python src/snap_zones/zone.py --create-preset quarters \
    --screen-width 3440 --screen-height 1440 --save /tmp/test_zones.json
# Saved 4 zones to JSON

# Load and test point detection
$ python src/snap_zones/zone.py --load /tmp/test_zones.json --test-point 100 100
# Correctly identified "Top Left" zone

$ python src/snap_zones/zone.py --load /tmp/test_zones.json --test-point 2000 900
# Correctly identified "Bottom Right" zone
```

**JSON Format:**
```json
{
  "version": "1.0",
  "zones": [
    {
      "x": 0,
      "y": 0,
      "width": 1720,
      "height": 720,
      "name": "Top Left",
      "color": "#3498db"
    }
  ]
}
```

---

## Phase 1 Summary

**Status:** ✅ COMPLETE
**Date Completed:** 2025-10-07

All three blocks successfully implemented and tested:

1. **Window Detection** - Enumerate, query, and track windows
2. **Window Manipulation** - Move and resize windows programmatically
3. **Zone Management** - Define, persist, and query snap zones

**Command-Line Tools:**

```bash
# Window operations
python src/snap_zones/window_manager.py --list
python src/snap_zones/window_manager.py --active
python src/snap_zones/window_manager.py --move-active X Y WIDTH HEIGHT

# Zone operations
python src/snap_zones/zone.py --create-preset {halves|thirds|quarters|grid3x3}
python src/snap_zones/zone.py --save FILE
python src/snap_zones/zone.py --load FILE --list
python src/snap_zones/zone.py --load FILE --test-point X Y
```

**Next Phase:** Phase 2 - Input Monitoring System
- Block 2.1: Global Mouse Tracking
- Block 2.2: Modifier Key Detection
- Block 2.3: Global Hotkey System

---

## Phase 2: Input Monitoring System ✅ COMPLETE

**Status:** ✅ Complete
**Date Completed:** 2025-10-07

### Block 2.1: Global Mouse Tracking ✅

**Status:** Complete
**File:** `src/snap_zones/input_monitor.py`

**Implemented:**

#### `MouseTracker` Class
- Properties:
  - `position` - Current mouse position (x, y)
  - `is_left_pressed` - Left button state
  - `is_right_pressed` - Right button state
  - `is_middle_pressed` - Middle button state
  - `is_dragging` - Drag operation state
  - `drag_start_position` - Position where drag started

- Callbacks:
  - `set_on_position_change(callback)` - Mouse movement
  - `set_on_drag_start(callback)` - Drag operation begins
  - `set_on_drag_move(callback)` - During drag
  - `set_on_drag_end(callback)` - Drag operation ends
  - `set_on_button_press(callback)` - Button pressed
  - `set_on_button_release(callback)` - Button released

- Methods:
  - `start()` - Start monitoring
  - `stop()` - Stop monitoring
  - `is_running()` - Check if active
  - `wait()` - Block until stopped

**Test Results:**
```bash
$ python src/snap_zones/input_monitor.py --monitor --duration 3
# Successfully tracked mouse position in real-time

$ python src/snap_zones/input_monitor.py --track-drag --duration 5
# Detected drag operations with start/move/end events
# Calculated drag distance and offset correctly
```

**Key Features:**
- Uses `pynput.mouse` for global mouse monitoring
- Tracks drag operations with start position and offset
- Real-time position updates
- Button state tracking for left/right/middle buttons
- Non-blocking listener in separate thread

---

### Block 2.2: Modifier Key Detection ✅

**Status:** Complete
**File:** `src/snap_zones/input_monitor.py`

**Implemented:**

#### `KeyboardTracker` Class
- Properties:
  - `is_shift_pressed` - Shift key state
  - `is_ctrl_pressed` - Ctrl key state
  - `is_alt_pressed` - Alt key state
  - `is_super_pressed` - Super/Windows key state
  - `pressed_keys` - Set of all currently pressed keys

- Callbacks:
  - `set_on_key_press(callback)` - Any key pressed
  - `set_on_key_release(callback)` - Any key released
  - `set_on_modifier_change(callback)` - Modifier state changed

- Methods:
  - `start()` / `stop()` / `is_running()` / `wait()`

#### `InputMonitor` Class
Combined mouse + keyboard monitoring with modifier-aware drag detection:
- `set_on_modifier_drag_start(callback)` - Drag with modifiers (x, y, shift, ctrl, alt, super)
- `set_on_modifier_drag_move(callback)` - Drag movement with modifiers
- `set_on_modifier_drag_end(callback)` - Drag end with modifiers
- `start()` - Start both trackers
- `stop()` - Stop both trackers

**Test Results:**
```bash
$ python src/snap_zones/input_monitor.py --track-modifiers --duration 10
# Successfully detected Shift, Ctrl, Alt, and Super key presses
[MODIFIERS] CTRL
[MODIFIERS] SHIFT
[MODIFIERS] SUPER
[MODIFIERS] ALT

$ python src/snap_zones/input_monitor.py --track-shift-drag --duration 15
# Successfully detected drag operations with and without modifiers
[NO MODIFIERS+DRAG START] at (389, 1208)
[-] (388, 1208) ...
[NO MODIFIERS+DRAG END] at (130, 1335)

[SHIFT+DRAG START] at (132, 1302)
[S] (135, 1299) ...  # [S] indicates Shift held
[SHIFT+DRAG END] at (425, 1203)

[CTRL+DRAG START] ...
[C] ...  # [C] indicates Ctrl held

[ALT+DRAG START] ...
[A] ...  # [A] indicates Alt held
```

**Key Features:**
- Detects all standard modifier keys (Shift, Ctrl, Alt, Super)
- Tracks modifier state during drag operations
- Combined state machine for mouse+keyboard interaction
- Real-time modifier change callbacks
- Uses `pynput.keyboard` for global keyboard monitoring

---

### Block 2.3: Global Hotkey System ✅

**Status:** Complete
**File:** `src/snap_zones/input_monitor.py`

**Implemented:**

#### `Hotkey` Class
Represents a keyboard hotkey combination:
- `__init__(modifiers, key, callback, description)` - Create hotkey
- `matches(shift, ctrl, alt, super, key)` - Check if state matches
- Properties: `modifiers`, `key`, `callback`, `description`

#### `HotkeyManager` Class
Manages global hotkey registration and triggering:
- `register(modifiers, key, callback, description)` - Register new hotkey
- `unregister(hotkey)` - Remove hotkey
- `clear_all()` - Remove all hotkeys
- `get_hotkeys()` - List registered hotkeys
- `set_on_hotkey_triggered(callback)` - Global hotkey callback
- `enable()` / `disable()` - Toggle hotkey processing
- `start()` / `stop()` / `is_running()` / `wait()`

**Test Results:**
```bash
$ python src/snap_zones/input_monitor.py --test-hotkeys --duration 15
Testing global hotkey system...
Registered hotkeys:
--------------------------------------------------------------------------------
1. Hotkey[ALT+SUPER+Z] (Toggle zones overlay)
2. Hotkey[CTRL+SHIFT+A] (Show all windows)
3. Hotkey[ALT+F] (Focus mode)

Press the registered hotkeys for 15 seconds...

# When pressing Super+Alt+Z:
*** HOTKEY 1 TRIGGERED: Super+Alt+Z ***
[HOTKEY DETECTED] Hotkey[ALT+SUPER+Z] (Toggle zones overlay)
```

**Key Features:**
- Register multiple hotkeys with arbitrary modifier combinations
- Callback system for individual and global hotkey triggers
- Enable/disable hotkey processing at runtime
- Human-readable hotkey representation
- Exact modifier matching (must match exactly, not just include)
- First-match trigger policy for overlapping hotkeys

---

## Phase 2 Summary

**Status:** ✅ COMPLETE
**Date Completed:** 2025-10-07

All three blocks successfully implemented and tested:

1. **Mouse Tracking** - Real-time position, drag detection, button states
2. **Modifier Detection** - Shift/Ctrl/Alt/Super tracking, combined with drag
3. **Hotkey System** - Global hotkey registration and triggering

**Command-Line Tools:**

```bash
# Mouse operations
python src/snap_zones/input_monitor.py --monitor --duration 10
python src/snap_zones/input_monitor.py --track-drag --duration 10
python src/snap_zones/input_monitor.py --track-buttons --duration 10

# Keyboard operations
python src/snap_zones/input_monitor.py --track-modifiers --duration 10
python src/snap_zones/input_monitor.py --track-shift-drag --duration 15
python src/snap_zones/input_monitor.py --test-hotkeys --duration 15
```

**Next Phase:** Phase 3 - Overlay Rendering System
- Block 3.1: Transparent Overlay Window
- Block 3.2: Zone Visualization
- Block 3.3: Zone Hit Detection

---

## Phase 3: Overlay Rendering System

**Status:** ⏸️ Pending

---

## Phase 4: Core Snapping Logic

**Status:** ⏸️ Pending

---

## Phase 5: Zone Editor

**Status:** ⏸️ Pending

---

## Phase 6: Keyboard Navigation

**Status:** ⏸️ Pending

---

## Phase 7: Polish & System Integration

**Status:** ⏸️ Pending

---

## Development Notes

### Technical Decisions

1. **X11 Protocol Choice**
   - Using `python-xlib` for direct X11 access
   - Provides low-level control needed for window management
   - Compatible with most Linux desktop environments

2. **Zone Overlap Handling**
   - When multiple zones overlap at a point, return smallest zone (most specific)
   - Allows nested zone layouts for advanced configurations

3. **Window Manager Integration**
   - Using EWMH/NetWM hints (`_NET_*`) for maximum compatibility
   - Automatic unmaximize before moving windows
   - Respects window manager protocols

### Testing Approach

- Each block tested immediately after implementation
- Manual verification with real windows and zones
- Command-line interface for quick validation
- Test results documented in this log

### Configuration

- Default config directory: `~/.config/snapzones/`
- Zone files use JSON format for human readability
- Version field in JSON for future compatibility

---

## Version History

- **v0.1.0** (2025-10-07) - Phase 1 complete: Core Window Management
- **v0.2.0** (2025-10-07) - Phase 2 complete: Input Monitoring System
