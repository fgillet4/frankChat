#!/bin/bash

echo "Setting up FrankChat..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR"

ln -sf "$SCRIPT_DIR/frank" "$BIN_DIR/frankChat"
chmod +x "$SCRIPT_DIR/frank"

echo ""
echo "FrankChat installed!"
echo "You can now type 'frankChat' from anywhere."
echo ""
echo "Note: Make sure dependencies are installed:"
echo "  pip install -r $SCRIPT_DIR/requirements.txt"
echo ""
