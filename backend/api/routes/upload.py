import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import tempfile, os

from db.dbconnect import get_db
from db.models import Document, Chunk
from services.ingestion import parse, chunk, embed

router = APIRouter()


@router.post("/ingest")
async def ingest(file: UploadFile = File(...), db=Depends(get_db)):

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        doc = Document(filename=file.filename)
        db.add(doc)
        db.commit()
        db.refresh(doc) # This allows us to communicate foreign keys or etc. back to the database to ensure data is up to date

        doc.status = "parsing"
        db.commit()
        elements = await asyncio.to_thread(parse, tmp_path)

        doc.status = "chunking"
        db.commit()
        chunks = await asyncio.to_thread(chunk, elements)

        doc.status = "embedding"
        db.commit()
        vectors = await asyncio.to_thread(embed, chunks)

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

        return doc
    except Exception as e:
        db.rollback()
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
