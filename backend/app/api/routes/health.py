from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.api.dependencies import get_database
from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": get_settings().app_name, "version": "v1"}


@router.get("/ready", response_model=None)
async def readiness() -> dict | Response:
    database = get_database()
    try:
        with database.connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": {"database": "failed"}},
        )
    return {"status": "ready", "checks": {"database": "ok"}}
