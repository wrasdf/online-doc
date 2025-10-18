from fastapi import APIRouter
from src.api.routes import documents

api_router = APIRouter()

# Register route modules
api_router.include_router(documents.router)
