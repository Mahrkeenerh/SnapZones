#!/usr/bin/env python3
"""
Zone Editor - Fullscreen overlay GUI for creating and editing zone layouts

Provides a transparent fullscreen overlay for:
- Drawing new zones with mouse (see exactly where they'll be on screen)
- Displaying existing zones over actual desktop
- Selecting, moving, and resizing zones in-place
- Applying preset layouts
- Saving/loading zone configurations

Controls:
- Click and drag: Draw new zone
- Click on zone: Select zone
- Drag selected zone: Move it
- Drag resize handles: Resize zone
- Delete key: Delete selected zone
- Escape: Exit editor
- S: Save zones
- L: Load zones
- N: New (clear all)
- 1-4: Apply presets (1=halves, 2=thirds, 3=quarters, 4=grid3x3)
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo
import json
import os
from typing import List, Optional, Tuple
from .zone import Zone, ZoneManager


class ZoneEditorOverlay(Gtk.Window):
    """Fullscreen transparent overlay for zone editing"""

    # Visual constants
    ZONE_FILL_COLOR = (0.3, 0.5, 0.8, 0.3)  # Blue with transparency
    ZONE_BORDER_COLOR = (0.2, 0.4, 0.7, 0.8)
    SELECTED_FILL_COLOR = (0.8, 0.5, 0.3, 0.4)  # Orange with transparency
    SELECTED_BORDER_COLOR = (0.7, 0.4, 0.2, 1.0)
    HANDLE_SIZE = 10
    HANDLE_COLOR = (1.0, 1.0, 1.0, 0.9)
    HANDLE_BORDER_COLOR = (0.0, 0.0, 0.0, 1.0)

    # Help text
    HELP_BG_COLOR = (0.1, 0.1, 0.1, 0.85)
    HELP_TEXT_COLOR = (1.0, 1.0, 1.0, 1.0)

    def __init__(self):
        super().__init__()

        self.zone_manager = ZoneManager()
        self.current_file: Optional[str] = None

        self.zones: List[Zone] = []
        self.selected_zone: Optional[Zone] = None

        # Drawing state
        self.is_drawing = False
        self.draw_start: Optional[Tuple[int, int]] = None
        self.draw_current: Optional[Tuple[int, int]] = None

        # Moving/resizing state
        self.is_moving = False
        self.is_resizing = False
        self.resize_handle: Optional[str] = None  # 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        self.move_start: Optional[Tuple[int, int]] = None
        self.zone_original_rect: Optional[Tuple[int, int, int, int]] = None

        # Status message
        self.status_message = "Zone Editor - Draw zones, ESC to exit, H for help"
        self.show_help = False

        # Setup window
        self._setup_window()
        self._setup_events()

        # Auto-load default zones if they exist
        self._auto_load_zones()

    def _setup_window(self):
        """Setup fullscreen transparent window"""
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.set_app_paintable(True)
        self.set_decorated(False)
        self.fullscreen()

        # Stay on top but allow click-through when not interacting
        self.set_keep_above(True)
        self.set_accept_focus(True)

    def _setup_events(self):
        """Setup event handlers"""
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )

    def _auto_load_zones(self):
        """Auto-load zones from default location if available"""
        default_file = os.path.expanduser("~/.config/snapzones/zones.json")
        if os.path.exists(default_file):
            try:
                self.zones = self.zone_manager.load_zones(default_file)
                self.current_file = default_file
                self.status_message = f"Loaded {len(self.zones)} zones from zones.json"
            except Exception as e:
                self.status_message = f"Failed to load default zones: {e}"

    def on_draw(self, widget, cr: cairo.Context):
        """Draw zones, handles, and UI"""
        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        alloc = self.get_allocation()
        width, height = alloc.width, alloc.height

        # Draw zones
        for zone in self.zones:
            is_selected = (zone == self.selected_zone)
            self._draw_zone(cr, zone, is_selected, width, height)

        # Draw temporary zone being created
        if self.is_drawing and self.draw_start and self.draw_current:
            x1, y1 = self.draw_start
            x2, y2 = self.draw_current
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)

            cr.set_source_rgba(*self.ZONE_FILL_COLOR)
            cr.rectangle(x, y, w, h)
            cr.fill_preserve()
            cr.set_source_rgba(*self.ZONE_BORDER_COLOR)
            cr.set_line_width(2)
            cr.stroke()

        # Draw help panel or status bar
        if self.show_help:
            self._draw_help(cr, width, height)
        else:
            self._draw_status_bar(cr, width, height)

        return False

    def _draw_zone(self, cr: cairo.Context, zone: Zone, is_selected: bool,
                   canvas_width: int, canvas_height: int):
        """Draw a single zone with optional selection handles"""
        # Convert relative coordinates to absolute
        x = int(zone.x * canvas_width)
        y = int(zone.y * canvas_height)
        w = int(zone.width * canvas_width)
        h = int(zone.height * canvas_height)

        # Fill
        if is_selected:
            cr.set_source_rgba(*self.SELECTED_FILL_COLOR)
        else:
            cr.set_source_rgba(*self.ZONE_FILL_COLOR)
        cr.rectangle(x, y, w, h)
        cr.fill()

        # Border
        if is_selected:
            cr.set_source_rgba(*self.SELECTED_BORDER_COLOR)
            cr.set_line_width(3)
        else:
            cr.set_source_rgba(*self.ZONE_BORDER_COLOR)
            cr.set_line_width(2)
        cr.rectangle(x, y, w, h)
        cr.stroke()

        # Label
        if zone.name:
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(16)

            text_extents = cr.text_extents(zone.name)
            text_x = x + (w - text_extents.width) / 2
            text_y = y + (h + text_extents.height) / 2

            cr.move_to(text_x, text_y)
            cr.show_text(zone.name)

        # Draw resize handles if selected
        if is_selected:
            self._draw_handles(cr, x, y, w, h)

    def _draw_handles(self, cr: cairo.Context, x: int, y: int, w: int, h: int):
        """Draw resize handles at corners and edges"""
        handles = [
            (x, y),                    # nw
            (x + w, y),                # ne
            (x, y + h),                # sw
            (x + w, y + h),            # se
            (x + w//2, y),             # n
            (x + w//2, y + h),         # s
            (x, y + h//2),             # w
            (x + w, y + h//2),         # e
        ]

        for hx, hy in handles:
            # White fill
            cr.set_source_rgba(*self.HANDLE_COLOR)
            cr.rectangle(
                hx - self.HANDLE_SIZE // 2,
                hy - self.HANDLE_SIZE // 2,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE
            )
            cr.fill()

            # Black border
            cr.set_source_rgba(*self.HANDLE_BORDER_COLOR)
            cr.set_line_width(2)
            cr.rectangle(
                hx - self.HANDLE_SIZE // 2,
                hy - self.HANDLE_SIZE // 2,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE
            )
            cr.stroke()

    def _draw_status_bar(self, cr: cairo.Context, width: int, height: int):
        """Draw status bar at bottom of screen"""
        bar_height = 40

        # Semi-transparent background
        cr.set_source_rgba(*self.HELP_BG_COLOR)
        cr.rectangle(0, height - bar_height, width, bar_height)
        cr.fill()

        # Status text
        cr.set_source_rgba(*self.HELP_TEXT_COLOR)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)
        cr.move_to(20, height - bar_height + 25)
        cr.show_text(self.status_message)

    def _draw_help(self, cr: cairo.Context, width: int, height: int):
        """Draw help panel"""
        panel_width = 500
        panel_height = 400
        panel_x = (width - panel_width) // 2
        panel_y = (height - panel_height) // 2

        # Background
        cr.set_source_rgba(*self.HELP_BG_COLOR)
        cr.rectangle(panel_x, panel_y, panel_width, panel_height)
        cr.fill()

        # Border
        cr.set_source_rgba(1, 1, 1, 0.5)
        cr.set_line_width(2)
        cr.rectangle(panel_x, panel_y, panel_width, panel_height)
        cr.stroke()

        # Help text
        cr.set_source_rgba(*self.HELP_TEXT_COLOR)
        cr.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)

        help_lines = [
            "ZONE EDITOR - HELP",
            "",
            "Drawing & Editing:",
            "  Click & Drag       - Draw new zone",
            "  Click on zone      - Select zone",
            "  Drag selected      - Move zone",
            "  Drag handles       - Resize zone",
            "",
            "Keyboard Shortcuts:",
            "  ESC     - Exit editor",
            "  H       - Toggle this help",
            "  S       - Save zones",
            "  L       - Load zones",
            "  N       - New (clear all)",
            "  Delete  - Delete selected zone",
            "",
            "Presets:",
            "  1  - Halves     2  - Thirds",
            "  3  - Quarters   4  - Grid 3x3",
            "",
            "Press H to close help"
        ]

        y_offset = panel_y + 30
        for line in help_lines:
            cr.move_to(panel_x + 20, y_offset)
            cr.show_text(line)
            y_offset += 18

    def on_button_press(self, widget, event):
        """Handle mouse button press"""
        if event.button != 1:  # Only left click
            return False

        x, y = int(event.x), int(event.y)
        alloc = self.get_allocation()

        # Check if clicking on selected zone's handles
        if self.selected_zone:
            handle = self._get_handle_at_position(x, y, alloc.width, alloc.height)
            if handle:
                self.is_resizing = True
                self.resize_handle = handle
                self.move_start = (x, y)
                self.zone_original_rect = (
                    self.selected_zone.x,
                    self.selected_zone.y,
                    self.selected_zone.width,
                    self.selected_zone.height
                )
                return True

        # Check if clicking on a zone
        clicked_zone = self._get_zone_at_position(x, y, alloc.width, alloc.height)
        if clicked_zone:
            self.selected_zone = clicked_zone
            self.is_moving = True
            self.move_start = (x, y)
            self.zone_original_rect = (
                clicked_zone.x,
                clicked_zone.y,
                clicked_zone.width,
                clicked_zone.height
            )
            self.status_message = f"Selected: {clicked_zone.name}"
            self.queue_draw()
            return True

        # Start drawing new zone
        self.selected_zone = None
        self.is_drawing = True
        self.draw_start = (x, y)
        self.draw_current = (x, y)
        self.status_message = "Drawing new zone..."
        self.queue_draw()
        return True

    def on_button_release(self, widget, event):
        """Handle mouse button release"""
        if event.button != 1:
            return False

        alloc = self.get_allocation()

        # Finish drawing new zone
        if self.is_drawing and self.draw_start and self.draw_current:
            x1, y1 = self.draw_start
            x2, y2 = self.draw_current

            # Create zone if it has reasonable size
            if abs(x2 - x1) > 30 and abs(y2 - y1) > 30:
                # Convert to relative coordinates
                rel_x1 = min(x1, x2) / alloc.width
                rel_y1 = min(y1, y2) / alloc.height
                rel_x2 = max(x1, x2) / alloc.width
                rel_y2 = max(y1, y2) / alloc.height

                new_zone = Zone(
                    rel_x1, rel_y1,
                    rel_x2 - rel_x1,
                    rel_y2 - rel_y1,
                    name=f"Zone {len(self.zones) + 1}"
                )
                self.zones.append(new_zone)
                self.selected_zone = new_zone
                self.status_message = f"Created {new_zone.name}"

            self.is_drawing = False
            self.draw_start = None
            self.draw_current = None
            self.queue_draw()
            return True

        # Finish moving
        if self.is_moving:
            self.is_moving = False
            self.move_start = None
            self.zone_original_rect = None
            self.status_message = f"Moved {self.selected_zone.name if self.selected_zone else 'zone'}"
            return True

        # Finish resizing
        if self.is_resizing:
            self.is_resizing = False
            self.resize_handle = None
            self.move_start = None
            self.zone_original_rect = None
            self.status_message = f"Resized {self.selected_zone.name if self.selected_zone else 'zone'}"
            return True

        return False

    def on_motion(self, widget, event):
        """Handle mouse motion"""
        x, y = int(event.x), int(event.y)
        alloc = self.get_allocation()

        # Update drawing
        if self.is_drawing:
            self.draw_current = (x, y)
            self.queue_draw()
            return True

        # Update moving
        if self.is_moving and self.move_start and self.zone_original_rect:
            dx = (x - self.move_start[0]) / alloc.width
            dy = (y - self.move_start[1]) / alloc.height

            orig_x, orig_y, orig_w, orig_h = self.zone_original_rect
            new_x = max(0, min(1 - orig_w, orig_x + dx))
            new_y = max(0, min(1 - orig_h, orig_y + dy))

            self.selected_zone.x = new_x
            self.selected_zone.y = new_y
            self.queue_draw()
            return True

        # Update resizing
        if self.is_resizing and self.move_start and self.zone_original_rect:
            self._handle_resize(x, y, alloc.width, alloc.height)
            self.queue_draw()
            return True

        return False

    def on_key_press(self, widget, event):
        """Handle keyboard shortcuts"""
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)

        # ESC - Exit
        if keyname == 'Escape':
            Gtk.main_quit()
            return True

        # H - Toggle help
        if keyname in ('h', 'H'):
            self.show_help = not self.show_help
            self.queue_draw()
            return True

        # S - Save
        if keyname in ('s', 'S'):
            self._save_zones()
            return True

        # L - Load
        if keyname in ('l', 'L'):
            self._load_zones()
            return True

        # N - New (clear all)
        if keyname in ('n', 'N'):
            self.zones.clear()
            self.selected_zone = None
            self.current_file = None
            self.status_message = "Cleared all zones"
            self.queue_draw()
            return True

        # Delete - Remove selected zone
        if keyname == 'Delete' and self.selected_zone:
            zone_name = self.selected_zone.name
            self.zones.remove(self.selected_zone)
            self.selected_zone = None
            self.status_message = f"Deleted {zone_name}"
            self.queue_draw()
            return True

        # Number keys - Apply presets
        presets = {
            '1': 'halves',
            '2': 'thirds',
            '3': 'quarters',
            '4': 'grid3x3'
        }
        if keyname in presets:
            preset_name = presets[keyname]
            self.zones = self.zone_manager.create_preset(preset_name)
            self.selected_zone = None
            self.status_message = f"Applied preset: {preset_name}"
            self.queue_draw()
            return True

        return False

    def _handle_resize(self, x: int, y: int, canvas_width: int, canvas_height: int):
        """Handle zone resizing based on which handle is being dragged"""
        if not self.selected_zone or not self.zone_original_rect or not self.move_start:
            return

        dx = (x - self.move_start[0]) / canvas_width
        dy = (y - self.move_start[1]) / canvas_height

        orig_x, orig_y, orig_w, orig_h = self.zone_original_rect

        new_x, new_y = orig_x, orig_y
        new_w, new_h = orig_w, orig_h

        # Apply resize based on handle
        if 'n' in self.resize_handle:
            new_y = orig_y + dy
            new_h = orig_h - dy
        if 's' in self.resize_handle:
            new_h = orig_h + dy
        if 'w' in self.resize_handle:
            new_x = orig_x + dx
            new_w = orig_w - dx
        if 'e' in self.resize_handle:
            new_w = orig_w + dx

        # Clamp to canvas bounds and minimum size
        min_size = 0.03
        if new_w < min_size:
            if 'w' in self.resize_handle:
                new_x = orig_x + orig_w - min_size
            new_w = min_size
        if new_h < min_size:
            if 'n' in self.resize_handle:
                new_y = orig_y + orig_h - min_size
            new_h = min_size

        new_x = max(0, min(1 - new_w, new_x))
        new_y = max(0, min(1 - new_h, new_y))
        new_w = min(1 - new_x, new_w)
        new_h = min(1 - new_y, new_h)

        self.selected_zone.x = new_x
        self.selected_zone.y = new_y
        self.selected_zone.width = new_w
        self.selected_zone.height = new_h

    def _get_zone_at_position(self, x: int, y: int,
                              canvas_width: int, canvas_height: int) -> Optional[Zone]:
        """Find zone at given position (smallest zone first for overlaps)"""
        rel_x = x / canvas_width
        rel_y = y / canvas_height

        # Find all zones containing the point
        containing_zones = [z for z in self.zones if z.contains_point(rel_x, rel_y)]

        # Return smallest zone (highest priority)
        if containing_zones:
            return min(containing_zones, key=lambda z: z.width * z.height)
        return None

    def _get_handle_at_position(self, x: int, y: int,
                               canvas_width: int, canvas_height: int) -> Optional[str]:
        """Check if position is over a resize handle"""
        if not self.selected_zone:
            return None

        zone = self.selected_zone
        zx = int(zone.x * canvas_width)
        zy = int(zone.y * canvas_height)
        zw = int(zone.width * canvas_width)
        zh = int(zone.height * canvas_height)

        threshold = self.HANDLE_SIZE

        # Check corners first (higher priority)
        if abs(x - zx) < threshold and abs(y - zy) < threshold:
            return 'nw'
        if abs(x - (zx + zw)) < threshold and abs(y - zy) < threshold:
            return 'ne'
        if abs(x - zx) < threshold and abs(y - (zy + zh)) < threshold:
            return 'sw'
        if abs(x - (zx + zw)) < threshold and abs(y - (zy + zh)) < threshold:
            return 'se'

        # Check edges
        if abs(y - zy) < threshold and zx < x < zx + zw:
            return 'n'
        if abs(y - (zy + zh)) < threshold and zx < x < zx + zw:
            return 's'
        if abs(x - zx) < threshold and zy < y < zy + zh:
            return 'w'
        if abs(x - (zx + zw)) < threshold and zy < y < zy + zh:
            return 'e'

        return None

    def _save_zones(self):
        """Save zones to file"""
        if not self.current_file:
            # Default to zones.json
            config_dir = os.path.expanduser("~/.config/snapzones")
            os.makedirs(config_dir, exist_ok=True)
            self.current_file = os.path.join(config_dir, "zones.json")

        try:
            self.zone_manager.zones = self.zones
            self.zone_manager.save_zones(self.current_file)
            self.status_message = f"Saved {len(self.zones)} zones to {os.path.basename(self.current_file)}"
        except Exception as e:
            self.status_message = f"Failed to save: {e}"

        self.queue_draw()

    def _load_zones(self):
        """Load zones from file"""
        if not self.current_file:
            config_dir = os.path.expanduser("~/.config/snapzones")
            self.current_file = os.path.join(config_dir, "zones.json")

        if not os.path.exists(self.current_file):
            self.status_message = f"File not found: {self.current_file}"
            self.queue_draw()
            return

        try:
            self.zones = self.zone_manager.load_zones(self.current_file)
            self.selected_zone = None
            self.status_message = f"Loaded {len(self.zones)} zones from {os.path.basename(self.current_file)}"
        except Exception as e:
            self.status_message = f"Failed to load: {e}"

        self.queue_draw()


def main():
    """Run zone editor overlay"""
    import argparse

    parser = argparse.ArgumentParser(description="SnapZones Zone Editor - Fullscreen Overlay")
    parser.add_argument('--load', type=str, help='Load zone layout from file')
    args = parser.parse_args()

    window = ZoneEditorOverlay()

    # Load file if specified
    if args.load and os.path.exists(args.load):
        try:
            window.zones = window.zone_manager.load_zones(args.load)
            window.current_file = args.load
            window.status_message = f"Loaded {len(window.zones)} zones from {os.path.basename(args.load)}"
        except Exception as e:
            print(f"Failed to load file: {e}")

    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
