from fastapi import APIRouter

from app.core.config import settings
from app.db.database import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "DataTalk AI"}


@router.get("/health")
def health_check() -> dict[str, str]:
    database_status = "connected" if check_database_connection() else "disconnected"

    return {
        "status": "ok",
        "database": database_status,
        "llm_provider": settings.llm_provider,
    }
