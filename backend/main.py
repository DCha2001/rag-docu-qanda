import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from core.logging import configure_logging
from db.dbconnect import init_db
from api.routes import health, upload, chat

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
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)
