import structlog

from fastapi import APIRouter, Depends
from db.dbconnect import get_db

from sqlalchemy import text

router = APIRouter()

logger = structlog.get_logger(__name__)

@router.get("/health")
async def ping(db=Depends(get_db)):
    log = logger.bind(endpoint="GET /health")
    try:
        db.execute(text("SELECT 1"))
        log.info("Health check successful")
        return {"status": "ok"}
    except Exception as e:
        log.error("Health check failed", error=str(e))
        return {"status": "error", "details": str(e)}
