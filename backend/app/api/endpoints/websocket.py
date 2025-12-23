"""
WebSocket Endpoints

Real-time communication for document processing updates
Uses Redis pub/sub to receive updates from Celery workers
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import logging
import asyncio
import redis.asyncio as aioredis

from app.core.security import get_current_user_ws
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Redis client for pub/sub
redis_client: aioredis.Redis = None

async def get_redis():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

# Store active WebSocket connections per user
# Format: {user_id: {websocket1, websocket2, ...}}
active_connections: Dict[int, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections"""
    
    @staticmethod
    async def connect(websocket: WebSocket, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in active_connections:
            active_connections[user_id] = set()
        
        active_connections[user_id].add(websocket)
        logger.info(f"✅ WebSocket connected for user {user_id}. Total connections: {len(active_connections[user_id])}")
    
    @staticmethod
    def disconnect(websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not active_connections[user_id]:
                del active_connections[user_id]
            
            logger.info(f"❌ WebSocket disconnected for user {user_id}")
    
    @staticmethod
    async def send_personal_message(message: dict, user_id: int):
        """Send message to all connections of a specific user"""
        if user_id in active_connections:
            disconnected = set()
            
            for websocket in active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                active_connections[user_id].discard(ws)
    
    @staticmethod
    async def broadcast_to_user(user_id: int, event_type: str, data: dict):
        """Broadcast an event to all user's connections"""
        message = {
            "type": event_type,
            "data": data
        }
        await ConnectionManager.send_personal_message(message, user_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket endpoint for real-time updates
    
    Query parameter:
    - token: JWT access token for authentication
    
    Message format:
    {
        "type": "document_status_update",
        "data": {
            "document_id": 123,
            "status": "completed",
            "message": "Processing complete"
        }
    }
    """
    logger.info(f"🔌 WebSocket connection attempt with token: {token[:20]}...")
    
    # Authenticate user
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        user = await get_current_user_ws(token, db)
        user_id = user.id
        logger.info(f"✅ WebSocket authenticated for user {user_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    finally:
        if 'db' in locals():
            db.close()
    
    # Connect
    await manager.connect(websocket, user_id)
    
    # Start Redis subscriber in background
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"user:{user_id}:updates")
    
    async def redis_listener():
        """Listen for Redis pub/sub messages"""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                        logger.info(f"📡 Forwarded update to user {user_id}: {data.get('type')}")
                    except Exception as e:
                        logger.error(f"Error forwarding message: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    # Start listener task
    listener_task = asyncio.create_task(redis_listener())
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connected to document processing updates",
                "user_id": user_id
            }
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Wait for any message from client (heartbeat, etc.)
            data = await websocket.receive_text()
            
            # Echo back as heartbeat response
            await websocket.send_json({
                "type": "heartbeat",
                "data": {"status": "alive"}
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe(f"user:{user_id}:updates")
        await pubsub.close()
        manager.disconnect(websocket, user_id)


async def broadcast_document_update(user_id: int, document_id: int, status: str, message: str = None, data: dict = None):
    """
    Broadcast document status update to user's WebSocket connections
    
    Args:
        user_id: ID of document owner
        document_id: ID of document
        status: New status (uploaded, processing, completed, failed)
        message: Optional status message
        data: Additional data to include
    """
    update_data = {
        "document_id": document_id,
        "status": status,
    }
    
    if message:
        update_data["message"] = message
    
    if data:
        update_data.update(data)
    
    await manager.broadcast_to_user(user_id, "document_status_update", update_data)
    logger.info(f"📡 Broadcast document {document_id} status update to user {user_id}: {status}")


def broadcast_document_update_sync(user_id: int, document_id: int, status: str, message: str = None, data: dict = None):
    """
    Synchronous wrapper for broadcast_document_update
    Can be called from Celery tasks (non-async context)
    
    Uses Redis pub/sub to send updates to WebSocket connections
    
    Args:
        user_id: ID of document owner
        document_id: ID of document
        status: New status (uploaded, processing, completed, failed)
        message: Optional status message
        data: Additional data to include
    """
    import redis
    from app.core.config import settings
    
    update_data = {
        "document_id": document_id,
        "status": status,
    }
    
    if message:
        update_data["message"] = message
    
    if data:
        update_data.update(data)
    
    message_to_send = {
        "type": "document_status_update",
        "data": update_data
    }
    
    try:
        # Publish to Redis channel
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.publish(
            f"user:{user_id}:updates",
            json.dumps(message_to_send)
        )
        redis_client.close()
        logger.info(f"📡 Published document {document_id} update for user {user_id}: {status}")
    except Exception as e:
        logger.error(f"Error publishing to Redis: {e}")
