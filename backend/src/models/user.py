from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from datetime import datetime
import uuid
from src.db.session import Base
from src.models.document import Document

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    owned_documents = relationship("Document", back_populates="owner")
