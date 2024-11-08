# app/websocket_manager.py

import asyncio
from fastapi import WebSocket
from typing import List, Dict

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id].remove(websocket)

    async def send_notification(self, user_id: int, message: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def keep_alive(self, interval: int = 30):
        """
        Sends a "ping" to all connected users periodically to keep the WebSocket connection alive.
        :param interval: The time in seconds between pings.
        """
        while True:
            for user_id, connections in self.active_connections.items():
                for connection in connections:
                    try:
                        # Send a ping message to keep the connection alive
                        await connection.send_text("ping")
                    except:
                        # If connection fails (e.g., disconnected client), remove it
                        self.disconnect(connection, user_id)
            await asyncio.sleep(interval)

# Global instance of WebSocketManager
manager = WebSocketManager()


