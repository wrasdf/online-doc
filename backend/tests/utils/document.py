
import random
import string
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document
from src.schemas.document import DocumentCreate
from src.services.document_service import DocumentService


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


async def create_random_document(
    db_session: AsyncSession, owner_id: uuid.UUID, title: Optional[str] = None
) -> Document:
    """
    Create a random document.
    """
    if title is None:
        title = random_lower_string()
    content = random_lower_string()
    document_in = DocumentCreate(title=title, content=content)
    return await DocumentService.create_document(
        db=db_session, document=document_in, owner_id=owner_id
    )
