# FrankChat

A secure, private terminal-based chat application for local network communication with an AIM-style interface.

## Features

- 🔒 End-to-end encryption using RSA
- 💬 Clean AIM-style TUI interface
- 🌐 Peer-to-peer communication
- 👥 Buddy list management
- 🔐 Automatic key generation and management
- 📱 Real-time messaging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start the chat application:

```bash
python chat.py
```

### Add a buddy:

1. Press `Ctrl+A` or type in the input:
```
/add <name> <ip-address>
```

Example:
```
/add laptop 192.168.1.100
```

### Chat with a buddy:

1. Click or select a buddy from the list on the left
2. Type your message and press Enter

### Keyboard shortcuts:

- `Ctrl+Q` - Quit
- `Ctrl+A` - Add buddy prompt

## How it works

- Each computer runs the chat application on port 5555
- RSA keys are automatically generated on first run (stored in `~/.frankchat/`)
- Messages are encrypted with the recipient's public key
- Contacts are saved locally in `~/.frankchat/contacts.json`

## Find your IP address:

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

## Security

- All messages are encrypted end-to-end using RSA-2048
- Keys are generated locally and never transmitted in plaintext
- Only works on local networks (not exposed to internet)
