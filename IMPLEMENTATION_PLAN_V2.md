# SnapZones Layout Management System - Implementation Plan V2

## Architecture Overview

**Global Layout Library**: Named layouts stored centrally (e.g., "Coding", "Video Editing", "Browsing")
**Workspace-Layout Mapping**: Each workspace references one active layout from the library
**File Structure**:
- `~/.config/snapzones/layouts/<name>.json` - Individual named layouts
- `~/.config/snapzones/workspace_layouts.json` - Maps workspace IDs to layout names

---

## Phase 1: Layout Library System (FUNCTIONAL - PRIORITY)

### 1.1 Layout Storage Refactoring
- Create `LayoutLibrary` class to manage named layouts
- Extend Zone JSON format to include layout metadata (name, description, created_date)
- Implement CRUD operations: create, read, update, delete, list layouts
- Migration: Convert existing workspace zones to named layouts

### 1.2 Layout Selection System
- Create workspace-to-layout mapping configuration
- Implement `get_active_layout(workspace_id)` → returns layout name
- Implement `set_active_layout(workspace_id, layout_name)` → assigns layout to workspace
- Fallback to "default" layout if no mapping exists

### 1.3 Hotkey-Triggered Layout Selector UI
- Create GTK dialog window listing all available layouts
- Show current active layout for current workspace (highlighted/marked)
- Allow selection via mouse click or arrow keys + Enter
- Save selection to workspace mapping on confirm
- Integrate with HotkeyManager (e.g., Super+Alt+L to trigger)

### 1.4 Zone Editor Layout Management
- Add layout selector dropdown/menu in zone editor
- Allow switching between layouts for editing
- When saving: save to currently selected layout
- Add "New Layout" button (prompts for name)
- Add "Delete Layout" button (with confirmation)
- Show current layout name in status bar

---

## Phase 2: Keyboard Navigation (FUNCTIONAL - PRIORITY)

### 2.1 Directional Zone Movement
**Goal**: Move active window between zones using keyboard arrows

**Implementation**:
- Register hotkeys: Super+Arrow keys (or configurable modifier+arrows)
- Two zone orderings for different navigation axes:
  - **Horizontal (Left/Right)**: Sort zones by (x, then y)
  - **Vertical (Up/Down)**: Sort zones by (y, then x)
- Arrow key logic (all cycle with wrapping):
  - **Right**: Next zone in horizontal order
  - **Left**: Previous zone in horizontal order
  - **Down**: Next zone in vertical order
  - **Up**: Previous zone in vertical order
- Snap window immediately to selected zone (no preview/highlight)
- Simple, predictable cycling behavior

**No Features**:
- ❌ Visual preview/highlight before snap
- ❌ Smart spatial analysis
- ❌ Separate Tab cycling mode
- ✅ Simple position-based ordering with arrow keys

---

## Phase 3: Enhanced Snapping Features (NICE-TO-HAVE)

### 3.1 Multi-Zone Proximity Snapping
- When cursor near boundary of 2+ zones, detect proximity
- Calculate union/OR of overlapping zones
- Snap window to combined area (useful for "between zones" positioning)
- Configurable proximity threshold (default: 50px from zone edge)

### 3.2 Magnetic Edge Snapping in Editor
- Add "Magnetic Snap" toggle button/checkbox in zone editor
- When enabled: zone edges snap to other zone edges during resize/move
- When disabled (e.g., Shift pressed): free-form positioning
- Visual guides showing snap alignment lines

### 3.3 Zone Dimension Display in Editor
- Overlay zone size in pixels on each zone (width × height)
- Show top-left corner coordinates (x, y) in pixels
- Toggle on/off with keyboard shortcut (e.g., 'D' for dimensions)
- Semi-transparent background for readability

---

## Phase 4: System Integration (POLISH - LATER)

### 4.1 System Tray Indicator
- Add AppIndicator3 system tray icon
- Menu options:
  - "Open Zone Editor"
  - "Select Layout for Current Workspace" (opens layout selector)
  - "Enable/Disable Snapping"
  - "Settings"
  - "Quit"

### 4.2 Settings Dialog
- GTK settings window with tabs:
  - **Keyboard Shortcuts**: Configure all hotkeys
  - **Modifier Key**: Choose trigger modifier (Alt/Super/Ctrl/Shift)
  - **Behavior**: Proximity threshold, animation settings
  - **Autostart**: Enable/disable autostart on login
- Save settings to `~/.config/snapzones/config.json`

### 4.3 Autostart Integration
- Create `.desktop` file for XDG autostart
- Install to `~/.config/autostart/snapzones.desktop`
- Toggle via settings dialog

---

## Phase 5: Deployment (FINAL POLISH)

### 5.1 Packaging
- Create `setup.py` for pip installation
- Package desktop files and icons
- Create installation script

### 5.2 Documentation
- User guide with screenshots
- Keyboard shortcut reference
- Layout creation tutorial
- Troubleshooting guide

---

## Implementation Order (Focus on Functional First)

**Sprint 1** (Functional Core - Layout System):
1. Phase 1.1: Layout library backend (LayoutLibrary class)
2. Phase 1.2: Workspace-to-layout mapping system
3. Phase 1.3: Hotkey-triggered layout selector dialog
4. Phase 1.4: Zone editor layout management UI
5. Update snapper.py to use LayoutLibrary

**Sprint 2** (Functional Core - Keyboard Navigation):
6. Phase 2.1: Directional zone movement with arrow keys (simple position-based)

**Sprint 3** (Nice-to-Have Features):
7. Phase 3.1: Multi-zone proximity snapping
8. Phase 3.2: Magnetic editing
9. Phase 3.3: Dimension display in editor

**Sprint 4** (Polish):
10. Phase 4: System tray, settings, autostart
11. Phase 5: Packaging and deployment

---

## File Changes Summary

**New Files**:
- `src/snap_zones/layout_library.py` - Layout management system
- `src/snap_zones/layout_selector.py` - GTK layout selection dialog
- `src/snap_zones/settings.py` - Settings management and dialog
- `src/snap_zones/tray_indicator.py` - System tray integration

**Modified Files**:
- `src/snap_zones/zone.py` - Add layout metadata to Zone/ZoneManager
- `src/snap_zones/snapper.py` - Use LayoutLibrary, add keyboard navigation
- `src/snap_zones/zone_editor.py` - Add layout selector UI, magnetic snapping, dimension display
- `src/snap_zones/input_monitor.py` - Register navigation hotkeys

**New Config Files**:
- `~/.config/snapzones/layouts/*.json` - Individual layout files
- `~/.config/snapzones/workspace_layouts.json` - Workspace-layout mapping
- `~/.config/snapzones/config.json` - Application settings

---

## Keyboard Navigation Detail

### Zone Ordering Algorithm
```python
# Sort zones by top-left corner
# For horizontal navigation (LEFT/RIGHT): sort by (x, then y)
horizontal_zones = sorted(zones, key=lambda z: (z.x, z.y))

# For vertical navigation (UP/DOWN): sort by (y, then x)
vertical_zones = sorted(zones, key=lambda z: (z.y, z.x))

# Arrow key actions (all cycle with wrapping):
# RIGHT: current_index = (current_index + 1) % len(horizontal_zones)
# LEFT:  current_index = (current_index - 1) % len(horizontal_zones)
# DOWN:  current_index = (current_index + 1) % len(vertical_zones)
# UP:    current_index = (current_index - 1) % len(vertical_zones)
```

### No Visual Feedback
- Window snaps immediately to target zone
- No preview overlay
- No brief highlights
- Simple and fast behavior
