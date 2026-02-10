#!/usr/bin/env python3
"""
Generate shared encryption key for FrankChat
Run this once, then copy .chat_key to all devices
"""
from cryptography.fernet import Fernet
from pathlib import Path

KEY_FILE = Path(__file__).parent / ".chat_key"

if KEY_FILE.exists():
    print(f"Key already exists at {KEY_FILE}")
    response = input("Overwrite? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        exit(0)

key = Fernet.generate_key()

with open(KEY_FILE, 'wb') as f:
    f.write(key)

KEY_FILE.chmod(0o600)

print(f"✓ Encryption key generated: {KEY_FILE}")
print(f"\nKey (base64): {key.decode()}")
print(f"\nCopy this file to all devices:")
print(f"  scp {KEY_FILE} frank-local:~/frankChat/")
print(f"  scp {KEY_FILE} pc-local:~/frankChat/")
print(f"  scp {KEY_FILE} powerpi-local:~/frankChat/")
print(f"\nOr share the key manually and create .chat_key on each device")
