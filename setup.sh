#!/bin/bash
set -e

echo "=== FrankChat Setup ==="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 9 ]; then
    echo "Error: Python 3.9+ required."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create and activate virtualenv
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Install the 'frank' CLI shortcut
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$SCRIPT_DIR/frank" "$BIN_DIR/frank"
chmod +x "$SCRIPT_DIR/frank"

# Add ~/.local/bin to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    [[ "$SHELL" == */zsh ]] && SHELL_RC="$HOME/.zshrc"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
    echo "Added $BIN_DIR to PATH in $SHELL_RC"
    echo "Run: source $SHELL_RC  (or open a new terminal)"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Start the chat:"
echo "  frank"
echo "  # or: python3 $SCRIPT_DIR/chat.py"
echo ""
echo "In the chat, connect to someone:"
echo "  /add <name> <their-ip>    # e.g. /add alice 192.168.1.50"
echo "  /chat <name>              # start chatting"
echo "  /list                     # see all contacts"
echo ""
echo "To find your IP:  hostname -I | awk '{print \$1}'"
echo ""
