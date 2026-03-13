#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime


DEFAULT_PORT = 5555


class ChatServer:
    def __init__(self, port=DEFAULT_PORT):
        self.port = port
        self.clients = {}
        self.server = None
    
    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )
        addr = self.server.sockets[0].getsockname()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] FrankChat Server started on {addr[0]}:{addr[1]}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for clients...")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_name = None
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    msg = json.loads(data.decode())
                    
                    if msg["type"] == "join":
                        client_name = msg["name"]
                        self.clients[client_name] = writer
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {client_name} joined from {addr}")
                        await self.broadcast({
                            "type": "system",
                            "message": f"{client_name} joined the chat"
                        }, exclude=client_name)
                        
                        user_list = list(self.clients.keys())
                        response = json.dumps({
                            "type": "user_list",
                            "users": user_list
                        })
                        writer.write(response.encode() + b'\n')
                        await writer.drain()
                    
                    elif msg["type"] == "message":
                        if client_name:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] {client_name}: {msg['content']}")
                            await self.broadcast({
                                "type": "message",
                                "sender": client_name,
                                "content": msg["content"]
                            })
                
                except json.JSONDecodeError:
                    pass
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error with {client_name or addr}: {e}")
        finally:
            if client_name and client_name in self.clients:
                del self.clients[client_name]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {client_name} left")
                await self.broadcast({
                    "type": "system",
                    "message": f"{client_name} left the chat"
                })
            writer.close()
            await writer.wait_closed()
    
    async def broadcast(self, message, exclude=None):
        msg_data = json.dumps(message).encode()
        dead_clients = []
        
        for name, writer in self.clients.items():
            if name != exclude:
                try:
                    writer.write(msg_data + b'\n')
                    await writer.drain()
                except:
                    dead_clients.append(name)
        
        for name in dead_clients:
            if name in self.clients:
                del self.clients[name]


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    
    server = ChatServer(port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Server shutting down...")
