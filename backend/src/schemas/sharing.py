
from pydantic import BaseModel, EmailStr
import uuid
from typing import List
from datetime import datetime


class ShareDocumentRequest(BaseModel):
    user_ids: List[uuid.UUID]


class CollaboratorInfo(BaseModel):
    user_id: uuid.UUID
    username: str
    email: EmailStr
    access_type: str
    granted_at: datetime

    class Config:
        from_attributes = True


class ShareResponse(BaseModel):
    document_id: uuid.UUID
    shared_with: List[CollaboratorInfo]


class CollaboratorsResponse(BaseModel):
    document_id: uuid.UUID
    collaborators: List[CollaboratorInfo]
