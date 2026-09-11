from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings
from backend.app.db.session import engine

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    database = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database = "error"
    return {
        "status": "ok" if database == "ok" else "degraded",
        "environment": settings.app_env,
        "version": "1.0.0",
        "database": database,
        "model_status": "available" if Path(settings.model_path).is_file() else "missing",
        "prototype": True,
    }
