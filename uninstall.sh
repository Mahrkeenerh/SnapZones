#!/bin/bash
# SnapZones Uninstallation Script

set -e

# Parse arguments
NON_INTERACTIVE=false
if [[ "$1" == "-y" ]] || [[ "$1" == "--yes" ]]; then
    NON_INTERACTIVE=true
fi

BIN_DIR="$HOME/.local/bin"
AUTOSTART_DIR="$HOME/.config/autostart"
CONFIG_DIR="$HOME/.config/snapzones"

echo "========================================="
echo "SnapZones Uninstallation"
echo "========================================="
echo ""

# Stop running daemon
echo "Stopping SnapZones daemon..."
pkill -f "snap_zones.daemon" || true
pkill -f "snapzones" || true
sleep 1
echo "✓ Daemon stopped"
echo ""

# Remove scripts
echo "Removing installed scripts..."
rm -f "$BIN_DIR/snapzones"
rm -f "$BIN_DIR/snapzones-editor"
rm -f "$BIN_DIR/snapzones-status"
echo "✓ Scripts removed"
echo ""

# Remove icon
echo "Removing icon..."
rm -f "$HOME/.local/share/icons/snapzones.png"
echo "✓ Icon removed"
echo ""

# Remove autostart
echo "Removing autostart..."
rm -f "$AUTOSTART_DIR/snapzones.desktop"
echo "✓ Autostart removed"
echo ""

# Remove GNOME keyboard shortcut
echo "Removing keyboard shortcut..."
if command -v gsettings &> /dev/null; then
    # Get current custom keybindings
    current_bindings=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)

    # Find and remove SnapZones entries
    # Look for entries with "snapzones-editor" in the command
    for slot_num in {0..20}; do
        slot_path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${slot_num}/"

        # Check if this slot exists
        if echo "$current_bindings" | grep -q "$slot_path"; then
            # Check if it's our command
            cmd=$(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path command 2>/dev/null || echo "")
            if echo "$cmd" | grep -q "snapzones-editor"; then
                # Remove this slot from the bindings list
                new_bindings=$(echo "$current_bindings" | sed "s|'$slot_path'||g" | sed "s|\[, |\[|g" | sed "s|, \]|\]|g" | sed "s|, , |, |g")
                gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$new_bindings"

                # Reset the slot properties
                gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path name 2>/dev/null || true
                gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path command 2>/dev/null || true
                gsettings reset org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path binding 2>/dev/null || true

                echo "✓ Keyboard shortcut removed"
                break
            fi
        fi
    done
else
    echo "⚠ gsettings not found - skipping keyboard shortcut removal"
fi
echo ""

# Ask about config
if [ "$NON_INTERACTIVE" = false ]; then
    read -p "Remove configuration and layouts? (y/N) " -n 1 -r
    echo
    REMOVE_CONFIG=$REPLY
else
    REMOVE_CONFIG="n"
fi

if [[ $REMOVE_CONFIG =~ ^[Yy]$ ]]; then
    rm -rf "$CONFIG_DIR"
    echo "✓ Configuration removed"
else
    echo "Configuration kept at $CONFIG_DIR"
fi
echo ""

# Ask about venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/venv" ]; then
    if [ "$NON_INTERACTIVE" = false ]; then
        read -p "Remove Python virtual environment? (y/N) " -n 1 -r
        echo
        REMOVE_VENV=$REPLY
    else
        REMOVE_VENV="n"
    fi

    if [[ $REMOVE_VENV =~ ^[Yy]$ ]]; then
        rm -rf "$SCRIPT_DIR/venv"
        echo "✓ Virtual environment removed"
    else
        echo "Virtual environment kept"
    fi
fi
echo ""

echo "========================================="
echo "Uninstallation Complete!"
echo "========================================="
echo ""
echo "SnapZones has been removed from your system."
echo ""
