from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(default="", description="Plain text content")

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Document title")
    content: Optional[str] = Field(None, description="Plain text content")
    yjs_state: Optional[bytes] = Field(None, description="Binary Yjs CRDT state")

class Document(DocumentBase):
    """Schema for document response"""
    id: uuid.UUID
    owner_id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
    yjs_state: Optional[bytes] = None

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2

class DocumentList(BaseModel):
    """Schema for listing documents"""
    documents: list[Document]
    total: int
