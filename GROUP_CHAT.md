# Group Chat Setup

## Quick Start

**1. Pick one computer to be the server** (e.g., your Mac Mini):

```bash
python3 server.py
```

Note the IP address shown.

**2. On all other computers** (laptop, PC, Pi), connect as clients:

```bash
python3 client.py <server-ip>
```

Example:
```bash
python3 client.py 192.168.1.100
```

**With custom username:**
```bash
python3 client.py 192.168.1.100 5555 MyLaptop
```

## Commands

- `/users` - Show who's online
- `Ctrl+Q` - Quit

## Example Setup

**Mac Mini (server):**
```bash
cd ~/frankChat
python3 server.py
# Shows: Server started on 192.168.1.100:5555
```

**MacBook:**
```bash
cd ~/frankChat
python3 client.py 192.168.1.100 5555 MacBook
```

**PC:**
```bash
cd frankChat
python client.py 192.168.1.100 5555 PC
```

**Raspberry Pi:**
```bash
cd ~/frankChat
python3 client.py 192.168.1.100 5555 Pi
```

Now everyone can chat together in the same room!

## Custom Port

If port 5555 is in use:

**Server:**
```bash
python3 server.py 5556
```

**Clients:**
```bash
python3 client.py 192.168.1.100 5556 MyName
```

## Features

- Multi-user group chat
- Shows when users join/leave
- Real-time messaging
- Text selection and copy/paste support
- Clean AIM-style interface
