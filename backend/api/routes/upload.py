import structlog

import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import tempfile, os

from sqlalchemy import text

from db.dbconnect import get_db
from db.models import Document, Chunk
from services.ingestion import parse, chunk, embed

from utils.hash import generate_hash
from schemas.documents import DocumentResponse

router = APIRouter()

logger = structlog.get_logger(__name__)

# The ingest endpoint already returns a Document ORM object (`return doc`).
# Adding response_model=DocumentResponse means FastAPI will validate that
# object against our schema and serialize it — no code change needed inside
# the function body. The schema does the work.
@router.post("/ingest", response_model=DocumentResponse)
async def ingest(file: UploadFile = File(...), db=Depends(get_db)):
    log = logger.bind(endpoint="POST /ingest", filename=file.filename)

    if (file.size is not None) and (file.size > 50 * 1024 * 1024):
        log.warning("File size exceeds limit", file_size=file.size)
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    log.info("Starting document ingestion")

    try:
        file_read = await file.read()
        suffix = os.path.splitext(file.filename)[1]
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

        # Check for existing document with this hash
        existing = db.execute(
            text("SELECT id, filename FROM documents WHERE file_hash = :hash"),
            {"hash": file_hash}
        ).fetchone()

        if existing:
            log.error("Duplicate document detected, skipping ingestion", existing_id=existing.id, existing_filename=existing.filename)
            raise HTTPException(status_code=400, detail=f"Document already ingested as '{existing.filename}'")
        doc = Document(filename=file.filename, file_hash=file_hash)
        db.add(doc)
        db.commit()
        db.refresh(doc) # This allows us to communicate foreign keys or etc. back to the database to ensure data is up to date
        log.info("Document record created in database", document_id=doc.id)

        log.info("Starting parsing", document_id=doc.id)
        doc.status = "parsing"
        db.commit()
        elements = await asyncio.to_thread(parse, tmp_path)

        log.info("Parsing completed, starting chunking", element_count=len(elements))

        log.info("Starting chunking", document_id=doc.id)   
        doc.status = "chunking"
        db.commit()
        chunks = await asyncio.to_thread(chunk, elements)

        log.info("Chunking completed, starting embedding", chunk_count=len(chunks))

        log.info("Starting embedding", document_id=doc.id)
        doc.status = "embedding"
        db.commit()
        vectors = await asyncio.to_thread(embed, chunks)
        log.info("Embedding completed", document_id=doc.id)

        for i, (chunk_el, vector) in enumerate(zip(chunks, vectors)):
            page_num = getattr(chunk_el.metadata, "page_number", None)
            chunk_record = Chunk(
                document_id=doc.id,
                content=chunk_el.text,
                chunk_index=i,
                page_number=page_num,
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
    except Exception as e:
        db.rollback()
        if doc is not None:
            doc.status = "failed"
            db.commit()
        log.error("Error during document ingestion", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
