from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.middleware.auth import get_current_user
from src.models.user import User
from src.schemas.document import Document, DocumentCreate, DocumentUpdate, DocumentList
from src.services.document_service import DocumentService
from typing import Optional
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new document.

    - **title**: Document title (1-255 characters)
    - **content**: Plain text content (optional, defaults to empty string)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    db_document = await DocumentService.create_document(
        db=db,
        document=document,
        owner_id=current_user.id
    )
    return db_document


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents owned by the current user.

    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return (default 100, max 100)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Enforce maximum limit
    limit = min(limit, 100)

    documents, total = await DocumentService.get_documents_by_owner(
        db=db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return DocumentList(documents=documents, total=total)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific document by ID.

    Only the document owner can view the document.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    document = await DocumentService.get_document_by_id(db=db, document_id=document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )

    return document


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: uuid.UUID,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a document.

    Only the document owner can update the document.
    All fields are optional - only provided fields will be updated.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check ownership first
    is_owner = await DocumentService.check_document_ownership(
        db=db,
        document_id=document_id,
        user_id=current_user.id
    )

    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this document"
        )

    # Update document
    updated_document = await DocumentService.update_document(
        db=db,
        document_id=document_id,
        document_update=document_update
    )

    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document.

    Only the document owner can delete the document.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check ownership first
    is_owner = await DocumentService.check_document_ownership(
        db=db,
        document_id=document_id,
        user_id=current_user.id
    )

    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )

    # Delete document
    deleted = await DocumentService.delete_document(db=db, document_id=document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return None
