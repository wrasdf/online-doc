from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List

from src.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(index=True)
    content: Mapped[str]
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    accesses = relationship("DocumentAccess", back_populates="document", cascade="all, delete-orphan")
    edit_sessions = relationship("EditSession", back_populates="document", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="document", cascade="all, delete-orphan")
