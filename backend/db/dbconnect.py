import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

from core.config import DATABASE_URL

logger = logging.getLogger(__name__)

# engine that manages connection pool to the databases (e.g how many connections, when to close them, etc.)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=True,
)

# manages sessions (transactions) with the database, using the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    logger.info("Initializing database and creating tables if they don't exist...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()


# Dependency function to get a database session for each request (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
