import json
import asyncio
from typing import List
from fastapi import WebSocket

class WebSocketHub:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WS] Client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                stale_connections.append(connection)
                
        for stale in stale_connections:
            self.disconnect(stale)

ws_hub = WebSocketHub()
