import structlog

from fastapi import APIRouter, Depends
from db.dbconnect import get_db

from sqlalchemy import text

from schemas.health import HealthResponse

router = APIRouter()

logger = structlog.get_logger(__name__)

# `response_model=HealthResponse` does two things:
#   1. FastAPI validates your return value against the schema before sending it
#   2. The /docs UI shows the exact response shape for this endpoint
@router.get("/health", response_model=HealthResponse)
async def ping(db=Depends(get_db)):
    log = logger.bind(endpoint="GET /health")
    try:
        db.execute(text("SELECT 1"))
        log.info("Health check successful")
        return {"status": "ok"}
    except Exception as e:
        log.error("Health check failed", error=str(e))
        return {"status": "error", "details": str(e)}
