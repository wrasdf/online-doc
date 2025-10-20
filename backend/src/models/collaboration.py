from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, Text, LargeBinary, DateTime, CheckConstraint, Enum as SQLEnum, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
import uuid

from src.db.session import Base


class ConnectionStatus(str, enum.Enum):
    """Enum for WebSocket connection status."""
    CONNECTED = "connected"
    IDLE = "idle"
    DISCONNECTED = "disconnected"


class OperationType(str, enum.Enum):
    """Enum for document change operation types."""
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"


class EditSession(Base):
    """
    Represents an active editing session.

    Tracks which users are currently viewing/editing which documents,
    along with their cursor positions and connection status.
    """
    __tablename__ = "edit_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)

    # Cursor and awareness information
    cursor_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cursor_color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color #RRGGBB

    # Connection status
    connection_status: Mapped[str] = mapped_column(
        SQLEnum(ConnectionStatus),
        nullable=False,
        default=ConnectionStatus.CONNECTED
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # WebSocket connection identifier
    websocket_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="edit_sessions")
    document = relationship("Document", back_populates="edit_sessions")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "cursor_position >= 0 OR cursor_position IS NULL",
            name="valid_cursor_position"
        ),
    )

    def __repr__(self):
        return (
            f"<EditSession(id={self.id}, user_id={self.user_id}, "
            f"document_id={self.document_id}, status={self.connection_status})>"
        )


class Change(Base):
    """
    Represents a single edit operation in a document.

    Used for real-time synchronization and potentially for version history.
    Stores both plain text changes and binary Yjs CRDT updates.
    """
    __tablename__ = "changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Operation details
    operation_type: Mapped[str] = mapped_column(
        SQLEnum(OperationType),
        nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content for different operation types
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For insert
    length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For delete

    # Binary Yjs update for CRDT synchronization
    yjs_update: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    # Timestamp and ordering
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        autoincrement=True
    )

    # Relationships
    document = relationship("Document", back_populates="changes")
    user = relationship("User", back_populates="changes")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="valid_position"
        ),
        CheckConstraint(
            "(operation_type != 'insert') OR (content IS NOT NULL)",
            name="insert_has_content"
        ),
        CheckConstraint(
            "(operation_type != 'delete') OR (length > 0)",
            name="delete_has_length"
        ),
    )

    def __repr__(self):
        return (
            f"<Change(id={self.id}, document_id={self.document_id}, "
            f"operation={self.operation_type}, position={self.position})>"
        )
