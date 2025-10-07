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

        # Fallback: estimate from window geometry
        try:
            geom = window.get_geometry()

            # If window has negative coordinates, it has borders
            left_border = max(0, -geom.x) if geom.x < 0 else 0
            top_border = max(0, -geom.y) if geom.y < 0 else 0

            # If left border detected, assume uniform borders (common pattern)
            if left_border > 0:
                return (left_border, left_border, left_border, left_border)

            # If only top border, it's likely a title bar
            if top_border > 0:
                return (0, 0, top_border, 0)

        except Exception:
            pass

        return (0, 0, 0, 0)

    def get_window_geometry(self, window) -> Tuple[int, int, int, int]:
        """Get window geometry (x, y, width, height)"""
        try:
            geom = window.get_geometry()
            # Translate coordinates to root window
            trans = window.translate_coords(self.root, 0, 0)
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

    def move_resize_window(self, window_id: int, x: int, y: int, width: int, height: int) -> bool:
        """Move and resize a window to the specified geometry"""
        try:
            window = self.display.create_resource_object('window', window_id)

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

    def _get_frame_extents(self, window) -> tuple[int, int, int, int]:
        """
        Get the frame extents (window decorations) for a window

        Returns:
            Tuple of (left, right, top, bottom) border widths in pixels
        """
        try:
            net_frame_extents = self.display.get_atom('_NET_FRAME_EXTENTS')
            extents_prop = window.get_full_property(net_frame_extents, X.AnyPropertyType)

            if extents_prop and len(extents_prop.value) == 4:
                # Returns [left, right, top, bottom]
                return tuple(extents_prop.value)

        except Exception:
            pass

        # Default to no frame if we can't get the property
        return (0, 0, 0, 0)

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
