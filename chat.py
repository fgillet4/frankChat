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
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.reactive import reactive


CONFIG_DIR = Path.home() / ".frankchat"
CONFIG_DIR.mkdir(exist_ok=True)
PRIVATE_KEY_FILE = CONFIG_DIR / "private_key.pem"
PUBLIC_KEY_FILE = CONFIG_DIR / "public_key.pem"
CONTACTS_FILE = CONFIG_DIR / "contacts.json"

DEFAULT_PORT = 5555
DISCOVERY_PORT = 5556


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
                self.app.call_from_thread(self.app.add_system_message, f"{self.peer_name} connected")
            elif msg["type"] == "message":
                decrypted = self.crypto.decrypt(msg["content"])
                self.app.call_from_thread(self.app.add_message, self.peer_name, decrypted)
        except Exception as e:
            pass
    
    def connection_lost(self, exc):
        if self.peer_name:
            self.app.call_from_thread(self.app.add_system_message, f"{self.peer_name} disconnected")


class MessageDisplay(Static):
    pass


class BuddyList(ListView):
    pass


class FrankChat(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #sidebar {
        width: 25;
        background: $panel;
        border-right: solid $primary;
    }
    
    #main {
        width: 1fr;
    }
    
    #messages {
        height: 1fr;
        overflow-y: auto;
        background: $surface;
        padding: 1;
    }
    
    #input-container {
        height: auto;
        background: $panel;
        padding: 1;
    }
    
    Input {
        width: 100%;
    }
    
    .message {
        margin: 1 0;
    }
    
    .message-sender {
        color: $accent;
        text-style: bold;
    }
    
    .message-self {
        color: $success;
    }
    
    .message-system {
        color: $warning;
        text-style: italic;
    }
    
    BuddyList {
        height: 1fr;
    }
    
    ListItem {
        padding: 1;
    }
    
    #status {
        height: 3;
        background: $panel;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+a", "add_buddy", "Add Buddy"),
    ]
    
    def __init__(self):
        super().__init__()
        self.crypto = CryptoManager()
        self.contacts = ContactManager()
        self.username = socket.gethostname()
        self.connections = {}
        self.server = None
        self.current_chat = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label(f"[b]FrankChat[/b]\n{self.username}", id="status")
                yield BuddyList(id="buddy-list")
            with Vertical(id="main"):
                yield Container(id="messages")
                with Container(id="input-container"):
                    yield Input(placeholder="Type a message...", id="message-input")
        yield Footer()
    
    async def on_mount(self):
        self.messages_container = self.query_one("#messages", Container)
        self.message_input = self.query_one("#message-input", Input)
        self.buddy_list = self.query_one("#buddy-list", BuddyList)
        
        await self._start_server()
        self._update_buddy_list()
        self.add_system_message(f"Listening on port {DEFAULT_PORT}")
        self.add_system_message(f"Your computer: {self.username}")
    
    async def _start_server(self):
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            lambda: ChatProtocol(self, self.crypto),
            "0.0.0.0",
            DEFAULT_PORT
        )
    
    def _update_buddy_list(self):
        self.buddy_list.clear()
        for contact in self.contacts.list_contacts():
            self.buddy_list.append(ListItem(Label(f"[cyan]{contact}[/cyan]")))
    
    def on_connection(self, protocol):
        hello_msg = json.dumps({
            "type": "hello",
            "name": self.username,
            "public_key": self.crypto.get_public_key_pem()
        })
        protocol.transport.write(hello_msg.encode())
    
    def add_system_message(self, text):
        timestamp = datetime.now().strftime("%H:%M")
        msg = Static(f"[dim]{timestamp}[/dim] [yellow]* {text}[/yellow]", classes="message message-system")
        self.messages_container.mount(msg)
        self.messages_container.scroll_end(animate=False)
    
    def add_message(self, sender, text):
        timestamp = datetime.now().strftime("%H:%M")
        msg = Static(
            f"[dim]{timestamp}[/dim] [cyan]{sender}:[/cyan] {text}",
            classes="message"
        )
        self.messages_container.mount(msg)
        self.messages_container.scroll_end(animate=False)
    
    def add_self_message(self, text):
        timestamp = datetime.now().strftime("%H:%M")
        msg = Static(
            f"[dim]{timestamp}[/dim] [green]{self.username}:[/green] {text}",
            classes="message message-self"
        )
        self.messages_container.mount(msg)
        self.messages_container.scroll_end(animate=False)
    
    async def on_list_view_selected(self, event: ListView.Selected):
        contact_name = event.item.children[0].renderable.plain.strip()
        await self._connect_to_buddy(contact_name)
    
    async def _connect_to_buddy(self, contact_name):
        contact = self.contacts.get_contact(contact_name)
        if not contact:
            return
        
        if contact_name in self.connections:
            self.current_chat = contact_name
            self.add_system_message(f"Chatting with {contact_name}")
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
        except Exception as e:
            self.add_system_message(f"Failed to connect to {contact_name}")
    
    async def on_input_submitted(self, event: Input.Submitted):
        message = event.value.strip()
        if not message:
            return
        
        if message.startswith("/add "):
            parts = message.split()
            if len(parts) == 3:
                name, host = parts[1], parts[2]
                self.contacts.add_contact(name, host)
                self._update_buddy_list()
                self.add_system_message(f"Added {name} ({host})")
            else:
                self.add_system_message("Usage: /add <name> <host>")
        elif self.current_chat and self.current_chat in self.connections:
            protocol = self.connections[self.current_chat]
            encrypted = self.crypto.encrypt(self.current_chat, message)
            msg = json.dumps({
                "type": "message",
                "content": encrypted.hex()
            })
            protocol.transport.write(msg.encode())
            self.add_self_message(message)
        else:
            self.add_system_message("Select a buddy first or use /add <name> <host>")
        
        self.message_input.value = ""
    
    def action_add_buddy(self):
        self.add_system_message("Type: /add <name> <ip-address>")
        self.message_input.focus()
    
    async def on_unmount(self):
        if self.server:
            self.server.close()


if __name__ == "__main__":
    app = FrankChat()
    app.run()
