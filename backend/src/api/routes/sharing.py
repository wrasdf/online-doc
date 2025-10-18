
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

from src.db.session import get_db
from src.schemas.sharing import ShareDocumentRequest, ShareResponse, CollaboratorsResponse
from src.services.sharing_service import SharingService
from src.services.user_service import UserService
from src.middleware.auth import get_current_user
from src.models.user import User

router = APIRouter()


@router.post("/documents/{document_id}/share", response_model=ShareResponse)
async def share_document(
    document_id: uuid.UUID,
    request: ShareDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Share a document with other users.
    """
    try:
        accesses = await SharingService.share_document(
            db=db,
            document_id=document_id,
            user_ids=request.user_ids,
            owner_id=current_user.id,
        )
        return {"document_id": document_id, "shared_with": accesses}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/documents/{document_id}/share/{user_id}")
async def remove_collaborator(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a user's access to a document.
    """
    try:
        await SharingService.remove_access(
            db=db,
            document_id=document_id,
            user_id=user_id,
            owner_id=current_user.id,
        )
        return {"message": "Access removed successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/documents/{document_id}/collaborators", response_model=CollaboratorsResponse)
async def get_collaborators(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the list of collaborators for a document.
    """
    try:
        collaborators = await SharingService.get_collaborators(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )
        return {"document_id": document_id, "collaborators": collaborators}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
