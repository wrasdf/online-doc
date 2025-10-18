from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.db.session import SessionLocal

reusable_oauth2 = HTTPBearer(
    scheme_name='Bearer'
)

async def get_current_user(request: Request):
    try:
        token = await reusable_oauth2(request)
        if token is None:
            return None
        payload = AuthService.decode_access_token(token.credentials)
        if payload is None:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        async with SessionLocal() as db:
            user = await UserService.get_user_by_id(db, user_id)
            if user is None:
                return None
            return user
    except (HTTPException, Exception):
        return None
