import structlog

from fastapi import APIRouter

router = APIRouter()

log = structlog.get_logger(__name__)

@router.get("/ping")
async def ping():
    log.info("Received ping request")
    return {"status": "ok"}
