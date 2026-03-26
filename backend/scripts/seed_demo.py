"""
Seed demo documents on first startup.

Idempotent: if any is_demo=True document already exists, the function exits
immediately. This means redeploys and restarts are safe — seeding only runs
once against a fresh database.
"""
import asyncio
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import Document, Chunk
from services.ingestion import parse, embed
from utils.hash import generate_hash

logger = logging.getLogger(__name__)

DEMO_DOCS_DIR = Path(__file__).parent.parent / "demo_docs"


async def seed_demo_documents(db: Session) -> None:
    # Guard: skip entirely if demo docs have already been seeded
    if db.query(Document).filter(Document.is_demo == True).first():
        logger.info("Demo documents already seeded, skipping.")
        return

    #needs unstructured api version to run with pdf
    if not DEMO_DOCS_DIR.exists():
        logger.warning("demo_docs/ directory not found, skipping demo seeding.")
        return

    docx_files = list(DEMO_DOCS_DIR.glob("*.docx"))
    if not docx_files:
        logger.warning("No PDFs found in demo_docs/, skipping demo seeding.")
        return

    for docx_path in docx_files:
        logger.info(f"Seeding demo document: {docx_path.name}")
        doc = None
        try:
            file_bytes = docx_path.read_bytes()
            file_hash = generate_hash(file_bytes)

            # Skip if this exact file was somehow already ingested
            if db.query(Document).filter(Document.file_hash == file_hash).first():
                logger.info(f"Demo doc already exists by hash: {docx_path}, skipping.")
                continue

            doc = Document(
                filename=docx_path.name,
                file_hash=file_hash,
                is_demo=True,
                status="parsing",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            chunks = await asyncio.to_thread(parse, str(docx_path))

            doc.status = "embedding"
            db.commit()
            # No cancel_event — seeding runs at startup before any user can cancel
            vectors = await asyncio.to_thread(embed, chunks)

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
            logger.info(f"Demo document seeded: {docx_path.name} ({len(chunks)} chunks)")

        except Exception as e:
            db.rollback()
            if doc is not None:
                doc.status = "failed"
                db.commit()
            logger.error(f"Failed to seed demo document {docx_path.name}: {e}")
