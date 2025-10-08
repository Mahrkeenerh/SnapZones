# SnapZones Implementation Log

Linux window management tool inspired by Windows PowerToys FancyZones.

---

## Recent Changes

### 2025-10-08: Complete Workspace-Layout Auto-Mapping System

**Summary**: Implemented automatic workspace-to-layout mapping with live reload support, plus non-interactive installation scripts.

#### 1. Auto-mapping When Switching Layouts
- **Feature**: When switching layouts in the editor (via double-click or creating new layout), the current workspace is automatically mapped to that layout
- **Implementation**:
  - Added X11 display connection to `ZoneEditorOverlay.__init__()` for workspace detection
  - Added `get_current_workspace()` method to query X11's `_NET_CURRENT_DESKTOP` property
  - Updated `on_row_activated()` handler to call `layout_library.set_active_layout()` on double-click
  - Updated `_on_create_layout()` to auto-map new layouts to current workspace
  - Updates `workspace_layouts.json` automatically
- **Files Modified**: `src/snap_zones/zone_editor.py`

#### 2. Daemon Live Reload of Workspace Mappings
- **Feature**: Daemon now picks up workspace mapping changes immediately without restart
- **Implementation**:
  - Modified `LayoutLibrary.get_active_layout()` to call `self._load_workspace_mappings()` on every request
  - This reloads the mappings from disk, ensuring changes made by the editor are immediately available
- **Files Modified**: `src/snap_zones/layout_library.py`
- **User Impact**: Changes to workspace mappings take effect immediately when Alt+Dragging windows

#### 3. Editor Auto-Loads Workspace Layout
- **Feature**: Zone editor now starts with the layout assigned to the current workspace instead of always using "default"
- **Implementation**:
  - Modified `_load_current_layout()` to auto-detect workspace and load assigned layout
  - Falls back to "default" if no mapping exists
- **Files Modified**: `src/snap_zones/zone_editor.py`

#### 4. Non-Interactive Install/Uninstall Scripts
- **Feature**: Added `-y`/`--yes` flags to avoid hanging when running scripts in automated contexts
- **Implementation**:
  - Added `NON_INTERACTIVE` flag parsing to both scripts
  - Modified all `read -p` prompts to check flag and skip in non-interactive mode
  - Allows running `./uninstall.sh -y && ./install.sh -y` without hanging
- **Files Modified**: `install.sh`, `uninstall.sh`
- **User Impact**: Scripts can now be run in automated/scripted environments

#### Overall User Impact
Users no longer need to:
- Manually edit `workspace_layouts.json` to map workspaces to layouts
- Restart the daemon after changing workspace mappings
- Manually select the correct layout when opening the editor on different workspaces

The system now provides a seamless workflow where layouts automatically follow workspaces.

---

## Project Status Summary

### Completed Phases ✅

**Phase 1-5**: Core functionality complete
- **Window Management** (Phase 1): X11-based window detection, manipulation, zone data structures
- **Input Monitoring** (Phase 2): Global mouse/keyboard tracking, modifier detection, hotkey system
- **Overlay System** (Phase 3): Transparent fullscreen overlay, zone visualization, hit detection
- **Snapping Logic** (Phase 4): Modifier+drag workflow, workspace support, snap-to-zone
- **Zone Editor** (Phase 5): WYSIWYG fullscreen editor, in-place zone creation/editing, preset layouts

### Technology Stack
- **Platform**: Linux X11
- **Language**: Python 3.10+
- **GUI**: GTK3 + Cairo
- **Input**: python-xlib, pynput
- **Config**: JSON files in `~/.config/snapzones/`

### Key Features Implemented
- Fullscreen transparent overlay for zone editing and snapping
- Modifier key + drag to trigger zone overlay
- Click or release over zone to snap window
- Preset layouts (halves, thirds, quarters, 3x3 grid)
- WYSIWYG zone editor with drag, resize, delete operations
- 8-handle resize system (corners + edges)
- **Global layout library system** (v0.6.0+)
  - Multiple named layouts stored globally
  - Workspace-to-layout mappings
  - Center-positioned layout manager window (integrated into zone editor)
  - Layout rename with three methods: button, slow-click, F2 key (v0.6.2)
  - Auto-save on all zone modifications
  - Deep copy to prevent layout cross-contamination
- **Zone dimension display** (v0.6.1 - Phase 3.3)
  - Position (X: Y:) overlay in top-left corner
  - Size (W × H) overlay in bottom-right corner
  - CaptiX-inspired styling with semi-transparent backgrounds
  - Enabled by default, toggle with 'D' key
- Zone persistence in JSON format

---

## Current Implementation (v0.7.0 - Deployment Ready)

### File Structure
```
src/snap_zones/
├── __init__.py
├── window_manager.py      # X11 window operations
├── zone.py                # Zone data structures, presets
├── input_monitor.py       # Mouse/keyboard tracking
├── overlay.py             # Transparent zone overlay
├── snapper.py             # Core snapping orchestration
├── zone_editor.py         # Fullscreen zone editor with integrated layout manager
├── layout_library.py      # Global layout library management
└── daemon.py              # Background service (Alt+drag monitoring)

bin/
├── snapzones              # Daemon launcher
├── snapzones-editor       # Zone editor launcher
└── snapzones-status       # Daemon management utility

install.sh                 # Installation script
uninstall.sh              # Uninstallation script
snapzones.desktop         # Autostart configuration
```

### Configuration Files
- `~/.config/snapzones/layouts/*.json` - Named layout files
- `~/.config/snapzones/workspace_layouts.json` - Workspace-to-layout mappings
- Auto-loads workspace-assigned layouts, falls back to "default"

### CLI Commands
```bash
# Window management
python -m snap_zones.window_manager --list
python -m snap_zones.window_manager --move-active X Y W H

# Zone creation
python -m snap_zones.zone --create-preset quarters --save FILE

# Input monitoring
python -m snap_zones.input_monitor --track-shift-drag
python -m snap_zones.input_monitor --test-hotkeys

# Overlay testing
python -m snap_zones.overlay --show --preset grid3x3

# Interactive snapping
python -m snap_zones.snapper --interactive --modifier alt

# Zone editor
python -m snap_zones.zone_editor

# Layout management
python -m snap_zones.layout_library --list
python -m snap_zones.layout_library --show LAYOUT_NAME
python -m snap_zones.layout_library --create LAYOUT_NAME
python -m snap_zones.layout_library --delete LAYOUT_NAME
python -m snap_zones.layout_library --set-workspace WORKSPACE_ID LAYOUT_NAME
python -m snap_zones.layout_library --list-workspaces
```

### Keyboard Controls

**Zone Editor**:
- Click & Drag: Draw new zone (auto-saves)
- Click zone: Select zone
- Drag selected: Move zone (auto-saves)
- Drag handles: Resize zone (auto-saves)
- `ESC`: Exit editor
- `H`: Toggle help
- `D`: Toggle dimension display (position + size overlays)
- `S`: Save zones (manual save)
- **Layout Manager** (center-positioned window, always visible)
  - Auto-updates zone count on modifications
  - Single-click: Select layout
  - Double-click: Load layout
  - Slow-click (click selected item again): Rename layout
  - `F2`: Rename selected layout
  - "Create New": Create new layout with name dialog
  - "Rename": Rename selected layout with dialog
  - "Delete": Delete selected layout with confirmation
  - "Close Editor": Exit entire editor
- `N`: Clear all zones (auto-saves)
- `Delete`: Delete selected zone (auto-saves)
- `1-4`: Apply presets (halves/thirds/quarters/grid) (auto-saves)

**Snapping** (runtime):
- `Modifier + Drag Window`: Show overlay
- Release over zone: Snap window
- `ESC`: Cancel

---

## Deployment Complete (v0.7.0) ✅

### Phase 6: Basic Deployment (COMPLETED)
- ✅ Background daemon with PID locking
- ✅ Native GNOME keyboard shortcut (Super+Shift+Tab via gsettings)
- ✅ Installation script with dependency checking
- ✅ Uninstallation script
- ✅ Autostart integration
- ✅ Status management utility

### Known Issues & Future Enhancements

**Pending Features**:
- ⏸️ Keyboard navigation (Super+Arrow keys to move windows between zones)
- ⏸️ System tray indicator
- ⏸️ Settings dialog
- ⏸️ Multi-zone proximity snapping
- ⏸️ Magnetic edge snapping in editor

---

## Next Development Phase

**Goal**: Implement keyboard navigation for zone switching

See `IMPLEMENTATION_PLAN_V2.md` for detailed plan.

**Remaining Features**:
- Simple arrow-key navigation (position-based ordering)
- Super+Arrow keys to move windows between zones

---

## Version History

- **v0.1.0** (2025-10-07) - Phase 1: Core Window Management
- **v0.2.0** (2025-10-07) - Phase 2: Input Monitoring System
- **v0.3.0** (2025-10-07) - Phase 3: Overlay Rendering System
- **v0.4.0** (2025-10-07) - Phase 4: Core Snapping Logic
- **v0.5.0** (2025-10-07) - Phase 5: Zone Editor
- **v0.6.0** (2025-10-07) - Phase 6: Layout Library System
  - Global layout library with named layouts
  - Workspace-to-layout mapping system
  - Visual layout manager in zone editor
  - Layout selector dialog for workspace assignment
  - Auto-save functionality
  - Deep copy fix for layout isolation
- **v0.6.2** (2025-10-08) - Layout Rename & UI Improvements
  - Added layout rename functionality to layout manager
  - Three rename methods: Rename button, slow-click, and F2 key
  - Removed duplicate layout selector dialog (consolidated into zone editor)
  - Repositioned layout manager window from top-right to center
  - Layout rename updates all workspace mappings automatically
- **v0.7.0** (2025-10-08) - Deployment & Native Integration
  - Background daemon service with PID locking
  - Native GNOME keyboard shortcut integration (gsettings)
  - Removed HotkeyManager (conflicted with system shortcuts)
  - Installation/uninstallation scripts
  - Autostart configuration
  - Status management utility (snapzones-status)
  - Full documentation and README update
  - Fixed import bug (List type in snapper.py)
  - Fixed workspace-layout mapping bug
