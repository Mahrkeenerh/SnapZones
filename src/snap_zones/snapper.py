"""Core window snapping logic for SnapZones"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import Optional, Dict, Tuple
import threading
import time

from .window_manager import WindowManager
from .zone import Zone, ZoneManager
from .overlay import OverlayManager
from .input_monitor import KeyboardTracker, MouseTracker
from .layout_library import LayoutLibrary


class WindowSnapper:
    """Manages window snapping to zones"""

    def __init__(self, trigger_modifier: str = 'alt'):
        self.window_manager = WindowManager()
        self.zone_manager = ZoneManager()  # Keep for compatibility
        self.layout_library = LayoutLibrary()
        self.overlay_manager = OverlayManager()
        self.keyboard_tracker = KeyboardTracker()
        self.mouse_tracker = MouseTracker()

        # Configuration
        self.trigger_modifier = trigger_modifier.lower()  # 'shift', 'ctrl', 'alt', 'super'

        # State tracking
        self._active_window_id: Optional[int] = None
        self._original_geometry: Optional[Tuple[int, int, int, int]] = None
        self._is_snapping = False
        self._selected_zone: Optional[Zone] = None
        self._overlay_visible = False
        self._window_is_moving = False
        self._last_snap_time: float = 0  # Timestamp of last snap to prevent immediate re-trigger

        # Workspace support
        self._current_workspace = 0

    def snap_window_to_zone(self, window_id: int, zone: Zone, animate: bool = False) -> bool:
        """
        Snap a window to a zone

        Args:
            window_id: X11 window ID
            zone: Zone to snap to (with relative coordinates 0.0-1.0)
            animate: Whether to animate the transition (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get window object
            window = self.window_manager.display.create_resource_object('window', window_id)

            # Get current window geometry to store as original
            x, y, width, height = self.window_manager.get_window_geometry(window)

            # Store original geometry if not already stored
            if self._original_geometry is None:
                self._original_geometry = (x, y, width, height)

            # Get screen dimensions to convert relative coordinates to absolute
            screen = self.window_manager.display.screen()
            screen_width = screen.width_in_pixels
            screen_height = screen.height_in_pixels

            # Convert relative zone coordinates (0.0-1.0) to absolute pixels
            abs_x = int(zone.x * screen_width)
            abs_y = int(zone.y * screen_height)
            abs_width = int(zone.width * screen_width)
            abs_height = int(zone.height * screen_height)

            # Move and resize window to zone
            success = self.window_manager.move_resize_window(
                window_id, abs_x, abs_y, abs_width, abs_height
            )

            return success

        except Exception as e:
            print(f"Error snapping window: {e}")
            return False

    def snap_active_window_to_zone(self, zone: Zone, animate: bool = False) -> bool:
        """
        Snap the active window to a zone

        Args:
            zone: Zone to snap to
            animate: Whether to animate the transition (optional)

        Returns:
            True if successful, False otherwise
        """
        active_window = self.window_manager.get_active_window()
        if not active_window:
            return False

        return self.snap_window_to_zone(active_window.window_id, zone, animate)

    def restore_window_geometry(self, window_id: int) -> bool:
        """
        Restore window to its original geometry before snapping

        Args:
            window_id: X11 window ID

        Returns:
            True if successful, False otherwise
        """
        if self._original_geometry is None:
            return False

        x, y, w, h = self._original_geometry
        success = self.window_manager.move_resize_window(window_id, x, y, w, h)

        if success:
            self._original_geometry = None

        return success

    def get_current_workspace(self) -> int:
        """
        Get the current workspace/desktop number

        Returns:
            Workspace number (0-indexed)
        """
        try:
            display = self.window_manager.display
            root = display.screen().root

            # Query _NET_CURRENT_DESKTOP
            current_desktop = root.get_full_property(
                display.intern_atom('_NET_CURRENT_DESKTOP'),
                0  # Xlib.X.AnyPropertyType
            )

            if current_desktop:
                return current_desktop.value[0]

            return 0

        except Exception as e:
            print(f"Error getting current workspace: {e}")
            return 0

    def load_workspace_zones(self, workspace: Optional[int] = None) -> List[Zone]:
        """
        Load zones for a specific workspace using layout library

        Args:
            workspace: Workspace number (None = current workspace)

        Returns:
            List of zones for the workspace
        """
        if workspace is None:
            workspace = self.get_current_workspace()

        # Load layout for this workspace
        layout = self.layout_library.get_workspace_layout(workspace)

        if layout:
            print(f"Loaded layout '{layout.name}' for workspace {workspace} ({len(layout.zones)} zones)")
            return list(layout.zones)
        else:
            print(f"No layout found for workspace {workspace}")
            return []

    def show_overlay_at_cursor(self) -> Optional[Zone]:
        """
        Show overlay at cursor position and wait for zone selection

        Returns:
            Selected zone or None if cancelled
        """
        # Load zones for current workspace
        workspace = self.get_current_workspace()
        zones = self.load_workspace_zones(workspace)

        if len(zones) == 0:
            print("No zones configured for current workspace")
            return None

        # Show overlay
        self.overlay_manager.show(zones)

        return None  # Zone selection handled by callback

    def hide_overlay(self):
        """Hide the overlay"""
        self.overlay_manager.hide()

    def _is_trigger_modifier_pressed(self) -> bool:
        """Check if the configured trigger modifier is currently pressed"""
        if self.trigger_modifier == 'shift':
            return self.keyboard_tracker.is_shift_pressed
        elif self.trigger_modifier == 'ctrl':
            return self.keyboard_tracker.is_ctrl_pressed
        elif self.trigger_modifier == 'alt':
            return self.keyboard_tracker.is_alt_pressed
        elif self.trigger_modifier == 'super':
            return self.keyboard_tracker.is_super_pressed
        return False

    def start_snap_workflow(self):
        """
        Start the complete snap workflow:
        1. Monitor for window drag with modifier key pressed
        2. Show overlay when drag starts with modifier
        3. Hide overlay when modifier is released
        4. Snap window when zone is selected
        """
        print("Starting snap workflow...")
        print(f"Hold {self.trigger_modifier.upper()} and drag a window to snap it to a zone")
        print(f"Release {self.trigger_modifier.upper()} to cancel")
        print("Click on a zone to snap the window")
        print("Press Escape to cancel")
        print("Press Ctrl+C to exit")

        # Start keyboard and mouse trackers
        self.keyboard_tracker.start()
        self.mouse_tracker.start()

        # Set up mouse button release callback
        def on_button_release(button_name: str):
            """Called when any mouse button is released"""
            if button_name == 'left' and self._window_is_moving:
                # Always clear window moving state on mouse release
                self._window_is_moving = False

                # Only process if overlay is visible
                if self._overlay_visible:
                    print("Mouse button released - checking for zone under cursor")

                    def check_zone_and_snap():
                        # Get the currently highlighted zone from overlay
                        overlay = self.overlay_manager.overlay
                        if overlay:
                            highlighted_zone = overlay.get_highlighted_zone()
                            if highlighted_zone and self._active_window_id:
                                print(f"Snapping to highlighted zone: {highlighted_zone}")
                                self.snap_window_to_zone(self._active_window_id, highlighted_zone)
                                # Record snap time to prevent immediate re-trigger
                                import time
                                self._last_snap_time = time.time()

                        # Hide overlay after processing
                        self.overlay_manager.hide()
                        self._overlay_visible = False
                        self._is_snapping = False
                        self._active_window_id = None
                        return False

                    GLib.idle_add(check_zone_and_snap)
                else:
                    # Just clear the active window ID
                    self._active_window_id = None

        self.mouse_tracker.set_on_button_release(on_button_release)

        # Set up keyboard modifier change callback
        def on_modifier_change(shift: bool, ctrl: bool, alt: bool, super_key: bool):
            """Called when modifier keys change state"""
            modifier_pressed = self._is_trigger_modifier_pressed()

            # If overlay is visible and modifier released, hide overlay
            if self._overlay_visible and not modifier_pressed:
                print(f"{self.trigger_modifier.upper()} released - hiding overlay")

                def hide_overlay_on_main_thread():
                    self.overlay_manager.hide()
                    self._overlay_visible = False
                    self._is_snapping = False
                    self._active_window_id = None
                    # Don't clear _window_is_moving here - user might still be dragging
                    return False

                GLib.idle_add(hide_overlay_on_main_thread)

            # If window is moving, modifier pressed, but overlay not visible, show overlay
            # Only show if mouse button is actually pressed (still dragging)
            elif self._window_is_moving and modifier_pressed and not self._overlay_visible and self.mouse_tracker.is_left_pressed:
                print(f"{self.trigger_modifier.upper()} pressed during drag - showing overlay")

                def show_overlay_on_main_thread():
                    if not self._is_trigger_modifier_pressed():
                        return False

                    self._is_snapping = True
                    self._overlay_visible = True

                    # Show overlay
                    workspace = self.get_current_workspace()
                    zones = self.load_workspace_zones(workspace)

                    if len(zones) > 0:
                        self.overlay_manager.show(zones)
                        print(f"Overlay shown with {len(zones)} zones", flush=True)
                    else:
                        print("No zones configured", flush=True)

                    return False

                GLib.idle_add(show_overlay_on_main_thread)

        self.keyboard_tracker.set_on_modifier_change(on_modifier_change)

        # Set up overlay callbacks
        overlay = self.overlay_manager.create_overlay()

        def on_zone_selected(zone: Zone):
            print(f"Zone selected: {zone}")
            self._selected_zone = zone

            # Snap window to zone
            if self._active_window_id:
                success = self.snap_window_to_zone(self._active_window_id, zone)
                if success:
                    print(f"Snapped window {self._active_window_id} to {zone}")
                else:
                    print("Failed to snap window")

        def on_overlay_hidden():
            print("Overlay hidden")
            self._is_snapping = False
            self._active_window_id = None
            self._overlay_visible = False

        overlay.set_on_zone_selected(on_zone_selected)
        overlay.set_on_overlay_hidden(on_overlay_hidden)

        # Set up window movement callbacks
        def on_move_start(window_id: int, x: int, y: int):
            """Called when window starts moving"""
            # Check if this is too soon after a snap (within 50ms)
            import time
            time_since_snap = time.time() - self._last_snap_time
            if time_since_snap < 0.05:
                print(f"Ignoring window movement {time_since_snap:.3f}s after snap")
                return

            self._window_is_moving = True
            self._active_window_id = window_id

            # Store original geometry
            try:
                window = self.window_manager.display.create_resource_object('window', window_id)
                geom = self.window_manager.get_window_geometry(window)
                self._original_geometry = geom
            except Exception as e:
                print(f"Failed to get window geometry: {e}")

            # Only show overlay if trigger modifier is pressed
            if not self._is_trigger_modifier_pressed():
                print(f"Window {window_id} started moving (no modifier)")
                return

            print(f"Window {window_id} started moving with {self.trigger_modifier.upper()} at ({x}, {y})", flush=True)

            def show_overlay_on_main_thread():
                """Execute GTK operations on main thread"""
                # Double-check modifier is still pressed
                if not self._is_trigger_modifier_pressed():
                    return False

                self._is_snapping = True
                self._overlay_visible = True

                # Show overlay
                workspace = self.get_current_workspace()
                zones = self.load_workspace_zones(workspace)

                if len(zones) > 0:
                    self.overlay_manager.show(zones)
                    print(f"Overlay shown with {len(zones)} zones", flush=True)
                else:
                    print("No zones configured", flush=True)

                return False  # Don't repeat

            # Schedule GTK operations on main thread
            GLib.idle_add(show_overlay_on_main_thread)

        def on_move_update(window_id: int, x: int, y: int):
            """Called when window position updates"""
            # Could update UI here if needed
            pass

        def on_move_end(window_id: int, x: int, y: int):
            """Called when window stops moving (position unchanged for timeout period)"""
            # Don't mark window as not moving here - wait for mouse button release
            if self._active_window_id == window_id:
                print(f"Window {window_id} stopped moving at ({x}, {y}) - waiting for mouse release")

        # Start window movement monitoring in separate thread
        monitor_thread = threading.Thread(
            target=self.window_manager.monitor_window_movements,
            args=(on_move_start, on_move_update, on_move_end),
            daemon=True
        )
        monitor_thread.start()

        # Run GTK main loop
        try:
            Gtk.main()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.keyboard_tracker.stop()
            self.mouse_tracker.stop()
            self.overlay_manager.destroy()


class SnapperCLI:
    """Command-line interface for the snapper"""

    def __init__(self, trigger_modifier: str = 'alt'):
        self.snapper = WindowSnapper(trigger_modifier=trigger_modifier)

    def run_interactive(self):
        """Run interactive snapping workflow"""
        self.snapper.start_snap_workflow()

    def snap_active_to_preset(self, preset: str, screen_width: int, screen_height: int):
        """Snap active window to first zone of a preset"""
        from zone import create_preset_layout

        zones = create_preset_layout(preset, screen_width, screen_height)
        if not zones:
            print(f"Failed to create preset: {preset}")
            return

        # Snap to first zone
        success = self.snapper.snap_active_window_to_zone(zones[0])
        if success:
            print(f"Snapped active window to {zones[0]}")
        else:
            print("Failed to snap window")

    def list_workspaces(self):
        """List all workspaces with zone counts"""
        import os
        config_dir = os.path.expanduser("~/.config/snapzones")

        print("Workspaces:")
        print("-" * 40)

        for i in range(10):  # Check first 10 workspaces
            zones_file = f"{config_dir}/zones_ws{i}.json"
            if os.path.exists(zones_file):
                zm = ZoneManager()
                if zm.load_from_file(zones_file):
                    print(f"Workspace {i}: {len(zm)} zones")

        # Check for default zones
        default_file = f"{config_dir}/zones.json"
        if os.path.exists(default_file):
            zm = ZoneManager()
            if zm.load_from_file(default_file):
                print(f"Default: {len(zm)} zones")


def main():
    """Command-line interface for testing snapper"""
    import argparse
    import sys
    import os

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    parser = argparse.ArgumentParser(description='SnapZones Window Snapper')
    parser.add_argument('--interactive', action='store_true',
                       help='Run interactive snap workflow (modifier+drag to snap)')
    parser.add_argument('--modifier', choices=['shift', 'ctrl', 'alt', 'super'],
                       default='alt', help='Modifier key to trigger snapping (default: alt)')
    parser.add_argument('--snap-active', metavar='PRESET',
                       choices=['halves', 'thirds', 'quarters', 'grid3x3'],
                       help='Snap active window to first zone of preset')
    parser.add_argument('--screen-width', type=int, default=3440, help='Screen width')
    parser.add_argument('--screen-height', type=int, default=1440, help='Screen height')
    parser.add_argument('--list-workspaces', action='store_true',
                       help='List all workspaces with zone counts')

    args = parser.parse_args()

    cli = SnapperCLI(trigger_modifier=args.modifier)

    if args.interactive:
        cli.run_interactive()
    elif args.snap_active:
        cli.snap_active_to_preset(args.snap_active, args.screen_width, args.screen_height)
    elif args.list_workspaces:
        cli.list_workspaces()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
