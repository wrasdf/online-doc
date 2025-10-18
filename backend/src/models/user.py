from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List

from src.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]

    documents = relationship("Document", back_populates="owner")
    document_accesses = relationship("DocumentAccess", back_populates="user", foreign_keys="[DocumentAccess.user_id]")
