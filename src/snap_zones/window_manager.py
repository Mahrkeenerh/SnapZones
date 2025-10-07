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

            # Use _NET_MOVERESIZE_WINDOW for better compatibility with window managers
            net_moveresize_window = self.display.get_atom('_NET_MOVERESIZE_WINDOW')

            # Gravity (1 = NorthWest), flags indicate which values are set (all of them)
            # Flags: 0x1=x, 0x2=y, 0x4=width, 0x8=height, 0x10=gravity
            flags = (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12)  # Source indication + x,y,w,h

            event = protocol.event.ClientMessage(
                window=window,
                client_type=net_moveresize_window,
                data=(32, [flags, x, y, width, height])
            )

            mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
            self.root.send_event(event, event_mask=mask)
            self.display.flush()
            self.display.sync()

            return True

        except Exception as e:
            print(f"Error moving/resizing window: {e}", file=sys.stderr)
            return False

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
