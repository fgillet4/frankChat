#!/usr/bin/env python3
import asyncio
import json
import socket
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input, TextArea
from textual.binding import Binding


CONFIG_FILE = Path(__file__).parent / "config.json"


class GroupChatClient(App):
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
        Binding("ctrl+c", "copy_mode", "Copy Mode", show=False),
    ]
    
    def __init__(self, server_ip, server_port=5555, username=None):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username or socket.gethostname()
        self.reader = None
        self.writer = None
        self.users = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield TextArea(id="chat-log", read_only=False, show_line_numbers=False)
        with Container(id="input-container"):
            yield Input(placeholder="Type your message... (Ctrl+C in chat to copy)", id="message-input")
        yield Footer()
    
    async def on_mount(self):
        self.chat_log = self.query_one("#chat-log", TextArea)
        self.message_input = self.query_one("#message-input", Input)
        self.message_input.focus()
        
        self.log_message(f"=== FrankChat Group ===")
        self.log_message(f"Username: {self.username}")
        self.log_message(f"Connecting to {self.server_ip}:{self.server_port}...")
        self.log_message("")
        
        await self.connect_to_server()
    
    async def connect_to_server(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.server_ip, self.server_port
            )
            
            join_msg = json.dumps({
                "type": "join",
                "name": self.username
            })
            self.writer.write(join_msg.encode())
            await self.writer.drain()
            
            self.log_message("Connected to server!")
            self.log_message("")
            
            asyncio.create_task(self.receive_messages())
        
        except Exception as e:
            self.log_message(f"Failed to connect: {e}")
            self.log_message("Press Ctrl+Q to quit")
    
    async def receive_messages(self):
        try:
            while True:
                data = await self.reader.read(4096)
                if not data:
                    break
                
                try:
                    msg = json.loads(data.decode())
                    
                    if msg["type"] == "message":
                        sender = msg["sender"]
                        content = msg["content"]
                        self.log_message(f"{sender}: {content}")
                    
                    elif msg["type"] == "system":
                        self.log_message(f"* {msg['message']}")
                    
                    elif msg["type"] == "user_list":
                        self.users = msg["users"]
                        self.log_message(f"Users online: {', '.join(self.users)}")
                
                except json.JSONDecodeError:
                    pass
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log_message(f"Connection lost: {e}")
    
    def log_message(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.chat_log.text
        if current_text:
            self.chat_log.text = f"{current_text}\n[{timestamp}] {text}"
        else:
            self.chat_log.text = f"[{timestamp}] {text}"
        self.chat_log.scroll_end(animate=False)
    
    async def on_input_submitted(self, event: Input.Submitted):
        message = event.value.strip()
        if not message:
            return
        
        if message == "/users":
            self.log_message(f"Users online: {', '.join(self.users)}")
        elif self.writer:
            msg = json.dumps({
                "type": "message",
                "content": message
            })
            try:
                self.writer.write(msg.encode())
                await self.writer.drain()
            except Exception as e:
                self.log_message(f"Failed to send: {e}")
        
        self.message_input.value = ""
    
    def action_copy_mode(self):
        self.chat_log.focus()
    
    async def on_unmount(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    import sys
    
    config = load_config()
    
    if len(sys.argv) >= 2:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
        username = sys.argv[3] if len(sys.argv) > 3 else None
    elif config.get("server_ip"):
        server_ip = config["server_ip"]
        server_port = config.get("server_port", 5555)
        username = config.get("username") or None
        print(f"Using config: {server_ip}:{server_port}")
    else:
        print("Usage: python client.py <server-ip> [port] [username]")
        print("   OR: Edit config.json with server details")
        print("")
        print("Example: python client.py 192.168.1.100")
        print("Example: python client.py 192.168.1.100 5555 MacMini")
        sys.exit(1)
    
    app = GroupChatClient(server_ip, server_port, username)
    app.run()
