# Snap Zones - Development Plan

## Overview

**Snap Zones** is a Linux implementation inspired by Windows PowerToys FancyZones. This document outlines the implementation plan for a Python/GTK standalone window management application with zone-based window snapping and keyboard shortcuts.

### Project Identity

- **Name**: Snap Zones
- **Inspiration**: Windows PowerToys FancyZones
- **Platform**: Linux (X11/Wayland)
- **Technology**: Python + GTK

## Input Handling Capabilities

The Python/GTK app will support:

1. **Global hotkeys**: Using `python-xlib` or `pynput` for system-wide key detection
2. **Mouse monitoring**: Track mouse position and button states globally
3. **Modifier keys**: Detect Shift/Ctrl/Alt states during drag operations
4. **Custom keybindings**: Register global shortcuts like Super+Arrow for zone navigation

---

## Phase 1: Core Window Management

**Goal**: Demonstrate basic window manipulation capabilities

### Block 1.1: Window Detection System

**Deliverables**:
- [ ] Script that lists all open windows with their titles and IDs
- [ ] Function to get active window information
- [ ] Function to get window under cursor

**Test**: Run `python window_manager.py --list` and see all windows printed

### Block 1.2: Window Manipulation

**Deliverables**:
- [ ] Move window to specific coordinates
- [ ] Resize window to specific dimensions
- [ ] Get current window geometry

**Test**: Run `python window_manager.py --move-active 100 100 800 600` and see window move/resize

### Block 1.3: Zone Data Structure

**Deliverables**:
- [ ] Zone class with overlap detection
- [ ] Save/load zones to JSON file
- [ ] Zone collection manager with CRUD operations

**Test**: Create zones programmatically, save to file, reload and verify

---

## Phase 2: Input Monitoring System

**Goal**: Detect and respond to user input events

### Block 2.1: Global Mouse Tracking

**Deliverables**:
- [ ] Continuously track mouse position
- [ ] Detect mouse button states
- [ ] Detect when dragging starts/ends

**Test**: Run monitor and see real-time mouse coordinates printed

### Block 2.2: Modifier Key Detection

**Deliverables**:
- [ ] Detect Shift key press during drag
- [ ] Detect other modifiers (Ctrl, Alt)
- [ ] Combined mouse+keyboard state machine

**Test**: Drag window with Shift and see "SHIFT+DRAG DETECTED" in console

### Block 2.3: Global Hotkey System

**Deliverables**:
- [ ] Register global hotkeys (e.g., Super+Alt+Z)
- [ ] Hotkey configuration system
- [ ] Callback system for hotkey actions

**Test**: Press configured hotkey and see action triggered (e.g., print message)

---

## Phase 3: Overlay Rendering System

**Goal**: Display transparent overlay with zones

### Block 3.1: Transparent Overlay Window

**Deliverables**:
- [ ] Full-screen transparent GTK window
- [ ] Click-through when not active
- [ ] Show/hide on demand

**Test**: Run `python overlay.py --show` and see transparent overlay appear

### Block 3.2: Zone Visualization

**Deliverables**:
- [ ] Draw zones with semi-transparent colors
- [ ] Highlight zone under cursor
- [ ] Different highlight for selected zone

**Test**: Show overlay with sample zones, move mouse and see highlighting change

### Block 3.3: Zone Hit Detection

**Deliverables**:
- [ ] Detect which zone(s) contain cursor
- [ ] Handle overlapping zones (topmost priority)
- [ ] Return best match for window placement

**Test**: Move cursor over overlapping zones, verify correct zone selection

---

## Phase 4: Core Snapping Logic

**Goal**: Actually snap windows to zones

### Block 4.1: Basic Snap-to-Zone

**Deliverables**:
- [ ] Snap active window to zone under cursor
- [ ] Smooth animation (optional)
- [ ] Restore original position on cancel

**Test**: Shift+drag window over zone, release, verify window snaps correctly

### Block 4.2: Workspace Support

**Deliverables**:
- [ ] Detect current workspace
- [ ] Load workspace-specific zones
- [ ] Default zones for new workspaces

**Test**: Switch workspaces, verify different zone layouts load

### Block 4.3: Integration Test

**Deliverables**:
- [ ] Complete drag-to-snap workflow
- [ ] Shift+drag → overlay → highlight → release → snap
- [ ] Cancel with Escape

**Test**: Full end-to-end window snapping with overlay

---

## Phase 5: Zone Editor

**Goal**: GUI for creating and editing zones

### Block 5.1: Basic Canvas Editor

**Deliverables**:
- [ ] GTK window with drawing canvas
- [ ] Draw rectangles with mouse
- [ ] Display existing zones

**Test**: Open editor, draw new zone, see it appear on canvas

### Block 5.2: Zone Manipulation

**Deliverables**:
- [ ] Select zones by clicking
- [ ] Resize zones via handles
- [ ] Move zones by dragging
- [ ] Delete selected zone

**Test**: Load existing zones, modify each one, verify changes

### Block 5.3: Preset System

**Deliverables**:
- [ ] Built-in layout templates
- [ ] Apply preset to current workspace
- [ ] Save current layout as preset

**Test**: Apply "Thirds" preset, verify zones created correctly

---

## Phase 6: Keyboard Navigation

**Goal**: Navigate zones without mouse

### Block 6.1: Arrow Key Navigation

**Deliverables**:
- [ ] Move window to adjacent zone with arrows
- [ ] Smart direction detection
- [ ] Wrap-around option

**Test**: Press Super+Arrow keys, verify window moves between zones

### Block 6.2: Zone Cycling

**Deliverables**:
- [ ] Cycle through all zones with Tab
- [ ] Cycle through overlapping zones
- [ ] Visual indication of target zone

**Test**: Press Super+Tab repeatedly, see window move through all zones

---

## Phase 7: Polish & System Integration

**Goal**: Production-ready application

### Block 7.1: Edge Snapping

**Deliverables**:
- [ ] Detect window proximity to edges
- [ ] Magnetic snap to edges
- [ ] Window-to-window snapping

**Test**: Drag window near edge/another window, see it snap when close

### Block 7.2: System Integration

**Deliverables**:
- [ ] System tray indicator
- [ ] Autostart .desktop file
- [ ] Enable/disable toggle
- [ ] Settings GUI

**Test**: See icon in system tray, verify autostart works after reboot

### Block 7.3: Configuration Management

**Deliverables**:
- [ ] Settings file with all options
- [ ] GUI for configuration
- [ ] Import/export zone layouts

**Test**: Change settings in GUI, restart app, verify settings persist

---

## Testing Verification Checklist

Each phase should pass these gates before moving on:

1. **Unit Test**: Individual functions work as documented
2. **Integration Test**: Components work together
3. **User Test**: Manual testing of the deliverable
4. **Performance Test**: No noticeable lag or CPU usage
5. **Persistence Test**: Settings/zones survive restart

---

## Quick Validation Commands

```bash
# Phase 1 validation
./test_window_ops.py

# Phase 2 validation  
./test_input_monitor.py

# Phase 3 validation
./test_overlay.py

# Phase 4 validation
./test_snapping.py

# Full integration test
./run_tests.py --all
```

---

## Notes

This structure ensures each phase produces something tangible and testable. Each deliverable is independently verifiable and builds upon the previous phase's foundation.