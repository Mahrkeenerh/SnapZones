"""Core window snapping logic for SnapZones"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import Optional, Dict, Tuple
import threading
import time

# Handle both package and standalone imports
try:
    from .window_manager import WindowManager
    from .zone import Zone, ZoneManager
    from .overlay import OverlayManager
    from .input_monitor import InputMonitor
except ImportError:
    from window_manager import WindowManager
    from zone import Zone, ZoneManager
    from overlay import OverlayManager
    from input_monitor import InputMonitor


class WindowSnapper:
    """Manages window snapping to zones"""

    def __init__(self):
        self.window_manager = WindowManager()
        self.zone_manager = ZoneManager()
        self.overlay_manager = OverlayManager()
        self.input_monitor = InputMonitor()

        # State tracking
        self._active_window_id: Optional[int] = None
        self._original_geometry: Optional[Tuple[int, int, int, int]] = None
        self._is_snapping = False
        self._selected_zone: Optional[Zone] = None

        # Workspace support
        self._workspace_zones: Dict[int, ZoneManager] = {}
        self._current_workspace = 0

    def snap_window_to_zone(self, window_id: int, zone: Zone, animate: bool = False) -> bool:
        """
        Snap a window to a zone

        Args:
            window_id: X11 window ID
            zone: Zone to snap to
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

            # Move and resize window to zone
            success = self.window_manager.move_resize_window(
                window_id, zone.x, zone.y, zone.width, zone.height
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

    def load_workspace_zones(self, workspace: Optional[int] = None) -> ZoneManager:
        """
        Load zones for a specific workspace

        Args:
            workspace: Workspace number (None = current workspace)

        Returns:
            ZoneManager for the workspace
        """
        if workspace is None:
            workspace = self.get_current_workspace()

        # Check if zones already loaded for this workspace
        if workspace in self._workspace_zones:
            return self._workspace_zones[workspace]

        # Create new zone manager for this workspace
        zm = ZoneManager()
        zones_file = f"{zm.config_dir}/zones_ws{workspace}.json"

        # Try to load workspace-specific zones
        if zm.load_from_file(zones_file):
            print(f"Loaded zones for workspace {workspace}")
        else:
            # Fall back to default zones.json
            default_file = f"{zm.config_dir}/zones.json"
            if zm.load_from_file(default_file):
                print(f"Loaded default zones for workspace {workspace}")
            else:
                print(f"No zones found for workspace {workspace}")

        self._workspace_zones[workspace] = zm
        return zm

    def save_workspace_zones(self, workspace: Optional[int] = None) -> bool:
        """
        Save zones for a specific workspace

        Args:
            workspace: Workspace number (None = current workspace)

        Returns:
            True if successful, False otherwise
        """
        if workspace is None:
            workspace = self.get_current_workspace()

        if workspace not in self._workspace_zones:
            return False

        zm = self._workspace_zones[workspace]
        zones_file = f"{zm.config_dir}/zones_ws{workspace}.json"

        return zm.save_to_file(zones_file)

    def show_overlay_at_cursor(self) -> Optional[Zone]:
        """
        Show overlay at cursor position and wait for zone selection

        Returns:
            Selected zone or None if cancelled
        """
        # Load zones for current workspace
        workspace = self.get_current_workspace()
        zm = self.load_workspace_zones(workspace)

        if len(zm) == 0:
            print("No zones configured for current workspace")
            return None

        # Show overlay
        self.overlay_manager.show(list(zm))

        return None  # Zone selection handled by callback

    def hide_overlay(self):
        """Hide the overlay"""
        self.overlay_manager.hide()

    def start_snap_workflow(self):
        """
        Start the complete snap workflow:
        1. Monitor for Shift+drag
        2. Show overlay when drag detected
        3. Highlight zone under cursor
        4. Snap window on release
        """
        print("Starting snap workflow...")
        print("Shift+drag a window to snap it to a zone")
        print("Press Escape to cancel")
        print("Press Ctrl+C to exit")

        # Get active window at start
        active_window = self.window_manager.get_active_window()
        if active_window:
            self._active_window_id = active_window.window_id
            self._original_geometry = (active_window.x, active_window.y, active_window.width, active_window.height)
            print(f"Tracking window {self._active_window_id}")

        # Set up overlay callbacks
        overlay = self.overlay_manager.create_overlay()

        def on_zone_selected(zone: Zone):
            print(f"Zone selected: {zone}")
            self._selected_zone = zone

            # Snap active window to zone
            if self._active_window_id:
                success = self.snap_window_to_zone(self._active_window_id, zone)
                if success:
                    print(f"Snapped window to {zone}")
                else:
                    print("Failed to snap window")

        def on_overlay_hidden():
            print("Overlay hidden")
            self._is_snapping = False

        overlay.set_on_zone_selected(on_zone_selected)
        overlay.set_on_overlay_hidden(on_overlay_hidden)

        # Set up input monitor callbacks
        def on_shift_drag_start(x: int, y: int):
            """Called when Shift+drag starts"""
            print(f"Shift+drag started at ({x}, {y})")
            self._is_snapping = True

            # Get currently active window
            active_window = self.window_manager.get_active_window()
            if active_window:
                self._active_window_id = active_window.window_id
                self._original_geometry = (active_window.x, active_window.y, active_window.width, active_window.height)

            # Show overlay
            workspace = self.get_current_workspace()
            zm = self.load_workspace_zones(workspace)

            if len(zm) > 0:
                self.overlay_manager.show(list(zm))
            else:
                print("No zones configured")

        def on_shift_drag_end(x: int, y: int):
            """Called when Shift+drag ends"""
            print(f"Shift+drag ended at ({x}, {y})")

            # Don't auto-hide overlay - let zone click handle it
            # or let Escape cancel it

        self.input_monitor.set_on_shift_drag_start(on_shift_drag_start)
        self.input_monitor.set_on_shift_drag_end(on_shift_drag_end)

        # Start monitoring in separate thread
        monitor_thread = threading.Thread(target=self.input_monitor.start, daemon=True)
        monitor_thread.start()

        # Run GTK main loop
        try:
            Gtk.main()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.input_monitor.stop()
            self.overlay_manager.destroy()


class SnapperCLI:
    """Command-line interface for the snapper"""

    def __init__(self):
        self.snapper = WindowSnapper()

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
                       help='Run interactive snap workflow (Shift+drag to snap)')
    parser.add_argument('--snap-active', metavar='PRESET',
                       choices=['halves', 'thirds', 'quarters', 'grid3x3'],
                       help='Snap active window to first zone of preset')
    parser.add_argument('--screen-width', type=int, default=3440, help='Screen width')
    parser.add_argument('--screen-height', type=int, default=1440, help='Screen height')
    parser.add_argument('--list-workspaces', action='store_true',
                       help='List all workspaces with zone counts')

    args = parser.parse_args()

    cli = SnapperCLI()

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
