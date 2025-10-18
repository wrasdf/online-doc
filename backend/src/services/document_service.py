from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.models.document import Document
from src.schemas.document import DocumentCreate, DocumentUpdate
from typing import Optional, List
import uuid

class DocumentService:
    @staticmethod
    async def create_document(db: AsyncSession, document: DocumentCreate, owner_id: uuid.UUID) -> Document:
        """Create a new document"""
        db_document = Document(
            title=document.title,
            content=document.content,
            owner_id=owner_id
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        return db_document

    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document by ID"""
        result = await db.execute(select(Document).filter(Document.id == document_id))
        return result.scalars().first()

    @staticmethod
    async def get_documents_by_owner(
        db: AsyncSession,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Document], int]:
        """Get all documents owned by a user with pagination"""
        # Get documents
        result = await db.execute(
            select(Document)
            .filter(Document.owner_id == owner_id)
            .order_by(Document.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()

        # Get total count
        count_result = await db.execute(
            select(func.count(Document.id)).filter(Document.owner_id == owner_id)
        )
        total = count_result.scalar()

        return list(documents), total

    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        document_update: DocumentUpdate
    ) -> Optional[Document]:
        """Update a document"""
        result = await db.execute(select(Document).filter(Document.id == document_id))
        db_document = result.scalars().first()

        if not db_document:
            return None

        # Update only provided fields
        if document_update.title is not None:
            db_document.title = document_update.title
        if document_update.content is not None:
            db_document.content = document_update.content
        if document_update.yjs_state is not None:
            db_document.yjs_state = document_update.yjs_state

        # Increment version for optimistic locking
        db_document.version += 1

        await db.commit()
        await db.refresh(db_document)
        return db_document

    @staticmethod
    async def delete_document(db: AsyncSession, document_id: uuid.UUID) -> bool:
        """Delete a document"""
        result = await db.execute(select(Document).filter(Document.id == document_id))
        db_document = result.scalars().first()

        if not db_document:
            return False

        await db.delete(db_document)
        await db.commit()
        return True

    @staticmethod
    async def check_document_ownership(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Check if a user owns a document"""
        result = await db.execute(
            select(Document).filter(
                Document.id == document_id,
                Document.owner_id == user_id
            )
        )
        return result.scalars().first() is not None
