import asyncio
import websockets
import json
import threading
from ...memory import NexusMemory

# A WebSocket server that pushes memory updates to clients.
# It polls the memory (or orchestrator triggers it).
# For simplicity, we poll or rely on client "pull" maybe?
# Prompt says: "React Hook useNexus() that subscribes to this socket"
# So push is better.

class NexusWebServer:
    def __init__(self, port=3000):
        self.port = port
        self.memory = NexusMemory(create=False) # Attach
        self.clients = set()
        self.last_state_hash = 0

    async def register(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def broadcast(self):
        while True:
            # Poll for changes
            data = self.memory.read()
            current_hash = hash(data) 
            
            if current_hash != self.last_state_hash:
                self.last_state_hash = current_hash
                msg = data.decode('utf-8', errors='ignore')
                if self.clients:
                    # Broadcast
                    await asyncio.gather(*[client.send(msg) for client in self.clients], return_exceptions=True)
            
            await asyncio.sleep(0.1) # 10Hz sync

    async def main(self):
        print(f"[NEXUS-WEB] Socket Server starting on port {self.port}")
        async with websockets.serve(self.register, "localhost", self.port):
            await self.broadcast()

    def run_threaded(self):
        def start_loop():
            asyncio.run(self.main())
        t = threading.Thread(target=start_loop, daemon=True)
        t.start()
