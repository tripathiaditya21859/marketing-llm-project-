from fastapi import APIRouter
from app.config import DATABASE_PATH
from app.database_backend import get_connection



router = APIRouter(tags=["Health"])

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Moseta AI Backend is working"
    }

from fastapi import APIRouter

