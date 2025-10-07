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

## Phase 2: Input Monitoring System

**Status:** 🔄 Not Started

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
