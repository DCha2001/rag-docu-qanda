from fastapi import APIRouter, Depends

from db.dbconnect import get_db
from db.models import Document

router = APIRouter()


@router.get("/documents")
def list_documents(db=Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
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
