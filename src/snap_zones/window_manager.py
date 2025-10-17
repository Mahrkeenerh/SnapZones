"""Window management utilities for SnapZones using X11"""

import sys
from typing import List, Optional, Tuple, Dict
from Xlib import X, display, protocol
from Xlib.error import XError


class WindowInfo:
    """Represents information about a window"""

    def __init__(self, window_id: int, title: str, x: int, y: int, width: int, height: int):
        self.window_id = window_id
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return f"WindowInfo(id={hex(self.window_id)}, title='{self.title}', geometry=({self.x}, {self.y}, {self.width}, {self.height}))"


class WindowManager:
    """Manages X11 window operations"""

    def __init__(self):
        try:
            self.display = display.Display()
            self.screen = self.display.screen()
            self.root = self.screen.root
        except Exception as e:
            print(f"Error connecting to X11 display: {e}", file=sys.stderr)
            raise

        # Detect Window Calls extension (once at startup)
        self.has_window_calls = self._detect_window_calls_extension()

        if self.has_window_calls:
            print("Window Calls extension detected - using for all window operations")
        else:
            print("Window Calls extension not found - using X11 protocol")

    def get_window_title(self, window) -> str:
        """Get the title of a window"""
        try:
            # Try _NET_WM_NAME first (UTF-8)
            net_wm_name = self.display.get_atom('_NET_WM_NAME')
            utf8_string = self.display.get_atom('UTF8_STRING')
            prop = window.get_full_property(net_wm_name, utf8_string)
            if prop and prop.value:
                return prop.value.decode('utf-8', errors='replace')

            # Fallback to WM_NAME
            wm_name = window.get_wm_name()
            if wm_name:
                return wm_name

            return "<Untitled>"
        except Exception:
            return "<Unknown>"

    def get_window_frame_extents(self, window) -> Tuple[int, int, int, int]:
        """
        Get frame extents (window decorations) for a window

        Returns:
            Tuple of (left, right, top, bottom) border sizes in pixels
        """
        try:
            # First try _GTK_FRAME_EXTENTS for GTK apps with client-side decorations
            # This property describes invisible borders/shadows around GTK windows
            gtk_frame_extents = self.display.get_atom('_GTK_FRAME_EXTENTS')
            gtk_extents_prop = window.get_full_property(gtk_frame_extents, X.AnyPropertyType)

            if gtk_extents_prop and len(gtk_extents_prop.value) >= 4:
                left, right, top, bottom = gtk_extents_prop.value[:4]
                return (left, right, top, bottom)
        except Exception:
            pass

        try:
            # Try to get _NET_FRAME_EXTENTS property (standard window manager decorations)
            net_frame_extents = self.display.get_atom('_NET_FRAME_EXTENTS')
            extents_prop = window.get_full_property(net_frame_extents, X.AnyPropertyType)

            if extents_prop and len(extents_prop.value) >= 4:
                left, right, top, bottom = extents_prop.value[:4]
                return (left, right, top, bottom)
        except Exception:
            pass

        # Fallback: No frame extents detected
        # NOTE: The old fallback code that estimated borders from negative coordinates
        # is now broken since translate_coords can legitimately return negative coords
        return (0, 0, 0, 0)

    def get_window_geometry(self, window) -> Tuple[int, int, int, int]:
        """Get window geometry (x, y, width, height)"""
        try:
            geom = window.get_geometry()
            # Translate coordinates to root window
            # CORRECT: root.translate_coords(window, 0, 0) converts window's (0,0) to root coords
            # WRONG: window.translate_coords(root, 0, 0) converts root's (0,0) to window coords (inverts!)
            trans = self.root.translate_coords(window, 0, 0)
            return (trans.x, trans.y, geom.width, geom.height)
        except XError:
            return (0, 0, 0, 0)

    def is_normal_window(self, window) -> bool:
        """Check if window is a normal application window (not desktop, dock, etc.)"""
        try:
            # Check window type
            net_wm_window_type = self.display.get_atom('_NET_WM_WINDOW_TYPE')
            window_type = window.get_full_property(net_wm_window_type, X.AnyPropertyType)

            if window_type:
                type_atoms = [self.display.get_atom_name(atom) for atom in window_type.value]
                # Skip desktop, dock, and other non-normal windows
                skip_types = ['_NET_WM_WINDOW_TYPE_DESKTOP', '_NET_WM_WINDOW_TYPE_DOCK',
                             '_NET_WM_WINDOW_TYPE_TOOLBAR', '_NET_WM_WINDOW_TYPE_MENU',
                             '_NET_WM_WINDOW_TYPE_SPLASH', '_NET_WM_WINDOW_TYPE_NOTIFICATION']
                if any(t in skip_types for t in type_atoms):
                    return False

            # Check if window is mapped (visible)
            attrs = window.get_attributes()
            if attrs.map_state != X.IsViewable:
                return False

            return True
        except (XError, Exception):
            return False

    def get_all_windows(self) -> List[WindowInfo]:
        """Get information about all normal application windows"""
        windows = []

        try:
            # Get list of all client windows from _NET_CLIENT_LIST
            net_client_list = self.display.get_atom('_NET_CLIENT_LIST')
            client_list_prop = self.root.get_full_property(net_client_list, X.AnyPropertyType)

            if not client_list_prop:
                return windows

            for window_id in client_list_prop.value:
                try:
                    window = self.display.create_resource_object('window', window_id)

                    if not self.is_normal_window(window):
                        continue

                    title = self.get_window_title(window)
                    x, y, width, height = self.get_window_geometry(window)

                    # Skip windows with invalid geometry
                    if width > 0 and height > 0:
                        windows.append(WindowInfo(window_id, title, x, y, width, height))

                except (XError, Exception):
                    continue

        except Exception as e:
            print(f"Error getting window list: {e}", file=sys.stderr)

        return windows

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active (focused) window"""
        try:
            net_active_window = self.display.get_atom('_NET_ACTIVE_WINDOW')
            active_prop = self.root.get_full_property(net_active_window, X.AnyPropertyType)

            if not active_prop or not active_prop.value:
                return None

            window_id = active_prop.value[0]
            if window_id == 0:
                return None

            window = self.display.create_resource_object('window', window_id)

            if not self.is_normal_window(window):
                return None

            title = self.get_window_title(window)
            x, y, width, height = self.get_window_geometry(window)

            return WindowInfo(window_id, title, x, y, width, height)

        except Exception as e:
            print(f"Error getting active window: {e}", file=sys.stderr)
            return None

    def get_window_at_position(self, x: int, y: int) -> Optional[WindowInfo]:
        """Get the window at the specified screen coordinates"""
        try:
            # Query the window at position
            pointer_window = self.root.query_pointer()
            child = pointer_window.child

            if child == 0:
                return None

            # Walk up the window tree to find the top-level window
            window = child
            while True:
                parent = window.query_tree().parent
                if parent == self.root or parent == 0:
                    break
                window = parent

            if not self.is_normal_window(window):
                return None

            window_id = window.id
            title = self.get_window_title(window)
            wx, wy, width, height = self.get_window_geometry(window)

            return WindowInfo(window_id, title, wx, wy, width, height)

        except Exception as e:
            print(f"Error getting window at position: {e}", file=sys.stderr)
            return None

    def move_resize_window(self, window_id: int, x: int, y: int,
                           width: int, height: int) -> bool:
        """
        Move and resize window.

        Uses Window Calls extension if available, otherwise falls back to X11.
        Detection happens once at startup, not per-call.

        Args:
            window_id: Window ID
            x, y: Target position
            width, height: Target size

        Returns:
            True if successful
        """

        # Use Window Calls if available (detected at startup)
        if self.has_window_calls:
            return self._move_resize_via_window_calls(window_id, x, y, width, height)

        # Otherwise use existing X11 implementation
        return self._move_resize_via_x11(window_id, x, y, width, height)

    def _move_resize_via_x11(self, window_id: int, x: int, y: int, width: int, height: int) -> bool:
        """
        Move and resize window using X11 protocol.
        This is the original implementation, now used as fallback.
        """
        try:
            window = self.display.create_resource_object('window', window_id)

            # DEBUG: Log X11 move attempt
            title = self.get_window_title(window)
            print(f"[X11] Moving window '{title}' (ID: {window_id:#x}) to ({x}, {y}, {width}, {height})", file=sys.stderr)

            # Remove maximized state if present
            self._unmaximize_window(window)

            # Get frame extents (including invisible GTK borders/shadows)
            left, right, top, bottom = self.get_window_frame_extents(window)

            # Adjust position to compensate for invisible borders
            # If window has invisible borders, we need to position it so the VISIBLE content
            # starts at the target x,y (not the invisible border)
            adjusted_x = x - left
            adjusted_y = y - top
            adjusted_width = width + left + right
            adjusted_height = height + top + bottom

            # Use _NET_MOVERESIZE_WINDOW for better compatibility with window managers
            net_moveresize_window = self.display.get_atom('_NET_MOVERESIZE_WINDOW')

            # Gravity flags: StaticGravity (10) means coordinates are for the window including decorations
            # Flags: source=1 (application), x, y, width, height set
            gravity = 10  # StaticGravity
            source = 1    # Application
            flags = (source << 12) | (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | gravity

            # Convert signed values to unsigned 32-bit for X11 protocol
            # Negative coordinates need to be represented as large unsigned values
            def to_uint32(val):
                if val < 0:
                    return (1 << 32) + val
                return val

            event = protocol.event.ClientMessage(
                window=window,
                client_type=net_moveresize_window,
                data=(32, [flags, to_uint32(adjusted_x), to_uint32(adjusted_y), adjusted_width, adjusted_height])
            )

            mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
            self.root.send_event(event, event_mask=mask)
            self.display.flush()
            self.display.sync()

            return True

        except Exception as e:
            print(f"Error moving/resizing window: {e}", file=sys.stderr)
            return False

    def _get_window_calls_id(self, x11_window_id: int) -> Optional[int]:
        """
        Map X11 window ID to Window Calls window ID.

        Uses PID and window title to match windows between the two systems.
        Handles frame windows by checking their children for properties.

        Args:
            x11_window_id: X11 window ID

        Returns:
            Window Calls window ID if found, None otherwise
        """
        import subprocess
        import json

        try:
            # Get X11 window info
            window = self.display.create_resource_object('window', x11_window_id)

            # Get PID from X11 window
            net_wm_pid = self.display.get_atom('_NET_WM_PID')
            pid_prop = window.get_full_property(net_wm_pid, X.AnyPropertyType)

            # If no PID on parent, check first child (common for frame windows)
            if not pid_prop:
                try:
                    tree = window.query_tree()
                    if tree.children and len(tree.children) > 0:
                        child_window = tree.children[0]
                        pid_prop = child_window.get_full_property(net_wm_pid, X.AnyPropertyType)
                        if pid_prop:
                            # Use child window for getting properties
                            window = child_window
                except Exception:
                    pass

            if not pid_prop:
                return None
            x11_pid = pid_prop.value[0]

            # Get title from X11 window
            x11_title = self.get_window_title(window)

            # Get Window Calls window list
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell/Extensions/Windows',
                '--method', 'org.gnome.Shell.Extensions.Windows.List'
            ],
            capture_output=True,
            text=True,
            timeout=1.0
            )

            if result.returncode != 0:
                return None

            # Parse Window Calls output - it's a tuple with JSON string: ('...',)
            output = result.stdout.strip()
            if output.startswith("('") and output.endswith("',)"):
                json_str = output[2:-3]  # Remove ("' and "',)
                windows = json.loads(json_str)

                # First try to match by PID only (for efficiency)
                candidates = [w for w in windows if w.get('pid') == x11_pid]

                if len(candidates) == 1:
                    # Only one window with this PID, use it
                    return candidates[0]['id']
                elif len(candidates) > 1:
                    # Multiple windows with same PID
                    # Use the focused/active window from the candidates
                    print(f"Multiple windows found with PID {x11_pid} - using focused window",
                          file=sys.stderr)

                    # Try to find the focused window among candidates
                    focused = [w for w in candidates if w.get('focus') is True]
                    if len(focused) == 1:
                        print(f"  Found focused window: id={focused[0]['id']}", file=sys.stderr)
                        return focused[0]['id']

                    # If no focused window or multiple focused (shouldn't happen), fall back to X11
                    print(f"  Could not determine focused window - falling back to X11", file=sys.stderr)
                    return None
                elif len(candidates) == 0:
                    # PID matching failed (common for Flatpak apps with sandbox PIDs)
                    # Try matching by WM_CLASS instead
                    print(f"No windows found with PID {x11_pid} - trying WM_CLASS fallback for Flatpak apps",
                          file=sys.stderr)

                    # Get WM_CLASS from X11 window
                    try:
                        wm_class = self.display.get_atom('WM_CLASS')
                        wm_class_prop = window.get_full_property(wm_class, X.AnyPropertyType)
                        if wm_class_prop and wm_class_prop.value:
                            # WM_CLASS contains instance\0class\0
                            wm_class_str = wm_class_prop.value.decode('utf-8', errors='replace')
                            # Split by null byte and get the class name (second element)
                            wm_class_parts = wm_class_str.split('\0')
                            if len(wm_class_parts) >= 2:
                                x11_wm_class = wm_class_parts[1]
                                print(f"  X11 WM_CLASS: {x11_wm_class}", file=sys.stderr)

                                # Match by WM_CLASS in Window Calls
                                wm_class_candidates = [w for w in windows if w.get('wm_class', '').lower() == x11_wm_class.lower()]

                                if len(wm_class_candidates) == 1:
                                    print(f"  Found window by WM_CLASS: id={wm_class_candidates[0]['id']}", file=sys.stderr)
                                    return wm_class_candidates[0]['id']
                                elif len(wm_class_candidates) > 1:
                                    # Multiple windows with same WM_CLASS, use focused one
                                    print(f"  Multiple windows with WM_CLASS '{x11_wm_class}' - using focused window", file=sys.stderr)
                                    focused = [w for w in wm_class_candidates if w.get('focus') is True]
                                    if len(focused) >= 1:
                                        print(f"  Found focused window: id={focused[0]['id']}", file=sys.stderr)
                                        return focused[0]['id']
                    except Exception as e:
                        print(f"  WM_CLASS fallback failed: {e}", file=sys.stderr)

            return None

        except Exception as e:
            print(f"Error mapping window ID: {e}", file=sys.stderr)
            return None

    def _detect_window_calls_extension(self) -> bool:
        """
        Detect if Window Calls GNOME extension is available.
        Called once at startup.

        Returns:
            True if extension is available and responding
        """
        try:
            import subprocess

            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell/Extensions/Windows',
                '--method', 'org.gnome.Shell.Extensions.Windows.List'
            ],
            capture_output=True,
            timeout=1.0  # Quick timeout - should respond immediately
            )

            return result.returncode == 0

        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False

    def _move_resize_via_window_calls(self, window_id: int, x: int, y: int,
                                       width: int, height: int) -> bool:
        """
        Move and resize window using Window Calls GNOME extension.
        Falls back to X11 if Window Calls mapping or execution fails.

        Args:
            window_id: X11 window ID (as integer)
            x, y: Target position
            width, height: Target size

        Returns:
            True if successful, False otherwise
        """
        import subprocess

        try:
            # Map X11 window ID to Window Calls ID
            wc_window_id = self._get_window_calls_id(window_id)
            if wc_window_id is None:
                print(f"Could not map X11 window {window_id:#x} to Window Calls ID, falling back to X11",
                      file=sys.stderr)
                return self._move_resize_via_x11(window_id, x, y, width, height)

            # Use separate Resize and Move calls instead of MoveResize
            # MoveResize has issues with some windows (e.g., Steam) where it only resizes but doesn't move

            # First resize
            resize_result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell/Extensions/Windows',
                '--method', 'org.gnome.Shell.Extensions.Windows.Resize',
                str(wc_window_id),
                str(width),
                str(height)
            ],
            capture_output=True,
            timeout=2.0
            )

            if resize_result.returncode != 0:
                print(f"Window Calls Resize failed: {resize_result.stderr.decode('utf-8', errors='replace')}, falling back to X11",
                      file=sys.stderr)
                return self._move_resize_via_x11(window_id, x, y, width, height)

            # Then move
            move_result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell/Extensions/Windows',
                '--method', 'org.gnome.Shell.Extensions.Windows.Move',
                str(wc_window_id),
                str(x),
                str(y)
            ],
            capture_output=True,
            timeout=2.0
            )

            if move_result.returncode == 0:
                return True
            else:
                # Window Calls failed, fall back to X11
                print(f"Window Calls Move failed: {move_result.stderr.decode('utf-8', errors='replace')}, falling back to X11",
                      file=sys.stderr)
                return self._move_resize_via_x11(window_id, x, y, width, height)

        except subprocess.TimeoutExpired:
            print(f"Window Calls timeout for window {window_id:#x}, falling back to X11", file=sys.stderr)
            return self._move_resize_via_x11(window_id, x, y, width, height)
        except Exception as e:
            print(f"Window Calls error: {e}, falling back to X11", file=sys.stderr)
            return self._move_resize_via_x11(window_id, x, y, width, height)

    def _unmaximize_window(self, window):
        """Remove maximized state from a window"""
        try:
            net_wm_state = self.display.get_atom('_NET_WM_STATE')
            net_wm_state_maximized_vert = self.display.get_atom('_NET_WM_STATE_MAXIMIZED_VERT')
            net_wm_state_maximized_horz = self.display.get_atom('_NET_WM_STATE_MAXIMIZED_HORZ')

            # Send event to remove maximized state (0 = remove)
            for atom in [net_wm_state_maximized_vert, net_wm_state_maximized_horz]:
                event = protocol.event.ClientMessage(
                    window=window,
                    client_type=net_wm_state,
                    data=(32, [0, atom, 0, 1])  # 0=remove, source=1 (application)
                )
                mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
                self.root.send_event(event, event_mask=mask)

            self.display.flush()

        except Exception:
            pass  # Silently fail if window doesn't support this

    def get_window_by_id(self, window_id: int) -> Optional[WindowInfo]:
        """Get window information by window ID"""
        try:
            window = self.display.create_resource_object('window', window_id)

            if not self.is_normal_window(window):
                return None

            title = self.get_window_title(window)
            x, y, width, height = self.get_window_geometry(window)

            return WindowInfo(window_id, title, x, y, width, height)

        except Exception as e:
            print(f"Error getting window by ID: {e}", file=sys.stderr)
            return None

    def monitor_window_movements(self, on_move_start=None, on_move_update=None, on_move_end=None):
        """
        Monitor window movement events and call callbacks

        Args:
            on_move_start: Callback(window_id, x, y) when window starts moving
            on_move_update: Callback(window_id, x, y) when window position updates
            on_move_end: Callback(window_id, x, y) when window stops moving

        Note: This is a blocking call that runs an event loop
        """
        import time
        from collections import defaultdict

        # Subscribe to ConfigureNotify events on all windows
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)

        # Track window movement state
        window_positions = {}  # window_id -> (x, y, timestamp)
        moving_windows = set()  # window_ids currently moving

        MOVE_TIMEOUT = 0.15  # seconds without movement to consider stopped

        print("Monitoring window movements... (Press Ctrl+C to stop)", flush=True)

        while True:
            # Check for X11 events (non-blocking)
            while self.display.pending_events():
                event = self.display.next_event()

                if event.type == X.ConfigureNotify:
                    window_id = event.window.id
                    x, y = event.x, event.y
                    timestamp = time.time()

                    # Check if this is a normal window we care about
                    try:
                        window = self.display.create_resource_object('window', window_id)
                        if not self.is_normal_window(window):
                            continue
                    except:
                        continue

                    # Check if window actually moved
                    if window_id in window_positions:
                        old_x, old_y, old_time = window_positions[window_id]
                        if old_x == x and old_y == y:
                            continue  # No actual movement

                        # Window moved
                        if window_id not in moving_windows:
                            # Movement started
                            moving_windows.add(window_id)
                            if on_move_start:
                                on_move_start(window_id, x, y)
                        else:
                            # Movement continuing
                            if on_move_update:
                                on_move_update(window_id, x, y)

                    window_positions[window_id] = (x, y, timestamp)

            # Check for windows that stopped moving
            current_time = time.time()
            stopped_windows = []
            for window_id in list(moving_windows):
                if window_id in window_positions:
                    x, y, timestamp = window_positions[window_id]
                    if current_time - timestamp > MOVE_TIMEOUT:
                        stopped_windows.append((window_id, x, y))
                        moving_windows.remove(window_id)

            for window_id, x, y in stopped_windows:
                if on_move_end:
                    on_move_end(window_id, x, y)

            # Small sleep to avoid busy waiting
            time.sleep(0.01)
            self.display.flush()

    def close(self):
        """Clean up display connection"""
        if self.display:
            self.display.close()


def main():
    """Command-line interface for testing window operations"""
    import argparse

    parser = argparse.ArgumentParser(description='SnapZones Window Manager')
    parser.add_argument('--list', action='store_true', help='List all windows')
    parser.add_argument('--active', action='store_true', help='Show active window')
    parser.add_argument('--at-cursor', action='store_true', help='Show window under cursor')
    parser.add_argument('--move-active', nargs=4, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       type=int, help='Move/resize active window to X Y WIDTH HEIGHT')

    args = parser.parse_args()

    wm = WindowManager()

    try:
        if args.list:
            print("All windows:")
            print("-" * 80)
            windows = wm.get_all_windows()
            for i, win in enumerate(windows, 1):
                print(f"{i}. {win}")
            print(f"\nTotal: {len(windows)} windows")

        elif args.active:
            active = wm.get_active_window()
            if active:
                print("Active window:")
                print(active)
            else:
                print("No active window")

        elif args.at_cursor:
            print("Move your cursor over a window...")
            import time
            time.sleep(2)
            win = wm.get_window_at_position(0, 0)  # Position is ignored, uses current pointer
            if win:
                print("Window under cursor:")
                print(win)
            else:
                print("No window under cursor")

        elif args.move_active:
            x, y, width, height = args.move_active
            active = wm.get_active_window()
            if active:
                print(f"Moving window '{active.title}' to ({x}, {y}, {width}, {height})...")
                success = wm.move_resize_window(active.window_id, x, y, width, height)
                if success:
                    print("Window moved successfully!")
                    import time
                    time.sleep(0.5)  # Give window manager time to update
                    updated = wm.get_window_by_id(active.window_id)
                    if updated:
                        print(f"New geometry: ({updated.x}, {updated.y}, {updated.width}, {updated.height})")
                else:
                    print("Failed to move window")
            else:
                print("No active window")

        else:
            parser.print_help()

    finally:
        wm.close()


if __name__ == '__main__':
    main()
