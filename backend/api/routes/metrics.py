from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from db.dbconnect import get_db

router = APIRouter()

@router.get("/metrics/chunks")
async def get_chunk_metrics(document_id: str, db=Depends(get_db)):
    result = db.execute(
        text("""
        SELECT 
            document_id,
            COUNT(*) AS chunk_count,
            AVG(LENGTH(content)) AS mean_length,
            MIN(LENGTH(content)) AS min_length,
            MAX(LENGTH(content)) AS max_length,
            SUM(CASE WHEN LENGTH(content) < 100 THEN 1 ELSE 0 END) AS short_chunks,
            SUM(CASE WHEN LENGTH(content) > 1500 THEN 1 ELSE 0 END) AS long_chunks
        FROM chunks
        WHERE document_id = :document_id
        GROUP BY document_id
        """),
        {"document_id": document_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Document not found or no chunks available")

    return {
        "document_id": result.document_id,
        "chunk_count": result.chunk_count,
        "mean_length": result.mean_length,
        "min_length": result.min_length,
        "max_length": result.max_length,
        "short_chunks": result.short_chunks,
        "long_chunks": result.long_chunks
    }