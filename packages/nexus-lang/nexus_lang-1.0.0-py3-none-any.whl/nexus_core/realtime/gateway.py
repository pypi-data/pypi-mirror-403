"""
Nexus WebSocket Gateway
Real-time bidirectional communication with browser clients.
"""

import asyncio
import json
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
import threading
import time

from .events import EventBus, EventType, NexusEvent, get_event_bus, MemoryWatcher
from .pubsub import PubSub, Message, get_pubsub


@dataclass
class Client:
    """Represents a connected WebSocket client."""
    websocket: WebSocket
    client_id: str
    subscriptions: Set[str]
    connected_at: float
    
    async def send(self, data: dict) -> bool:
        """Send data to client. Returns False if failed."""
        try:
            await self.websocket.send_json(data)
            return True
        except:
            return False


class WebSocketGateway:
    """
    WebSocket gateway for real-time communication.
    
    Features:
    - Auto-assigns client IDs
    - Channel subscriptions
    - State sync on connect
    - Heartbeat/ping-pong
    - Broadcast to all or filtered clients
    """
    
    def __init__(self, app: FastAPI = None):
        self.app = app or FastAPI(title="Nexus Gateway")
        self.clients: Dict[str, Client] = {}
        self.event_bus = get_event_bus()
        self.pubsub = get_pubsub()
        self._client_counter = 0
        self._lock = threading.Lock()
        self._memory_watcher: Optional[MemoryWatcher] = None
        
        # Setup routes
        self._setup_routes()
        
        # Subscribe to events
        self.event_bus.subscribe_all(self._on_event)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            return self._get_dashboard_html()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, client_id: str = Query(None)):
            await self._handle_connection(websocket, client_id)
        
        @self.app.get("/api/clients")
        async def get_clients():
            return {
                "count": len(self.clients),
                "clients": [
                    {
                        "id": c.client_id,
                        "subscriptions": list(c.subscriptions),
                        "connected_at": c.connected_at
                    }
                    for c in self.clients.values()
                ]
            }
        
        @self.app.get("/api/state")
        async def get_state():
            from nexus_core import NexusMemory
            try:
                mem = NexusMemory(create=False)
                data = mem.read().decode('utf-8')
                mem.close()
                return json.loads(data)
            except:
                return {}
        
        @self.app.post("/api/broadcast")
        async def broadcast(channel: str, message: dict):
            count = await self.broadcast(channel, message)
            return {"sent_to": count}
    
    async def _handle_connection(self, websocket: WebSocket, client_id: str = None):
        """Handle a new WebSocket connection."""
        await websocket.accept()
        
        # Generate client ID
        with self._lock:
            self._client_counter += 1
            if not client_id:
                client_id = f"client_{self._client_counter}"
        
        client = Client(
            websocket=websocket,
            client_id=client_id,
            subscriptions=set(["state"]),  # Default subscription
            connected_at=time.time()
        )
        self.clients[client_id] = client
        
        # Send welcome message with current state
        try:
            from nexus_core import NexusMemory
            mem = NexusMemory(create=False)
            state = mem.read().decode('utf-8')
            mem.close()
        except:
            state = "{}"
        
        await client.send({
            "type": "welcome",
            "client_id": client_id,
            "state": json.loads(state),
            "timestamp": time.time()
        })
        
        print(f"[GATEWAY] Client connected: {client_id}")
        
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(client, data)
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[GATEWAY] Client error: {e}")
        finally:
            del self.clients[client_id]
            print(f"[GATEWAY] Client disconnected: {client_id}")
    
    async def _handle_message(self, client: Client, data: dict):
        """Handle incoming message from client."""
        msg_type = data.get("type", "")
        
        if msg_type == "subscribe":
            channels = data.get("channels", [])
            client.subscriptions.update(channels)
            await client.send({"type": "subscribed", "channels": list(client.subscriptions)})
            
        elif msg_type == "unsubscribe":
            channels = data.get("channels", [])
            client.subscriptions.difference_update(channels)
            await client.send({"type": "unsubscribed", "channels": list(client.subscriptions)})
            
        elif msg_type == "publish":
            channel = data.get("channel", "")
            message = data.get("message", {})
            self.pubsub.publish(channel, message, sender=client.client_id)
            
        elif msg_type == "ping":
            await client.send({"type": "pong", "timestamp": time.time()})
            
        elif msg_type == "get_state":
            try:
                from nexus_core import NexusMemory
                mem = NexusMemory(create=False)
                state = json.loads(mem.read().decode('utf-8'))
                mem.close()
                await client.send({"type": "state", "data": state})
            except Exception as e:
                await client.send({"type": "error", "message": str(e)})
                
        elif msg_type == "set_state":
            try:
                from nexus_core import NexusMemory
                mem = NexusMemory(create=False)
                mem.write(json.dumps(data.get("data", {})).encode())
                mem.close()
                await client.send({"type": "state_updated"})
            except Exception as e:
                await client.send({"type": "error", "message": str(e)})
    
    def _on_event(self, event: NexusEvent):
        """Handle events from the event bus."""
        asyncio.create_task(self._broadcast_event(event))
    
    async def _broadcast_event(self, event: NexusEvent):
        """Broadcast an event to subscribed clients."""
        channel = event.type.value
        data = {
            "type": "event",
            "event": event.to_dict()
        }
        
        for client in list(self.clients.values()):
            if channel in client.subscriptions or "state" in client.subscriptions:
                await client.send(data)
    
    async def broadcast(self, channel: str, message: Any) -> int:
        """Broadcast a message to all clients subscribed to a channel."""
        data = {
            "type": "message",
            "channel": channel,
            "data": message,
            "timestamp": time.time()
        }
        
        count = 0
        for client in list(self.clients.values()):
            if channel in client.subscriptions or "*" in client.subscriptions:
                if await client.send(data):
                    count += 1
        
        return count
    
    def start_memory_watcher(self):
        """Start watching memory for changes."""
        if self._memory_watcher is None:
            self._memory_watcher = MemoryWatcher(self.event_bus)
            self._memory_watcher.start()
    
    def stop_memory_watcher(self):
        """Stop the memory watcher."""
        if self._memory_watcher:
            self._memory_watcher.stop()
            self._memory_watcher = None
    
    def _get_dashboard_html(self) -> str:
        """Generate the gateway dashboard HTML."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Gateway</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0a1a, #1a1a3a);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { 
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
        }
        .card h3 { color: #00ff88; margin-bottom: 15px; }
        #state, #events { 
            font-family: monospace;
            background: #000;
            padding: 15px;
            border-radius: 8px;
            max-height: 300px;
            overflow: auto;
            font-size: 12px;
        }
        .status { 
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        .connected { background: #00ff88; color: #000; }
        .disconnected { background: #ff4444; color: #fff; }
        button {
            background: #00d4ff;
            color: #000;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #00ff88; }
        input {
            background: #222;
            border: 1px solid #444;
            color: #fff;
            padding: 8px;
            border-radius: 6px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Nexus Gateway <span id="status" class="status disconnected">Disconnected</span></h1>
        
        <div class="grid">
            <div class="card">
                <h3>Current State</h3>
                <pre id="state">Loading...</pre>
                <button onclick="refreshState()">Refresh</button>
            </div>
            
            <div class="card">
                <h3>Live Events</h3>
                <pre id="events"></pre>
                <button onclick="clearEvents()">Clear</button>
            </div>
            
            <div class="card" style="grid-column: span 2;">
                <h3>Send Message</h3>
                <input id="channel" placeholder="Channel" value="test">
                <input id="message" placeholder="Message" value="Hello Nexus!">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws;
        const events = document.getElementById('events');
        const stateEl = document.getElementById('state');
        const statusEl = document.getElementById('status');
        
        function connect() {
            ws = new WebSocket(`ws://${location.host}/ws`);
            
            ws.onopen = () => {
                statusEl.textContent = 'Connected';
                statusEl.className = 'status connected';
                log('Connected to gateway');
            };
            
            ws.onclose = () => {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status disconnected';
                log('Disconnected - reconnecting in 3s...');
                setTimeout(connect, 3000);
            };
            
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                log(JSON.stringify(data, null, 2));
                
                if (data.type === 'welcome' || data.type === 'state') {
                    stateEl.textContent = JSON.stringify(data.state || data.data, null, 2);
                }
                if (data.type === 'event' && data.event.type === 'state_update') {
                    stateEl.textContent = JSON.stringify(data.event.payload, null, 2);
                }
            };
        }
        
        function log(msg) {
            const time = new Date().toLocaleTimeString();
            events.textContent = `[${time}] ${msg}\n` + events.textContent;
            if (events.textContent.length > 10000) {
                events.textContent = events.textContent.slice(0, 10000);
            }
        }
        
        function refreshState() {
            ws.send(JSON.stringify({type: 'get_state'}));
        }
        
        function clearEvents() {
            events.textContent = '';
        }
        
        function sendMessage() {
            const channel = document.getElementById('channel').value;
            const message = document.getElementById('message').value;
            ws.send(JSON.stringify({
                type: 'publish',
                channel: channel,
                message: {text: message}
            }));
        }
        
        connect();
    </script>
</body>
</html>
'''


def create_gateway(app: FastAPI = None) -> WebSocketGateway:
    """Create a new gateway instance."""
    return WebSocketGateway(app)


# Default gateway instance
_default_gateway: Optional[WebSocketGateway] = None

def get_gateway() -> WebSocketGateway:
    """Get or create the default gateway."""
    global _default_gateway
    if _default_gateway is None:
        _default_gateway = WebSocketGateway()
    return _default_gateway
