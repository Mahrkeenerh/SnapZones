#!/usr/bin/env python3
"""
SnapZones Daemon - Background service for window snapping

Runs continuously in the background to:
1. Monitor for modifier+drag window movements (shows zone overlay)
2. Snap windows to zones on release

Note: Zone editor hotkey (Super+Shift+Tab) is registered via native GNOME
keyboard shortcuts during installation (gsettings).

Usage:
    python -m snap_zones.daemon [--modifier MODIFIER]

    --modifier: Trigger key for snapping (default: alt)
                Options: shift, ctrl, alt, super
"""

import sys
import os
import signal

from .snapper import WindowSnapper


class SnapZonesDaemon:
    """Background daemon for SnapZones window snapping"""

    def __init__(self, trigger_modifier: str = 'alt'):
        """
        Initialize daemon

        Args:
            trigger_modifier: Modifier key for snapping (shift/ctrl/alt/super)
        """
        self.trigger_modifier = trigger_modifier

        # Initialize snapper (handles modifier+drag workflow)
        self.snapper = WindowSnapper(trigger_modifier=trigger_modifier)

        print(f"SnapZones Daemon starting...")
        print(f"Snapping trigger: {trigger_modifier.upper()} + Drag")
        print(f"Zone editor: Super+Shift+Tab (native keyboard shortcut)")

    def _setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown"""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self):
        """Start the daemon"""
        try:
            # Setup signal handlers
            self._setup_signal_handlers()

            print("\nSnapZones daemon is running")
            print("Press Ctrl+C to exit\n")

            # Start snapping workflow (this runs GTK main loop)
            self.snapper.start_snap_workflow()

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
        except Exception as e:
            print(f"ERROR: Daemon crashed: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
            return False

        return True

    def stop(self):
        """Stop the daemon and cleanup"""
        print("Stopping daemon...")

        # Stop snapper trackers
        if self.snapper:
            if self.snapper.keyboard_tracker:
                self.snapper.keyboard_tracker.stop()
            if self.snapper.mouse_tracker:
                self.snapper.mouse_tracker.stop()

        print("Daemon stopped")


def main():
    """Main entry point for daemon"""
    import argparse

    parser = argparse.ArgumentParser(
        description='SnapZones Daemon - Background window snapping service'
    )
    parser.add_argument(
        '--modifier',
        choices=['shift', 'ctrl', 'alt', 'super'],
        default='alt',
        help='Modifier key to trigger zone overlay (default: alt)'
    )

    args = parser.parse_args()

    # Check for existing daemon instance
    pid_file = os.path.expanduser('~/.config/snapzones/daemon.pid')
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)

    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                print(f"ERROR: SnapZones daemon is already running (PID: {old_pid})")
                print(f"Kill it with: kill {old_pid}")
                sys.exit(1)
            except OSError:
                # Process doesn't exist, remove stale PID file
                os.remove(pid_file)
        except (ValueError, IOError):
            # Invalid PID file, remove it
            try:
                os.remove(pid_file)
            except:
                pass

    # Write our PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    try:
        # Create and start daemon
        daemon = SnapZonesDaemon(trigger_modifier=args.modifier)
        success = daemon.start()
    finally:
        # Clean up PID file
        try:
            os.remove(pid_file)
        except:
            pass

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
