"""
WebSocket Connection Manager for Real-Time Features.
Supports live AI nudges, collaboration updates, and instant data sync.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import logging

# We need a special way to verify tokens for WebSockets since we can't easily 
# use standard Dependency Injection with Headers in standard browser WebSockets
from utils.auth_jwt import decode_token
from models.user import User
from utils.database import SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> list of active connections (for multi-device sharing)
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected.")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to all active devices/tabs of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up dead connections
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        """Send a message to absolutely everyone connected."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Standard WebSocket endpoint. 
    Clients must pass token as a query parameter: ws://localhost:8000/api/ws?token=ey...
    """
    user_id = None
    db = SessionLocal()
    try:
        # Verify the token manually
        payload = decode_token(token)
        user_email = payload.get("sub")
        if not user_email:
            await websocket.close(code=1008, reason="Invalid token")
            return
            
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
            
        user_id = user.id
        await manager.connect(websocket, user_id)
        
        # Send a welcome packet
        await manager.send_personal_message({
            "type": "system",
            "message": "Connected to Brain Real-Time sync"
        }, user_id)
        
        # Listen for messages (if client sends us anything)
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                # Handle incoming messages here (e.g., mark nudge as read)
                logger.debug(f"Received from {user_id}: {parsed}")
                
                # Echo back for testing
                await manager.send_personal_message({
                    "type": "ack",
                    "original": parsed
                }, user_id)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({"error": "Invalid JSON format"}, user_id)
                
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            manager.disconnect(websocket, user_id)
    finally:
        db.close()
