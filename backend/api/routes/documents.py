import structlog

from fastapi import APIRouter, Depends, HTTPException

from db.dbconnect import get_db
from db.models import Document

router = APIRouter()

logger = structlog.get_logger(__name__)

@router.get("/documents")
def list_documents(db=Depends(get_db)):
    log = logger.bind(endpoint="GET /documents")
    log.info("list_documents.started")

    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
    except Exception as e:
        log.error("list_documents.db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

    log.info("list_documents.success", count=len(docs))

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in docs
    ]
