import structlog

import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from core.limiter import limiter
import tempfile, os

from sqlalchemy import text

from db.dbconnect import get_db
from db.models import Document, Chunk
from services.ingestion import parse, embed

from utils.hash import generate_hash
from utils.cancellation import IngestionCancelledError
import utils.cancellation as cancellation
from schemas.documents import DocumentResponse
from core.auth import get_current_user

router = APIRouter()

logger = structlog.get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html", ".xlsx"}


@router.post("/ingest", response_model=DocumentResponse)
@limiter.limit("5/minute")
async def ingest(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    log = logger.bind(endpoint="POST /ingest", filename=file.filename, user_id=user_id)

    if (file.size is not None) and (file.size > 50 * 1024 * 1024):
        log.warning("File size exceeds limit", file_size=file.size)
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(e.lstrip(".") for e in sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {allowed_str}")

    log.info("Starting document ingestion")

    try:
        file_read = await file.read()

        if ext == ".pdf" and not file_read.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF.")
        if ext == ".docx" and not file_read.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=400, detail="File does not appear to be a valid DOCX.")
        suffix = os.path.splitext(file.filename or "")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_read)
            tmp_path = tmp.name
    except Exception as e:
        log.error("Failed to save uploaded file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    log.info("File saved successfully, starting processing", temp_path=tmp_path)

    doc = None
    try:
        file_hash = generate_hash(file_read)

        # Check for duplicate — scoped to this user (demo docs use is_demo flag)
        existing = db.execute(
            text("SELECT id, filename FROM documents WHERE file_hash = :hash AND (user_id = :uid OR is_demo = true)"),
            {"hash": file_hash, "uid": user_id}
        ).fetchone()

        if existing:
            log.error("Duplicate document detected, skipping ingestion", existing_id=existing.id, existing_filename=existing.filename)
            raise HTTPException(status_code=400, detail=f"Document already ingested as '{existing.filename}'")

        doc = Document(filename=file.filename, file_hash=file_hash, user_id=user_id)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        log.info("Document record created in database", document_id=doc.id)

        log.info("Starting parsing", document_id=doc.id)
        doc.status = "parsing"
        db.commit()
        chunks = await asyncio.to_thread(parse, tmp_path)

        log.info("Parsing completed, starting embedding", chunk_count=len(chunks))

        log.info("Starting embedding", document_id=doc.id)
        doc.status = "embedding"
        db.commit()
        cancel_event = cancellation.register(str(doc.id))
        vectors = await asyncio.to_thread(embed, chunks, cancel_event)
        log.info("Embedding completed", document_id=doc.id)

        for i, (chunk_el, vector) in enumerate(zip(chunks, vectors)):
            chunk_record = Chunk(
                document_id=doc.id,
                content=chunk_el.text,
                chunk_index=i,
                category=chunk_el.category,
                embedding=vector,
            )
            db.add(chunk_record)

        doc.chunk_count = len(chunks)
        doc.status = "completed"
        db.commit()
        log.info("All chunks added to database session, committing", chunk_count=len(chunks))

        return doc
    except HTTPException as e:
        raise e
    except IngestionCancelledError:
        db.rollback()
        log.info("Ingestion cancelled — document was deleted mid-pipeline", document_id=doc.id if doc else None)
        raise HTTPException(status_code=409, detail="Document was deleted while processing")
    except Exception as e:
        db.rollback()
        if doc is not None:
            doc.status = "failed"
            db.commit()
        log.error("Error during document ingestion", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if doc is not None:
            cancellation.deregister(str(doc.id))
        os.unlink(tmp_path)
