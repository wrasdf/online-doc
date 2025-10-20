from sqlalchemy import ForeignKey, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
import uuid

from src.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(index=True)
    content: Mapped[str]
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    accesses = relationship("DocumentAccess", back_populates="document", cascade="all, delete-orphan")
    edit_sessions = relationship("EditSession", back_populates="document", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="document", cascade="all, delete-orphan")
