#!/bin/bash
# SnapZones Installation Script

set -e

# Parse arguments
NON_INTERACTIVE=false
if [[ "$1" == "-y" ]] || [[ "$1" == "--yes" ]]; then
    NON_INTERACTIVE=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local"
BIN_DIR="$INSTALL_DIR/bin"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "========================================="
echo "SnapZones Installation"
echo "========================================="
echo ""

# Check if running on X11
if [ -z "$DISPLAY" ]; then
    echo "ERROR: DISPLAY variable not set. SnapZones requires X11."
    exit 1
fi

if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "WARNING: Wayland detected. SnapZones requires X11 to function properly."
    echo "Please log out and select an X11 session instead."
    if [ "$NON_INTERACTIVE" = false ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "Running in non-interactive mode - continuing anyway"
    fi
fi

# Check for system dependencies
echo "Checking system dependencies..."
MISSING_DEPS=()

for pkg in python3-gi python3-gi-cairo gir1.2-gtk-3.0 libcairo2-dev python3-xlib libx11-dev python3-dev; do
    if ! dpkg -l | grep -q "^ii  $pkg"; then
        MISSING_DEPS+=($pkg)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "Missing system packages: ${MISSING_DEPS[@]}"
    echo ""
    echo "Install with:"
    echo "  sudo apt install ${MISSING_DEPS[@]}"
    echo ""
    if [ "$NON_INTERACTIVE" = true ]; then
        echo "Please install missing dependencies and run this script again."
        exit 1
    fi
    read -p "Install now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt install -y "${MISSING_DEPS[@]}"
    else
        echo "Please install missing dependencies and run this script again."
        exit 1
    fi
fi

echo "✓ System dependencies satisfied"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✓ Python dependencies installed"
echo ""

# Create installation directories
echo "Setting up installation directories..."
mkdir -p "$BIN_DIR"
mkdir -p "$AUTOSTART_DIR"
mkdir -p "$HOME/.config/snapzones/layouts"

echo "✓ Directories created"
echo ""

# Install entry point scripts
echo "Installing SnapZones scripts..."

# Create wrapper scripts that activate venv and run the actual scripts
cat > "$BIN_DIR/snapzones" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/src:\$PYTHONPATH"
exec python3 -m snap_zones.daemon "\$@"
EOF

cat > "$BIN_DIR/snapzones-editor" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/src:\$PYTHONPATH"
exec python3 -m snap_zones.zone_editor "\$@"
EOF

# Copy status script
cp "$SCRIPT_DIR/bin/snapzones-status" "$BIN_DIR/snapzones-status"

chmod +x "$BIN_DIR/snapzones"
chmod +x "$BIN_DIR/snapzones-editor"
chmod +x "$BIN_DIR/snapzones-status"

echo "✓ Scripts installed to $BIN_DIR"
echo ""

# Install autostart desktop file
echo "Setting up autostart..."
sed "s|Exec=.*|Exec=$BIN_DIR/snapzones|g" "$SCRIPT_DIR/snapzones.desktop" > "$AUTOSTART_DIR/snapzones.desktop"
chmod +x "$AUTOSTART_DIR/snapzones.desktop"

echo "✓ Autostart configured"
echo ""

# Register native GNOME keyboard shortcut
echo "Registering keyboard shortcut (Super+Shift+Tab)..."

# Function to register GNOME custom keybinding
register_gnome_shortcut() {
    local name="SnapZones Editor"
    local command="$BIN_DIR/snapzones-editor"
    local binding="<Super><Shift>Tab"

    # Get current custom keybindings list
    current_bindings=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)

    # Find next available custom keybinding slot
    slot_num=0
    while true; do
        slot_path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${slot_num}/"
        # Check if this slot exists in current bindings
        if echo "$current_bindings" | grep -q "$slot_path"; then
            ((slot_num++))
        else
            break
        fi
    done

    # Add our new slot to the list using Python to safely handle the array
    new_bindings=$(python3 << EOF
import sys
current = """$current_bindings"""
slot = """$slot_path"""

# Parse the current bindings (it's a GVariant array string)
if current in ["@as []", "[]"]:
    print(f"['{slot}']")
else:
    # Remove brackets and split by comma
    items = current.strip("[]").split(",")
    items = [item.strip().strip("'\"") for item in items if item.strip()]
    items.append(slot)
    # Format back
    formatted = ", ".join(f"'{item}'" for item in items)
    print(f"[{formatted}]")
EOF
)

    # Set the new bindings list
    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$new_bindings"

    # Set our keybinding properties
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path name "$name"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path command "$command"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$slot_path binding "$binding"

    echo "✓ Keyboard shortcut registered: Super+Shift+Tab → snapzones-editor"
}

# Only register if gsettings is available (GNOME/Pop!_OS)
if command -v gsettings &> /dev/null; then
    register_gnome_shortcut
else
    echo "⚠ gsettings not found - keyboard shortcut not registered"
    echo "  You can manually add a shortcut in System Settings → Keyboard"
    echo "  Command: $BIN_DIR/snapzones-editor"
    echo "  Shortcut: Super+Shift+Tab"
fi

echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "WARNING: $HOME/.local/bin is not in your PATH"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Create default layout if none exists
if [ ! -f "$HOME/.config/snapzones/layouts/default.json" ]; then
    echo "Creating default layout..."
    cat > "$HOME/.config/snapzones/layouts/default.json" << 'EOF'
{
  "name": "default",
  "description": "Default empty layout",
  "zones": [],
  "created": "2025-10-08",
  "modified": "2025-10-08"
}
EOF
    echo "✓ Default layout created"
    echo ""
fi

echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "SnapZones has been installed successfully."
echo ""
echo "Usage:"
echo "  snapzones              - Start background daemon"
echo "  snapzones-editor       - Open zone editor"
echo "  snapzones-status       - Check daemon status / manage daemon"
echo ""
echo "Default shortcuts:"
echo "  Alt + Drag Window      - Show zone overlay and snap"
echo "  Super+Shift+Tab        - Open zone editor"
echo ""
echo "The daemon will start automatically on next login."
echo ""

if [ "$NON_INTERACTIVE" = false ]; then
    read -p "Start SnapZones daemon now? (Y/n) " -n 1 -r
    echo
    START_DAEMON=$REPLY
else
    START_DAEMON="n"
fi

if [[ ! $START_DAEMON =~ ^[Nn]$ ]]; then
    echo "Starting daemon..."
    nohup "$BIN_DIR/snapzones" > /tmp/snapzones.log 2>&1 &
    echo "✓ Daemon started (PID: $!)"
    echo "  Logs: /tmp/snapzones.log"
    echo ""
    echo "Press Super+Shift+Tab to open the zone editor and create your first layout!"
else
    echo "Run 'snapzones' to start the daemon manually."
fi

echo ""
echo "Enjoy SnapZones! 🎯"
