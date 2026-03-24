# AIDocuReader

A full-stack RAG (Retrieval-Augmented Generation) application that lets you upload documents and ask natural language questions against them. Answers are grounded exclusively in the uploaded content and include source citations — powered by Claude (Anthropic API).

Chat history is persisted per session. Each session maintains its own document context and full conversation history, surviving page refreshes.

---

## How It Works

1. **Upload** — a document (PDF, DOCX, TXT, CSV, XLSX, PPTX, MD) is sent to the backend
2. **Parse** — `unstructured` extracts text elements from the file
3. **Chunk** — content is split into semantic chunks using title-based chunking
4. **Embed** — each chunk is embedded with `sentence-transformers` (`all-MiniLM-L6-v2`) and stored in PostgreSQL via `pgvector`
5. **Session** — users create named sessions and attach documents to them
6. **Query** — on a user question, the top-k most similar chunks are retrieved from the session's documents via cosine similarity search and passed as context to Claude, which returns a cited answer. The full conversation history for the session is included in each request.

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
│   ├── alembic.ini              # Alembic configuration
│   ├── alembic/
│   │   ├── env.py               # Migration environment (reads DATABASE_URL from .env)
│   │   └── versions/            # Migration history
│   ├── core/
│   │   ├── config.py            # Environment config
│   │   ├── client.py            # Anthropic client
│   │   └── logging.py           # structlog configuration
│   ├── db/
│   │   ├── dbconnect.py         # SQLAlchemy engine + session
│   │   └── models.py            # Document, Chunk, Session, Message ORM models
│   ├── schemas/
│   │   ├── chat.py              # QueryRequest/Response, SessionCreate/Out, MessageOut
│   │   └── documents.py         # DocumentResponse, MessageResponse
│   ├── services/
│   │   ├── ingestion.py         # parse(), chunk(), embed()
│   │   ├── retrieval.py         # pgvector similarity search (session-scoped)
│   │   └── augment_utils.py     # RAG prompt construction
│   └── api/routes/
│       ├── health.py            # GET /health
│       ├── upload.py            # POST /ingest
│       ├── chat.py              # POST /query
│       ├── documents.py         # GET /document/list, DELETE /document
│       ├── sessions.py          # CRUD /sessions + document attach/detach
│       └── metrics.py           # GET /metrics/chunks
├── frontend/
│   └── app/
│       ├── page.tsx             # Root page — session + chat state management
│       ├── components/
│       │   ├── Sidebar.tsx      # Sessions list + per-session document management
│       │   └── ChatPanel.tsx    # Chat interface with session header + history
│       ├── api/
│       │   ├── document/route.ts          # Proxies document list/upload/delete
│       │   ├── query/route.ts             # Proxies query (with session_id)
│       │   └── session/
│       │       ├── route.ts               # GET list / POST create session
│       │       └── [id]/
│       │           ├── route.ts           # DELETE session
│       │           ├── messages/route.ts  # GET session message history
│       │           └── documents/
│       │               ├── route.ts       # GET / POST attach document
│       │               └── [docId]/route.ts  # DELETE detach document
│       └── models/
│           ├── documents.ts     # Document type definitions
│           ├── query.ts         # Query/response type definitions
│           └── session.ts       # Session + Message type definitions
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

4. Start the database and backend:
```bash
docker compose up -d db backend
```

5. Run database migrations:
```bash
docker compose exec backend alembic upgrade head
```

6. Start all services:
```bash
docker compose up --build
```

The app will be available at `http://localhost:3000`.

> **Note:** Alembic migrations must be run inside the container (`docker compose exec backend ...`) because the `DATABASE_URL` uses the `db` Docker service hostname, which only resolves on the internal Docker network.

---

## Database Schema

```
documents          — uploaded files with status tracking
chunks             — text chunks + 384-dim embeddings (pgvector)
sessions           — named chat sessions
messages           — per-session chat history (role + content)
session_documents  — many-to-many: which documents belong to which session
```

Migrations are managed by Alembic. The `alembic_version` table in PostgreSQL tracks which migrations have been applied.

```bash
# Generate a new migration after changing models.py
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Roll back one migration
docker compose exec backend alembic downgrade -1

# Check current migration version
docker compose exec backend alembic current
```

---

## API Endpoints

### Documents
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Upload and process a document |
| `GET` | `/document/list` | List all documents |
| `DELETE` | `/document` | Delete a document and its chunks by ID |

### Sessions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions` | Create a new session |
| `DELETE` | `/sessions/{id}` | Delete a session and all its messages |
| `GET` | `/sessions/{id}/messages` | Get full message history for a session |
| `GET` | `/sessions/{id}/documents` | List documents attached to a session |
| `POST` | `/sessions/{id}/documents/{doc_id}` | Attach a document to a session |
| `DELETE` | `/sessions/{id}/documents/{doc_id}` | Detach a document from a session |

### Chat & Utility
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Ask a question (requires `session_id` in body) |
| `GET` | `/health` | Health check (includes DB connectivity) |
| `GET` | `/metrics/chunks` | Chunk quality stats for a given document |

---

## Key Design Decisions

**Session-scoped retrieval** — vector similarity search is filtered to only the documents attached to the active session. If a session has no documents attached, no chunks are retrieved. This prevents answers from bleeding across unrelated workspaces.

**Persistent chat history** — every user and assistant message is saved to the `messages` table keyed by `session_id`. On page load, history is fetched from the DB so conversations survive refreshes. Up to the last 20 messages are sent as context to Claude per request.

**Auto-titling** — when the first message is sent in a session that has no title, the session is automatically titled from the first 60 characters of that message. The sidebar updates immediately after the response returns.

**Auto-attach on upload** — when a document is uploaded while a session is active, it is automatically attached to that session after processing completes.

**Async ingestion** — parsing, chunking, and embedding are CPU-bound operations. They run in a thread pool via `asyncio.to_thread` so the FastAPI event loop is never blocked.

**Status tracking** — documents move through `uploaded → parsing → chunking → embedding → completed` states, persisted to the DB at each step. The frontend reflects live status with animated indicators.

**RAG prompt structure** — context chunks are wrapped in XML tags (`<context>`, `<question>`) following Anthropic's prompt engineering guidelines. Claude is instructed to cite sources by `[Source N]` label and refuse to answer outside the provided context.

**Duplicate detection** — files are SHA-256 hashed on upload. If a matching hash already exists in the database, ingestion is rejected with a `400` before any processing begins.

**Structured logging** — `structlog` is used throughout with key-value structured events (e.g. `document_id`, `chunk_count`, `error`) for machine-parseable logs in production and colorized output in development.

**Schema migrations** — `create_all` is not used at runtime. Alembic owns the schema — migrations run as a deploy step before the app starts, so the app always boots against a known, versioned schema state.

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
