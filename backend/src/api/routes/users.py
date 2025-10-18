
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.db.session import get_db
from src.services.user_service import UserService
from src.middleware.auth import get_current_user
from src.models.user import User

router = APIRouter()


@router.get("/users/search")
async def search_users(
    email: Optional[str] = Query(None, description="Search by email"),
    username: Optional[str] = Query(None, description="Search by username"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for users by email or username.
    """
    if not email and not username:
        raise HTTPException(status_code=400, detail="Please provide either email or username")

    try:
        if email:
            user = await UserService.get_user_by_email(db, email=email)
            if user:
                return [{
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                }]
            return []

        if username:
            user = await UserService.get_user_by_username(db, username=username)
            if user:
                return [{
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                }]
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search users")
