"""
Collaboration service for real-time document editing.

Handles:
- Redis pub/sub for broadcasting messages across multiple backend instances
- Document state management
- Change persistence
"""

import json
import logging
import base64
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from src.models.document import Document
from src.models.collaboration import Change, OperationType
from src.core.config import settings

logger = logging.getLogger(__name__)


class CollaborationService:
    """
    Service for managing real-time collaboration.

    Uses Redis pub/sub to broadcast messages across multiple backend instances
    for horizontal scaling.
    """

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

    async def connect_redis(self):
        """Connect to Redis for pub/sub."""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle binary data
            )
            self.pubsub = self.redis_client.pubsub()
            logger.info("Connected to Redis for pub/sub")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # In development, we can continue without Redis
            # In production, this should be a fatal error

    async def disconnect_redis(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Disconnected from Redis")

    async def publish_message(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name (typically document ID)
            message: Message dictionary to publish
        """
        if not self.redis_client:
            logger.warning("Redis not connected, message not published")
            return

        try:
            message_json = json.dumps(message)
            await self.redis_client.publish(channel, message_json)
            logger.debug(f"Published message to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

    async def subscribe_to_document(self, document_id: str):
        """
        Subscribe to updates for a document.

        Args:
            document_id: Document ID to subscribe to
        """
        if not self.pubsub:
            logger.warning("Redis pubsub not available")
            return

        try:
            await self.pubsub.subscribe(document_id)
            logger.info(f"Subscribed to document {document_id}")
        except Exception as e:
            logger.error(f"Failed to subscribe to document: {e}")

    async def unsubscribe_from_document(self, document_id: str):
        """
        Unsubscribe from document updates.

        Args:
            document_id: Document ID to unsubscribe from
        """
        if not self.pubsub:
            return

        try:
            await self.pubsub.unsubscribe(document_id)
            logger.info(f"Unsubscribed from document {document_id}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from document: {e}")

    async def get_document_state(
        self,
        document_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get current document state for sync_step2 response.

        Args:
            document_id: Document ID
            db: Database session

        Returns:
            Dictionary with document state and version
        """
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Return Yjs state if available, otherwise plain content
        yjs_state = ""
        if hasattr(document, 'yjs_state') and document.yjs_state:
            # Convert binary Yjs state to base64 for JSON transmission
            yjs_state = base64.b64encode(document.yjs_state).decode('utf-8')

        return {
            "document_id": document_id,
            "yjs_state": yjs_state,
            "content": document.content,
            "version": getattr(document, 'version', 1)
        }

    async def save_update(
        self,
        document_id: str,
        user_id: str,
        update: str,
        db: AsyncSession
    ):
        """
        Save a document update to the database.

        Args:
            document_id: Document ID
            user_id: User ID making the change
            update: Base64-encoded Yjs update
            db: Database session
        """
        try:
            # Decode base64 Yjs update
            yjs_update = base64.b64decode(update) if update else None

            # Create Change record
            change = Change(
                id=str(uuid.uuid4()),
                document_id=document_id,
                user_id=user_id,
                operation_type=OperationType.UPDATE,
                position=0,  # Position not used for Yjs updates
                yjs_update=yjs_update,
                timestamp=datetime.utcnow()
            )

            db.add(change)

            # Optionally update document's yjs_state
            # This could be done periodically or on every update
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if document and hasattr(document, 'yjs_state'):
                # In a real implementation, you'd apply the Yjs update
                # For now, we just store the latest update
                document.yjs_state = yjs_update

            await db.commit()

            logger.debug(f"Saved update for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to save update: {e}")
            await db.rollback()

    async def apply_yjs_update(
        self,
        document_id: str,
        yjs_update: bytes,
        db: AsyncSession
    ):
        """
        Apply a Yjs update to the document state.

        In a production system, this would use the Yjs library to merge updates.
        For now, we just store the raw update.

        Args:
            document_id: Document ID
            yjs_update: Binary Yjs update
            db: Database session
        """
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if document and hasattr(document, 'yjs_state'):
            # Store the update
            document.yjs_state = yjs_update
            await db.commit()

    async def get_active_users(
        self,
        document_id: str,
        db: AsyncSession
    ) -> list:
        """
        Get list of users currently editing a document.

        Args:
            document_id: Document ID
            db: Database session

        Returns:
            List of user dictionaries with presence information
        """
        from src.models.collaboration import EditSession, ConnectionStatus

        result = await db.execute(
            select(EditSession).where(
                EditSession.document_id == document_id,
                EditSession.connection_status == ConnectionStatus.CONNECTED
            )
        )
        sessions = result.scalars().all()

        active_users = []
        for session in sessions:
            active_users.append({
                "user_id": session.user_id,
                "cursor_position": session.cursor_position,
                "cursor_color": session.cursor_color,
                "last_activity": session.last_activity.isoformat()
            })

        return active_users

    async def cleanup_stale_sessions(self, db: AsyncSession):
        """
        Clean up stale edit sessions (inactive for > 5 minutes).

        Args:
            db: Database session
        """
        from src.models.collaboration import EditSession, ConnectionStatus
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(minutes=5)

        result = await db.execute(
            select(EditSession).where(
                EditSession.last_activity < cutoff_time,
                EditSession.connection_status != ConnectionStatus.DISCONNECTED
            )
        )
        stale_sessions = result.scalars().all()

        for session in stale_sessions:
            session.connection_status = ConnectionStatus.DISCONNECTED

        await db.commit()

        logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")


# Global collaboration service instance
collaboration_service = CollaborationService()


async def get_collaboration_service() -> CollaborationService:
    """Dependency injection for collaboration service."""
    return collaboration_service
