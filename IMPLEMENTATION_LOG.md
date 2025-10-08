# SnapZones Implementation Log

Linux window management tool inspired by Windows PowerToys FancyZones.

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
- **Global layout library system** (v0.6.0)
  - Multiple named layouts stored globally
  - Workspace-to-layout mappings
  - Always-visible layout manager window
  - Auto-save on all zone modifications
  - Deep copy to prevent layout cross-contamination
- **Zone dimension display** (v0.6.1 - Phase 3.3)
  - Position (X: Y:) overlay in top-left corner
  - Size (W × H) overlay in bottom-right corner
  - CaptiX-inspired styling with semi-transparent backgrounds
  - Enabled by default, toggle with 'D' key
- Zone persistence in JSON format

---

## Current Implementation (v0.6.1)

### File Structure
```
src/snap_zones/
├── __init__.py
├── window_manager.py      # X11 window operations
├── zone.py                # Zone data structures, presets
├── input_monitor.py       # Mouse/keyboard tracking, hotkeys
├── overlay.py             # Transparent zone overlay
├── snapper.py             # Core snapping orchestration
├── zone_editor.py         # Fullscreen zone editor with layout manager
├── layout_library.py      # Global layout library management
└── layout_selector.py     # GTK layout selector dialog
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

# Layout selector dialog
python -m snap_zones.layout_selector --workspace WORKSPACE_ID
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
- `L`: Always-visible layout manager window (create/switch/delete layouts)
  - Auto-updates zone count on modifications
  - Single-click: Select layout
  - Double-click: Load layout
  - "Create New": Dialog prompts for name
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

## Pending Work

### Phase 6: Keyboard Navigation ⏸️
- Directional zone movement (Super+Arrows)

### Phase 7: Polish & System Integration ⏸️
- System tray indicator
- Settings dialog
- Autostart integration
- Deployment packaging

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
