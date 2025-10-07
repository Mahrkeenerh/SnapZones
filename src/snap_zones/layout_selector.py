"""Layout selector dialog for SnapZones

GTK dialog for selecting which layout to assign to the current workspace.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import Optional, Callable
from .layout_library import LayoutLibrary


class LayoutSelectorDialog(Gtk.Window):
    """Dialog for selecting a layout to assign to current workspace"""

    def __init__(self, current_workspace: int, layout_library: LayoutLibrary,
                 on_layout_selected: Optional[Callable[[str], None]] = None):
        """
        Initialize layout selector dialog

        Args:
            current_workspace: Current workspace ID
            layout_library: LayoutLibrary instance
            on_layout_selected: Callback when layout is selected (receives layout name)
        """
        super().__init__()

        self.current_workspace = current_workspace
        self.layout_library = layout_library
        self.on_layout_selected = on_layout_selected
        self.selected_layout = None

        self._setup_window()
        self._create_ui()
        self._load_layouts()

    def _setup_window(self):
        """Setup window properties"""
        self.set_title(f"Select Layout for Workspace {self.current_workspace}")
        self.set_default_size(500, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_decorated(True)
        self.set_resizable(True)

        # Make window modal-like
        self.set_modal(True)

        # Connect close events
        self.connect("delete-event", self._on_close)
        self.connect("key-press-event", self._on_key_press)

    def _create_ui(self):
        """Create the UI layout"""
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(15)
        vbox.set_margin_end(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        self.add(vbox)

        # Header label
        header = Gtk.Label()
        header.set_markup(f"<b>Select Layout for Workspace {self.current_workspace}</b>")
        header.set_halign(Gtk.Align.START)
        vbox.pack_start(header, False, False, 0)

        # Current layout info
        current_layout_name = self.layout_library.get_active_layout(self.current_workspace)
        if current_layout_name:
            current_label = Gtk.Label()
            current_label.set_markup(f"<i>Current: {current_layout_name}</i>")
            current_label.set_halign(Gtk.Align.START)
            vbox.pack_start(current_label, False, False, 0)
            self.current_layout_label = current_label
        else:
            current_label = Gtk.Label()
            current_label.set_markup(f"<i>Current: (none set, using default)</i>")
            current_label.set_halign(Gtk.Align.START)
            vbox.pack_start(current_label, False, False, 0)
            self.current_layout_label = current_label

        # Scrollable list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        vbox.pack_start(scrolled, True, True, 0)

        # List box for layouts
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self._on_row_activated)
        scrolled.add(self.listbox)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        vbox.pack_start(button_box, False, False, 0)

        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", self._on_cancel)
        button_box.pack_start(cancel_btn, False, False, 0)

        # Select button
        self.select_btn = Gtk.Button(label="Select")
        self.select_btn.set_sensitive(False)
        self.select_btn.connect("clicked", self._on_select)
        self.select_btn.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.select_btn, False, False, 0)

    def _load_layouts(self):
        """Load and display available layouts"""
        layouts = self.layout_library.get_all_layouts()

        if not layouts:
            # Show empty state
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="No layouts found. Create layouts in the zone editor first.")
            label.set_sensitive(False)
            label.set_halign(Gtk.Align.START)
            label.set_margin_start(10)
            label.set_margin_end(10)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            row.add(label)
            self.listbox.add(row)
            return

        # Get current active layout
        current_layout_name = self.layout_library.get_active_layout(self.current_workspace)

        # Sort layouts by name
        layouts.sort(key=lambda l: l.name)

        for layout in layouts:
            row = Gtk.ListBoxRow()
            row.layout_name = layout.name  # Store layout name in row

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_margin_start(10)
            hbox.set_margin_end(10)
            hbox.set_margin_top(5)
            hbox.set_margin_bottom(5)

            # Layout name and info
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

            name_label = Gtk.Label()
            is_current = (layout.name == current_layout_name)
            if is_current:
                name_label.set_markup(f"<b>{layout.name}</b> ★")
            else:
                name_label.set_markup(f"<b>{layout.name}</b>")
            name_label.set_halign(Gtk.Align.START)
            vbox.pack_start(name_label, False, False, 0)

            # Description and zone count
            info_text = f"{len(layout.zones)} zones"
            if layout.description:
                info_text += f" - {layout.description}"

            info_label = Gtk.Label(label=info_text)
            info_label.set_halign(Gtk.Align.START)
            info_label.get_style_context().add_class("dim-label")
            info_label.set_sensitive(True)
            vbox.pack_start(info_label, False, False, 0)

            hbox.pack_start(vbox, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)

            # Select current layout by default
            if is_current:
                self.listbox.select_row(row)
                self.selected_layout = layout.name
                self.select_btn.set_sensitive(True)

    def _on_row_activated(self, listbox, row):
        """Handle row activation (double-click or Enter)"""
        if hasattr(row, 'layout_name'):
            self.selected_layout = row.layout_name
            self.select_btn.set_sensitive(True)
            self._apply_selection()

    def _on_select(self, button):
        """Handle select button click"""
        self._apply_selection()

    def _apply_selection(self):
        """Apply the selected layout"""
        selected_row = self.listbox.get_selected_row()

        if selected_row and hasattr(selected_row, 'layout_name'):
            layout_name = selected_row.layout_name

            # Set active layout for workspace
            if self.layout_library.set_active_layout(self.current_workspace, layout_name):
                # Call callback
                if self.on_layout_selected:
                    self.on_layout_selected(layout_name)

                self.destroy()
            else:
                # Show error dialog
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Failed to set layout"
                )
                dialog.format_secondary_text(f"Could not assign layout '{layout_name}' to workspace {self.current_workspace}")
                dialog.run()
                dialog.destroy()

    def _on_cancel(self, button):
        """Handle cancel button click"""
        self.destroy()

    def _on_close(self, widget, event):
        """Handle window close"""
        return False  # Allow close

    def _on_key_press(self, widget, event):
        """Handle keyboard shortcuts"""
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)

        # ESC to close
        if keyname == 'Escape':
            self.destroy()
            return True

        # Enter to select (if something is selected)
        if keyname in ('Return', 'KP_Enter'):
            selected_row = self.listbox.get_selected_row()
            if selected_row:
                self._apply_selection()
            return True

        return False


def show_layout_selector(current_workspace: int, layout_library: LayoutLibrary,
                         on_layout_selected: Optional[Callable[[str], None]] = None):
    """
    Show layout selector dialog

    Args:
        current_workspace: Current workspace ID
        layout_library: LayoutLibrary instance
        on_layout_selected: Callback when layout is selected
    """
    dialog = LayoutSelectorDialog(current_workspace, layout_library, on_layout_selected)
    dialog.show_all()


def main():
    """Standalone test for layout selector"""
    import argparse

    parser = argparse.ArgumentParser(description='SnapZones Layout Selector')
    parser.add_argument('--workspace', type=int, default=0,
                       help='Workspace ID (default: 0)')

    args = parser.parse_args()

    # Create library and show selector
    library = LayoutLibrary()

    def on_selected(layout_name):
        print(f"Selected layout '{layout_name}' for workspace {args.workspace}")

    show_layout_selector(args.workspace, library, on_selected)

    # Run GTK main loop
    Gtk.main()


if __name__ == '__main__':
    main()
