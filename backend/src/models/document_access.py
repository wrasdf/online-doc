
import uuid
from datetime import datetime

from sqlalchemy import Column, UUID, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.session import Base


class DocumentAccess(Base):
    __tablename__ = "document_access"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    access_type: Mapped[str] = mapped_column(String, nullable=False, default="editor")
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    document = relationship("Document", back_populates="accesses")
    user = relationship("User", back_populates="document_accesses", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])
