from services.ingestion import _get_model
from sqlalchemy import text


def search_simliar_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
    document_id: int | None = None,
    db=None,
):
    try:
        embedding_model = _get_model()
        query_embedding = embedding_model.encode([query], show_progress_bar=False).tolist()[0]

        sql = text("""
                    SELECT
                        dc.id AS chunk_id,
                        dc.document_id,
                        dc.content,
                        dc.chunk_index,
                        1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS similarity_score
                    FROM chunks dc
                    WHERE 1 - (dc.embedding <=> CAST(:query_vec AS vector)) >= :threshold
                    AND (:doc_id IS NULL OR dc.document_id = :doc_id)
                    ORDER BY dc.embedding <=> CAST(:query_vec AS vector) ASC
                    LIMIT :top_k
                    """)

        params = {
            "query_vec": str(query_embedding),
            "threshold": score_threshold,
            "doc_id": document_id,
            "top_k": top_k,
        }

        result = db.execute(sql, params)
        rows = result.fetchall()

        # Step 3: Map rows to dicts for the response schema
        chunks = [
            {
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "similarity_score": round(float(row.similarity_score), 4),
            }
            for row in rows
        ]
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e)}
