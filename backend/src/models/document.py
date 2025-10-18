from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, LargeBinary
from datetime import datetime
from typing import Optional
import uuid
from src.db.session import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    yjs_state: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="owned_documents")
