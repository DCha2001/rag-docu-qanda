import os

import voyageai
from sqlalchemy import text

_client: voyageai.Client | None = None


def _get_client() -> voyageai.Client:
    global _client
    if _client is None:
        _client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return _client


def search_simliar_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
    document_ids: list[str] | None = None,
    db=None,
):
    try:
        result = _get_client().embed([query], model="voyage-4-lite", input_type="query")
        query_embedding = result.embeddings[0]

        # Build the document filter clause dynamically.
        # When document_ids is provided and non-empty, restrict results to those
        # document IDs using PostgreSQL's string_to_array function so we can pass
        # the list as a single comma-separated string parameter.
        if document_ids:
            doc_filter_clause = "AND dc.document_id = ANY(string_to_array(:doc_ids, ','))"
            doc_ids_param = ",".join(document_ids)
        else:
            doc_filter_clause = ""
            doc_ids_param = None

        sql = text(f"""
                    SELECT
                        dc.id AS chunk_id,
                        dc.document_id,
                        dc.content,
                        dc.chunk_index,
                        1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS similarity_score
                    FROM chunks dc
                    WHERE 1 - (dc.embedding <=> CAST(:query_vec AS vector)) >= :threshold
                    {doc_filter_clause}
                    ORDER BY dc.embedding <=> CAST(:query_vec AS vector) ASC
                    LIMIT :top_k
                    """)

        params = {
            "query_vec": str(query_embedding),
            "threshold": score_threshold,
            "top_k": top_k,
        }

        if document_ids:
            params["doc_ids"] = doc_ids_param

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
