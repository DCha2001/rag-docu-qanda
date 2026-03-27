import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import OperationalError

from core.logging import configure_logging
from core.limiter import limiter
from db.dbconnect import init_db, SessionLocal
from scripts.seed_demo import seed_demo_documents
from api.routes import health, upload, chat, documents, metrics, sessions

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for attempt in range(10):
        try:
            init_db()
            logger.info("Database ready.")
            break
        except OperationalError:
            logger.warning(f"Database not ready, retrying ({attempt + 1}/10)...")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Could not connect to the database after 10 attempts.")

    async def _seed():
        db = SessionLocal()
        try:
            await seed_demo_documents(db)
        finally:
            db.close()

    asyncio.create_task(_seed())

    yield


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins_env = os.environ.get("ALLOWED_ORIGINS", "http://reliable-youth.railway.internal,http://localhost:3000,http://frontend:3000,http://localhost:8080")
allowed_origins = [o.strip() for o in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(metrics.router)
app.include_router(sessions.router)
