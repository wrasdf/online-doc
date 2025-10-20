from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
import uuid
from sqlalchemy import UUID, DateTime
from datetime import datetime

from src.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner")
    document_accesses = relationship("DocumentAccess", back_populates="user", foreign_keys="[DocumentAccess.user_id]")
    edit_sessions = relationship("EditSession", back_populates="user", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="user", cascade="all, delete-orphan")
