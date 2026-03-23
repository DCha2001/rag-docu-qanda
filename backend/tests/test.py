import pytest
from unittest.mock import MagicMock, patch

from services.augment_utils import combine_chunks, build_user_message


# ─── combine_chunks ────────────────────────────────────────────────────────────

def test_combine_chunks_empty():
    assert combine_chunks([]) is None


def test_combine_chunks_single():
    chunks = [
        {"document_id": "doc1", "similarity_score": 0.95, "content": "Paris is the capital of France."}
    ]
    result = combine_chunks(chunks)
    assert "[Source 1]" in result
    assert "Paris is the capital of France." in result
    assert "document_id: doc1" in result
    assert "relevance: 0.95" in result


def test_combine_chunks_multiple():
    chunks = [
        {"document_id": "doc1", "similarity_score": 0.9, "content": "First chunk."},
        {"document_id": "doc2", "similarity_score": 0.8, "content": "Second chunk."},
    ]
    result = combine_chunks(chunks)
    assert "[Source 1]" in result
    assert "[Source 2]" in result
    assert "---" in result
    assert result.index("[Source 1]") < result.index("[Source 2]")


# ─── build_user_message ────────────────────────────────────────────────────────

def test_build_user_message_contains_xml_tags():
    msg = build_user_message("some context", "What is this?")
    assert "<context>" in msg
    assert "</context>" in msg
    assert "<question>" in msg
    assert "</question>" in msg


def test_build_user_message_contains_content():
    msg = build_user_message("relevant excerpt", "My question")
    assert "relevant excerpt" in msg
    assert "My question" in msg


def test_build_user_message_context_before_question():
    msg = build_user_message("context text", "question text")
    assert msg.index("<context>") < msg.index("<question>")


# ─── embed ─────────────────────────────────────────────────────────────────────

def test_embed_output_shape():
    from services.ingestion import embed

    class _FakeChunk:
        def __init__(self, text):
            self.text = text

    vectors = embed([_FakeChunk("Hello world"), _FakeChunk("Goodbye world")])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384  # all-MiniLM-L6-v2 dimensionality


def test_embed_single_chunk():
    from services.ingestion import embed

    class _FakeChunk:
        def __init__(self, text):
            self.text = text

    vectors = embed([_FakeChunk("Only one chunk")])
    assert len(vectors) == 1
    assert isinstance(vectors[0][0], float)


# ─── GET /health ───────────────────────────────────────────────────────────────

def test_health_ok(client, mock_db):
    mock_db.execute.return_value = MagicMock()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_db_error(client, mock_db):
    mock_db.execute.side_effect = Exception("connection refused")
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert "connection refused" in body["details"]


# ─── POST /query ───────────────────────────────────────────────────────────────

def test_query_returns_response(client):
    mock_chunks = {
        "chunks": [
            {
                "chunk_id": "c1",
                "document_id": "doc1",
                "content": "Paris is the capital of France.",
                "chunk_index": 0,
                "similarity_score": 0.95,
            }
        ]
    }
    with patch("api.routes.chat.search_simliar_chunks", return_value=mock_chunks):
        resp = client.post("/query?query=What+is+Paris")

    assert resp.status_code == 200
    assert "response" in resp.json()


def test_query_retrieval_error_returns_500(client):
    mock_error = {"error": "pgvector extension not found"}
    with patch("api.routes.chat.search_simliar_chunks", return_value=mock_error):
        resp = client.post("/query?query=anything")

    assert resp.status_code == 500
    assert "pgvector" in resp.json()["detail"]


def test_query_missing_param(client):
    resp = client.post("/query")
    assert resp.status_code == 422


# ─── POST /ingest ──────────────────────────────────────────────────────────────

def test_ingest_missing_file(client):
    resp = client.post("/ingest")
    assert resp.status_code == 422


def test_ingest_duplicate_rejected(client, mock_db):
    # Simulate the duplicate-hash check returning an existing row
    existing_row = MagicMock()
    existing_row.id = "existing-id"
    existing_row.filename = "original.pdf"
    mock_db.execute.return_value.fetchone.return_value = existing_row

    pdf_bytes = b"%PDF-1.4 fake content"
    resp = client.post(
        "/ingest",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert resp.status_code == 400
    assert "already ingested" in resp.json()["detail"]
