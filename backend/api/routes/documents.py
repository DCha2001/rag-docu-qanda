import structlog

from fastapi import APIRouter, Depends, HTTPException

from db.dbconnect import get_db
from db.models import Document
from schemas.documents import DocumentResponse, MessageResponse
import utils.cancellation as cancellation

router = APIRouter()

logger = structlog.get_logger(__name__)

# response_model=MessageResponse tells FastAPI: validate the return value
# against MessageResponse and use it to generate /docs documentation.
# If your function accidentally returns {"detial": "..."} (typo), FastAPI
# will catch it at runtime rather than silently sending wrong JSON.
@router.delete("/document", response_model=MessageResponse)
def delete_document(id: str, db=Depends(get_db)):
    log = logger.bind(endpoint="DELETE /document", document_id=id)
    log.info("delete_document.started")

    try:
        doc = db.query(Document).filter(Document.id == id).first()
        if not doc:
            log.warning("delete_document.not_found")
            raise HTTPException(status_code=404, detail="Document not found")

        # Signal the ingestion pipeline (if running) to stop at the next
        # batch boundary. The pipeline will notice the event is set, raise
        # IngestionCancelledError, and clean itself up. We delete the DB
        # record immediately — the pipeline's finally block handles its own
        # cleanup (temp file, registry deregistration).
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

# list[DocumentResponse] means FastAPI expects a list where every item
# matches the DocumentResponse schema. It will serialize each Document
# ORM object automatically because DocumentResponse has from_attributes=True.
@router.get("/document/list", response_model=list[DocumentResponse])
def list_documents(db=Depends(get_db)):
    log = logger.bind(endpoint="GET /document")
    log.info("list_documents.started")

    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
    except Exception as e:
        log.error("list_documents.db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

    log.info("list_documents.success", count=len(docs))

    # Before schemas: we had to manually build a dict for each doc.
    # Now we return the ORM objects directly. Pydantic reads the attributes
    # off each Document instance because DocumentResponse has from_attributes=True.
    # FastAPI handles serialization (including the datetime → ISO string conversion).
    return docs
