from fastapi import APIRouter

from src.api.routes import documents, sharing, users

api_router = APIRouter()
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(sharing.router, tags=["sharing"])
api_router.include_router(users.router, tags=["users"])
