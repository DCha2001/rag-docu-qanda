# AIDocuReader

A full-stack RAG (Retrieval-Augmented Generation) application that lets you upload documents and ask natural language questions against them. Answers are grounded exclusively in the uploaded content and include source citations — powered by Claude (Anthropic API).

---

## How It Works

1. **Upload** — a document (PDF, DOCX, TXT, CSV, XLSX, PPTX, MD) is sent to the backend
2. **Parse** — `unstructured` extracts text elements from the file
3. **Chunk** — content is split into semantic chunks using title-based chunking
4. **Embed** — each chunk is embedded with `sentence-transformers` (`all-MiniLM-L6-v2`) and stored in PostgreSQL via `pgvector`
5. **Query** — on a user question, the top-k most similar chunks are retrieved via cosine similarity search and passed as context to Claude, which returns a cited answer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy + Alembic |
| Parsing | unstructured |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Anthropic API (Claude) |
| Logging | structlog |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
AIDocuReader/
├── backend/
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── core/
│   │   ├── config.py            # Environment config
│   │   ├── client.py            # Anthropic client
│   │   └── logging.py           # structlog configuration
│   ├── db/
│   │   ├── dbconnect.py         # SQLAlchemy engine + session
│   │   └── models.py            # Document, Chunk ORM models
│   ├── services/
│   │   ├── ingestion.py         # parse(), chunk(), embed()
│   │   ├── retrieval.py         # pgvector similarity search
│   │   └── augment_utils.py     # RAG prompt construction
│   └── api/routes/
│       ├── health.py            # GET /health
│       ├── upload.py            # POST /ingest
│       ├── chat.py              # POST /query
│       ├── documents.py         # GET /document/list, DELETE /document
│       └── metrics.py           # GET /metrics/chunks
├── frontend/
│   └── app/
│       ├── page.tsx             # Main page (upload + chat)
│       ├── components/
│       │   ├── Sidebar.tsx      # Document list + upload
│       │   └── ChatPanel.tsx    # Chat interface
│       ├── api/
│       │   ├── document/route.ts  # Proxies document list/delete to backend
│       │   └── query/route.ts     # Proxies query to backend
│       └── models/
│           ├── documents.ts     # Document type definitions
│           └── query.ts         # Query/response type definitions
└── docker-compose.yml
```

---

## Running Locally

### Prerequisites
- Docker + Docker Compose

### Setup

1. Clone the repo:
```bash
git clone <repo-url>
cd AIDocuReader
```

2. Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/aidocureader
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-haiku-4-5-20251001
MODE=development
```

3. Create `frontend/.env`:
```env
API_URL=http://backend:8000
MODE=development
```

4. Start all services:
```bash
docker compose up --build
```

The app will be available at `http://localhost:3000`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check (includes DB connectivity) |
| `POST` | `/ingest` | Upload and process a document |
| `GET` | `/document/list` | List all documents (ordered by creation date) |
| `DELETE` | `/document` | Delete a document and its chunks by ID |
| `POST` | `/query` | Ask a question against ingested documents |
| `GET` | `/metrics/chunks` | Chunk quality stats for a given document |

---

## Key Design Decisions

**Async ingestion** — parsing, chunking, and embedding are CPU-bound operations. They run in a thread pool via `asyncio.to_thread` so the FastAPI event loop is never blocked.

**Status tracking** — documents move through `parsing → chunking → embedding → completed` states, persisted to the DB at each step. The frontend polls every 3 seconds and reflects live status with animated indicators.

**RAG prompt structure** — context chunks are wrapped in XML tags (`<context>`, `<question>`) following Anthropic's prompt engineering guidelines. Claude is instructed to cite sources by `[Source N]` label and refuse to answer outside the provided context.

**Duplicate detection** — files are SHA-256 hashed on upload. If a matching hash already exists in the database, ingestion is rejected with a `400` before any processing begins.

**Structured logging** — `structlog` is used throughout with key-value structured events (e.g. `document_id`, `chunk_count`, `error`) for machine-parseable logs in production and colorized output in development.

**Chunk metrics** — the `/metrics/chunks` endpoint exposes per-document statistics (count, mean/min/max length, short and long chunk counts) useful for evaluating chunking quality.

---

## Tests

Tests live in `backend/tests/` and use `pytest`.

```
backend/tests/
├── conftest.py           # TestClient + mock DB fixtures
├── test.py               # Unit + integration tests (services, endpoints)
└── rag_test/
    └── test_rag_eval.py  # RAG evaluation tests
```

Coverage includes:
- `combine_chunks` / `build_user_message` (RAG prompt construction)
- `embed` output shape and dtype
- `GET /health` (ok + DB error paths)
- `POST /query` (success, retrieval error, missing param)
- `POST /ingest` (missing file, duplicate rejection)

Run tests:
```bash
cd backend
pytest tests/
```
