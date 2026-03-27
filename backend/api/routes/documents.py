import structlog

from fastapi import APIRouter, Depends, HTTPException

from db.dbconnect import get_db
from db.models import Document
from schemas.documents import DocumentResponse, MessageResponse
import utils.cancellation as cancellation
from core.auth import get_current_user

router = APIRouter()

logger = structlog.get_logger(__name__)


@router.delete("/document", response_model=MessageResponse)
def delete_document(id: str, db=Depends(get_db), user_id: str = Depends(get_current_user)):
    log = logger.bind(endpoint="DELETE /document", document_id=id, user_id=user_id)
    log.info("delete_document.started")

    try:
        doc = db.query(Document).filter(Document.id == id).first()
        if not doc:
            log.warning("delete_document.not_found")
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.is_demo:
            raise HTTPException(status_code=403, detail="Demo documents cannot be deleted.")

        # IDOR protection: only the owner can delete their document
        if doc.user_id != user_id:
            log.warning("delete_document.forbidden", doc_owner=doc.user_id)
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")

        was_processing = cancellation.signal(id)
        if was_processing:
            log.info("delete_document.cancellation_signalled", document_id=id)

        db.delete(doc)
        db.commit()
        log.info("delete_document.success")
        return {"detail": "Document deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("delete_document.db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/document/list", response_model=list[DocumentResponse])
def list_documents(db=Depends(get_db), user_id: str = Depends(get_current_user)):
    log = logger.bind(endpoint="GET /document", user_id=user_id)
    log.info("list_documents.started")

    try:
        # Return the user's own documents plus all demo documents
        docs = (
            db.query(Document)
            .filter((Document.user_id == user_id) | (Document.is_demo == True))
            .order_by(Document.created_at.desc())
            .all()
        )
    except Exception as e:
        log.error("list_documents.db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

    log.info("list_documents.success", count=len(docs))
    return docs
