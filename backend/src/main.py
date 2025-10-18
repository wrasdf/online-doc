from fastapi import FastAPI
from src.middleware.auth import get_current_user
from fastapi import Depends

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

# This is a placeholder for the actual API router
from src.api.router import api_router
app.include_router(api_router, prefix="/api/v1")
