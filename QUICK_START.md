# FrankChat Quick Start

## Your Devices

- **MacMini** (frankstation): 192.168.1.70
- **MacBook** (francisbrain4-3): 192.168.1.78
- **Pi** (powerpi): 192.168.1.130
- **PC**: 192.168.1.118

## Super Easy Commands

Copy `frankChat` folder to all devices, then:

### Group Chat

**On Mac Mini (server):**
```bash
cd ~/frankChat
./frank server
```

**On all other devices:**
```bash
cd ~/frankChat
./frank group
```

### P2P Chat

**On MacBook to chat with PC:**
```bash
./frank pc
```

**On PC to chat with MacBook:**
```bash
python frank macbook
```

**From any device:**
```bash
./frank pi       # Chat with Pi
./frank macmini  # Chat with Mac Mini
./frank macbook  # Chat with MacBook
./frank pc       # Chat with PC
```

## Commands

Just run `./frank` to see options:
- `./frank group` - Join group chat
- `./frank server` - Start server
- `./frank <device>` - P2P with device

## Installation on Each Device

**Mac/Linux (MacMini, MacBook, Pi):**
```bash
cd ~/frankChat
pip3 install -r requirements.txt
chmod +x frank
```

**Windows PC:**
```bash
cd frankChat
pip install -r requirements.txt
```

Then use:
```bash
python frank group
python frank macbook
```

That's it! No IPs to remember, no complex commands.
