#!/usr/bin/env python3
import asyncio
import json
import socket
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, TextArea
from textual.binding import Binding


CONFIG_DIR = Path.home() / ".frankchat"
CONFIG_DIR.mkdir(exist_ok=True)
PRIVATE_KEY_FILE = CONFIG_DIR / "private_key.pem"
PUBLIC_KEY_FILE = CONFIG_DIR / "public_key.pem"
CONTACTS_FILE = CONFIG_DIR / "contacts.json"

DEFAULT_PORT = 5555


def find_available_port(start_port=5555, max_attempts=10):
    for port in range(start_port, start_port + max_attempts):
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.bind(('0.0.0.0', port))
            test_sock.close()
            return port
        except OSError:
            continue
    return start_port


class CryptoManager:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.peer_keys = {}
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
            with open(PRIVATE_KEY_FILE, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            with open(PUBLIC_KEY_FILE, "rb") as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(), backend=default_backend()
                )
        else:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            
            with open(PRIVATE_KEY_FILE, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(PUBLIC_KEY_FILE, "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
    
    def get_public_key_pem(self):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def add_peer_key(self, peer_id, public_key_pem):
        self.peer_keys[peer_id] = serialization.load_pem_public_key(
            public_key_pem.encode(), backend=default_backend()
        )
    
    def encrypt(self, peer_id, message):
        if peer_id not in self.peer_keys:
            return message.encode()
        return self.peer_keys[peer_id].encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt(self, ciphertext):
        try:
            return self.private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode()
        except:
            return ciphertext.decode()


class ContactManager:
    def __init__(self):
        self.contacts = {}
        self._load_contacts()
    
    def _load_contacts(self):
        if CONTACTS_FILE.exists():
            with open(CONTACTS_FILE, "r") as f:
                self.contacts = json.load(f)
    
    def _save_contacts(self):
        with open(CONTACTS_FILE, "w") as f:
            json.dump(self.contacts, f, indent=2)
    
    def add_contact(self, name, host, port=DEFAULT_PORT):
        self.contacts[name] = {"host": host, "port": port}
        self._save_contacts()
    
    def get_contact(self, name):
        return self.contacts.get(name)
    
    def list_contacts(self):
        return list(self.contacts.keys())


class ChatProtocol(asyncio.Protocol):
    def __init__(self, app, crypto_manager):
        self.app = app
        self.crypto = crypto_manager
        self.transport = None
        self.peer_name = None
    
    def connection_made(self, transport):
        self.transport = transport
        self.app.call_from_thread(self.app.on_connection, self)
    
    def data_received(self, data):
        try:
            msg = json.loads(data.decode())
            if msg["type"] == "hello":
                self.peer_name = msg["name"]
                self.crypto.add_peer_key(self.peer_name, msg["public_key"])
                self.app.call_from_thread(self.app.log_message, f"* {self.peer_name} connected", "yellow")
            elif msg["type"] == "message":
                decrypted = self.crypto.decrypt(bytes.fromhex(msg["content"]))
                self.app.call_from_thread(self.app.log_message, f"{self.peer_name}: {decrypted}", "cyan")
        except Exception as e:
            pass
    
    def connection_lost(self, exc):
        if self.peer_name:
            self.app.call_from_thread(self.app.log_message, f"* {self.peer_name} disconnected", "yellow")


class FrankChat(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #chat-log {
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    
    #input-container {
        height: auto;
        background: $panel;
        padding: 1;
    }
    
    Input {
        width: 100%;
        height: 3;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.crypto = CryptoManager()
        self.contacts = ContactManager()
        self.username = socket.gethostname()
        self.connections = {}
        self.server = None
        self.current_chat = None
        self.port = find_available_port(DEFAULT_PORT)
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield TextArea(id="chat-log", read_only=True)
        with Container(id="input-container"):
            yield Input(placeholder="Type /add name ip, /chat name, or message...", id="message-input")
        yield Footer()
    
    async def on_mount(self):
        self.chat_log = self.query_one("#chat-log", TextArea)
        self.message_input = self.query_one("#message-input", Input)
        
        await self._start_server()
        self.log_message(f"FrankChat - {self.username}")
        self.log_message(f"Listening on port {self.port}")
        self.log_message(f"Commands: /add <name> <ip> [port], /chat <name>, /list")
        self.log_message("")
    
    async def _start_server(self):
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            lambda: ChatProtocol(self, self.crypto),
            "0.0.0.0",
            self.port
        )
    
    def on_connection(self, protocol):
        hello_msg = json.dumps({
            "type": "hello",
            "name": self.username,
            "public_key": self.crypto.get_public_key_pem()
        })
        protocol.transport.write(hello_msg.encode())
    
    def log_message(self, text, style=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.chat_log.text
        if current_text:
            self.chat_log.text = f"{current_text}\n[{timestamp}] {text}"
        else:
            self.chat_log.text = f"[{timestamp}] {text}"
        self.chat_log.scroll_end(animate=False)
    
    async def _connect_to_buddy(self, contact_name):
        contact = self.contacts.get_contact(contact_name)
        if not contact:
            self.log_message(f"Contact '{contact_name}' not found. Use /add first", "red")
            return
        
        if contact_name in self.connections:
            self.current_chat = contact_name
            self.log_message(f"Now chatting with {contact_name}", "green")
            return
        
        try:
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_connection(
                lambda: ChatProtocol(self, self.crypto),
                contact["host"],
                contact["port"]
            )
            self.connections[contact_name] = protocol
            self.current_chat = contact_name
            
            hello_msg = json.dumps({
                "type": "hello",
                "name": self.username,
                "public_key": self.crypto.get_public_key_pem()
            })
            transport.write(hello_msg.encode())
            self.log_message(f"Connected to {contact_name}", "green")
        except Exception as e:
            self.log_message(f"Failed to connect to {contact_name}: {e}", "red")
    
    async def on_input_submitted(self, event: Input.Submitted):
        message = event.value.strip()
        if not message:
            return
        
        if message.startswith("/add "):
            parts = message.split()
            if len(parts) >= 3:
                name, host = parts[1], parts[2]
                port = int(parts[3]) if len(parts) == 4 else DEFAULT_PORT
                self.contacts.add_contact(name, host, port)
                self.log_message(f"Added {name} ({host}:{port})", "green")
            else:
                self.log_message("Usage: /add <name> <host> [port]", "red")
        
        elif message.startswith("/chat "):
            parts = message.split()
            if len(parts) == 2:
                await self._connect_to_buddy(parts[1])
            else:
                self.log_message("Usage: /chat <name>", "red")
        
        elif message == "/list":
            contacts = self.contacts.list_contacts()
            if contacts:
                self.log_message("Contacts:", "cyan")
                for c in contacts:
                    status = "online" if c in self.connections else "offline"
                    self.log_message(f"  - {c} ({status})", "dim")
            else:
                self.log_message("No contacts. Use /add <name> <ip>", "dim")
        
        elif self.current_chat and self.current_chat in self.connections:
            protocol = self.connections[self.current_chat]
            encrypted = self.crypto.encrypt(self.current_chat, message)
            msg = json.dumps({
                "type": "message",
                "content": encrypted.hex()
            })
            protocol.transport.write(msg.encode())
            self.log_message(f"{self.username}: {message}", "green")
        
        else:
            self.log_message("Use /chat <name> to start chatting or /add <name> <ip> to add contact", "yellow")
        
        self.message_input.value = ""
    
    async def on_unmount(self):
        if self.server:
            self.server.close()


if __name__ == "__main__":
    app = FrankChat()
    app.run()
