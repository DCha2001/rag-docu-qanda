import structlog

import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import tempfile, os

from db.dbconnect import get_db
from db.models import Document, Chunk
from services.ingestion import parse, chunk, embed

router = APIRouter()

log = structlog.get_logger(__name__)

@router.post("/ingest")
async def ingest(file: UploadFile = File(...), db=Depends(get_db)):
    log = log.bing(endpoint="POST /ingest", filename=file.filename)

    log.info("Starting document ingestion")

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
    except Exception as e:
        log.error("Failed to save uploaded file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    log.info("File saved successfully, starting processing", temp_path=tmp_path)

    try:
        doc = Document(filename=file.filename)
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
    except Exception as e:
        db.rollback()
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
