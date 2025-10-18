"""
WebSocket connection handler for real-time collaborative editing.

Handles:
- WebSocket connections with JWT authentication
- Yjs CRDT update synchronization
- User presence and cursor tracking
- Message broadcasting via Redis pub/sub
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Set, Optional
import random

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.models.user import User
from src.models.document import Document
from src.models.document_access import DocumentAccess
from src.models.collaboration import EditSession, ConnectionStatus
from src.services.auth_service import decode_access_token
from src.services.collaboration_service import CollaborationService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Tracks connections per document and handles message broadcasting.
    """

    def __init__(self):
        # Document ID -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> User ID mapping
        self.connection_users: Dict[WebSocket, str] = {}
        # WebSocket -> Document ID mapping
        self.connection_documents: Dict[WebSocket, str] = {}

    async def connect(
        self,
        websocket: WebSocket,
        document_id: str,
        user_id: str
    ):
        """Connect a client to a document."""
        await websocket.accept()

        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()

        self.active_connections[document_id].add(websocket)
        self.connection_users[websocket] = user_id
        self.connection_documents[websocket] = document_id

        logger.info(
            f"User {user_id} connected to document {document_id}. "
            f"Total connections: {len(self.active_connections[document_id])}"
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a client."""
        document_id = self.connection_documents.get(websocket)
        user_id = self.connection_users.get(websocket)

        if document_id and document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)

            # Clean up empty document rooms
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]

        self.connection_users.pop(websocket, None)
        self.connection_documents.pop(websocket, None)

        logger.info(f"User {user_id} disconnected from document {document_id}")

        return document_id, user_id

    async def broadcast_to_document(
        self,
        document_id: str,
        message: dict,
        exclude: Optional[WebSocket] = None
    ):
        """Broadcast a message to all connections in a document."""
        if document_id not in self.active_connections:
            return

        connections = self.active_connections[document_id].copy()

        for connection in connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")
                    # Connection is broken, remove it
                    self.disconnect(connection)

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def get_user_id(self, websocket: WebSocket) -> Optional[str]:
        """Get user ID for a connection."""
        return self.connection_users.get(websocket)

    def get_document_id(self, websocket: WebSocket) -> Optional[str]:
        """Get document ID for a connection."""
        return self.connection_documents.get(websocket)


# Global connection manager
manager = ConnectionManager()


def generate_cursor_color() -> str:
    """Generate a random color for cursor indicator."""
    colors = [
        "#FF5733",  # Red-Orange
        "#33FF57",  # Green
        "#3357FF",  # Blue
        "#FF33F5",  # Magenta
        "#F5FF33",  # Yellow
        "#33FFF5",  # Cyan
        "#FF8C33",  # Orange
        "#8C33FF",  # Purple
    ]
    return random.choice(colors)


async def verify_document_access(
    document_id: str,
    user_id: str,
    db: AsyncSession
) -> bool:
    """
    Verify that a user has access to a document.

    Returns True if user is owner or has been granted access.
    """
    # Check if user is owner
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == user_id
        )
    )
    if result.scalar_one_or_none():
        return True

    # Check if user has been granted access
    result = await db.execute(
        select(DocumentAccess).where(
            DocumentAccess.document_id == document_id,
            DocumentAccess.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None


async def create_edit_session(
    websocket: WebSocket,
    document_id: str,
    user_id: str,
    db: AsyncSession
) -> EditSession:
    """Create an edit session for the connection."""
    session = EditSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        document_id=document_id,
        cursor_position=0,
        cursor_color=generate_cursor_color(),
        connection_status=ConnectionStatus.CONNECTED,
        started_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        websocket_id=str(id(websocket))
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


async def update_edit_session_status(
    session_id: str,
    status: ConnectionStatus,
    db: AsyncSession
):
    """Update edit session connection status."""
    result = await db.execute(
        select(EditSession).where(EditSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session:
        session.connection_status = status
        session.last_activity = datetime.utcnow()
        await db.commit()


async def websocket_endpoint(
    websocket: WebSocket,
    document_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
    collab_service: CollaborationService = Depends()
):
    """
    WebSocket endpoint for real-time collaboration.

    URL: /ws/documents/{document_id}?token={jwt_token}
    """
    # Authenticate user
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=4003, reason="Invalid token")
            return
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return

    # Verify document access
    has_access = await verify_document_access(document_id, user_id, db)
    if not has_access:
        await websocket.close(code=4003, reason="Access denied")
        return

    # Get user information
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        await websocket.close(code=4003, reason="User not found")
        return

    # Create edit session
    session = await create_edit_session(websocket, document_id, user_id, db)

    # Connect to manager
    await manager.connect(websocket, document_id, user_id)

    # Send user_joined notification to all other users
    await manager.broadcast_to_document(
        document_id,
        {
            "type": "user_joined",
            "document_id": document_id,
            "user": {
                "user_id": user_id,
                "username": user.username,
                "cursor_color": session.cursor_color
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude=websocket
    )

    # Send user_joined to the connecting user (for themselves)
    await manager.send_to_connection(websocket, {
        "type": "user_joined",
        "document_id": document_id,
        "user": {
            "user_id": user_id,
            "username": user.username,
            "cursor_color": session.cursor_color
        },
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            logger.debug(f"Received message type: {message_type} from user {user_id}")

            if message_type == "sync_step1":
                # Client requests initial document state
                document = await collab_service.get_document_state(document_id, db)

                await manager.send_to_connection(websocket, {
                    "type": "sync_step2",
                    "document_id": document_id,
                    "state": document.get("yjs_state", ""),
                    "version": document.get("version", 1)
                })

            elif message_type == "sync_update":
                # Client sends document update
                update = data.get("update")

                # Broadcast to all other clients
                await manager.broadcast_to_document(
                    document_id,
                    {
                        "type": "sync_update",
                        "document_id": document_id,
                        "update": update,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exclude=websocket
                )

                # Optionally save update to database (for persistence)
                await collab_service.save_update(
                    document_id, user_id, update, db
                )

            elif message_type == "awareness_update":
                # Client sends cursor/presence update
                awareness = data.get("awareness")

                # Update cursor position in edit session
                if awareness and "cursor_position" in awareness:
                    result = await db.execute(
                        select(EditSession).where(EditSession.id == session.id)
                    )
                    edit_session = result.scalar_one_or_none()
                    if edit_session:
                        edit_session.cursor_position = awareness["cursor_position"]
                        edit_session.last_activity = datetime.utcnow()
                        await db.commit()

                # Broadcast to all other clients
                await manager.broadcast_to_document(
                    document_id,
                    {
                        "type": "awareness_update",
                        "document_id": document_id,
                        "awareness": awareness
                    },
                    exclude=websocket
                )

            elif message_type == "pong":
                # Heartbeat response
                await update_edit_session_status(
                    session.id, ConnectionStatus.CONNECTED, db
                )

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        # Clean disconnect
        document_id, user_id = manager.disconnect(websocket)

        # Update session status
        await update_edit_session_status(
            session.id, ConnectionStatus.DISCONNECTED, db
        )

        # Notify other users
        if document_id and user_id:
            await manager.broadcast_to_document(
                document_id,
                {
                    "type": "user_left",
                    "document_id": document_id,
                    "user_id": user_id,
                    "username": user.username,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        document_id, user_id = manager.disconnect(websocket)

        # Update session status
        await update_edit_session_status(
            session.id, ConnectionStatus.DISCONNECTED, db
        )

        # Send error to client
        try:
            await manager.send_to_connection(websocket, {
                "type": "error",
                "error": "internal_error",
                "message": str(e),
                "code": 500
            })
        except:
            pass  # Connection might be closed
