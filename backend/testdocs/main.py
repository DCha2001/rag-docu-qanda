from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import json

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class Document(Base):
    """
    Represents an uploaded document.

    Each document goes through the pipeline:
    Upload → Parse → Chunk → Embed → Store

    The 'status' column tracks where it is in that pipeline,
    which your Next.js frontend can poll to show progress.
    """
    __tablename__ = "documents"

    # UUIDs are better than auto-incrementing integers for APIs —
    # they're not guessable and won't collide across environments.
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # File hash for deduplication — store the SHA-256 of uploaded files
    # so you can reject or skip duplicates in your ingestion pipeline.
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="uploaded",
        nullable=False
    )  # uploaded | parsing | chunking | embedding | completed | failed
    page_count: Mapped[int] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship: one document has many chunks.
    # cascade="all, delete-orphan" means if you delete a document,
    # all its chunks get deleted too — no orphan data.
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class Chunk(Base):
    """
    Represents a single chunk of text extracted from a document,
    along with its embedding vector for similarity search.

    This is where your unstructured CompositeElement data lands
    after you extract .text and run it through the embedder.
    """
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    # The actual text content from unstructured's CompositeElement.text
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Metadata from unstructured — page number, category, etc.
    # Storing chunk_index helps you reconstruct document order for context.
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=True)
    # Category from unstructured (e.g., "NarrativeText", "Title", "Table")
    category: Mapped[str] = mapped_column(String(50), nullable=True)

    # The embedding vector — 384 dimensions for all-MiniLM-L6-v2.
    # This is what pgvector uses for similarity search.
    embedding = mapped_column(Vector(384), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to the parent document.
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks"
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

#Database configurations

#engine that manages connection pool to the databases (e.g how many connections, when to close them, etc.)
engine = create_engine(
    os.getenv("DATABASE_URL"), 
    pool_size=10,
    max_overflow=20,
    echo=True
)

#manages sessions (transactions) with the database, using the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class for our ORM models to inherit from

# Dependency function to get a database session for each request (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:        
        db.close()

file_path = "C:/Users/Derek/OneDrive/Desktop/AIDocuReader/backend/testdocs/docs"
base_file_name = "layout-parser-paper-fast"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def ingest(file_path: str) -> Document:
    """
    Full pipeline: parse → chunk → embed → store in DB.
    Creates a Document record and all associated Chunk records with embeddings.
    """
    Base.metadata.create_all(engine)
    db = SessionLocal()
    doc = None
    try:
        # 1. Create the Document record
        doc = Document(filename=os.path.basename(file_path))
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"Created document record: {doc.id}")

        # 2. Parse
        doc.status = "parsing"
        db.commit()
        elements = parse(file_path)

        # 3. Chunk
        doc.status = "chunking"
        db.commit()
        chunks = chunk(elements)

        # 4. Embed
        doc.status = "embedding"
        db.commit()
        vectors = embed(chunks)

        # 5. Store chunks with their embeddings
        for i, (chunk_el, vector) in enumerate(zip(chunks, vectors)):
            page_num = getattr(chunk_el.metadata, "page_number", None)
            chunk_record = Chunk(
                document_id=doc.id,
                content=chunk_el.text,
                chunk_index=i,
                page_number=page_num,
                category=chunk_el.category,
                embedding=vector,
            )
            db.add(chunk_record)

        doc.chunk_count = len(chunks)
        doc.status = "completed"
        db.commit()
        print(f"Ingested {len(chunks)} chunks for document '{doc.filename}' (id={doc.id})")
        return doc

    except Exception as e:
        if doc:
            doc.status = "failed"
            db.commit()
        print(f"Ingestion failed: {e}")
        raise
    finally:
        db.close()

def parse(file_path:str) -> list:
    elements = partition(
        filename=file_path,
        strategy="fast",          # accurate but slower; use "fast" for prototyping
        infer_table_structure=True,  # captures tables properly
        include_page_breaks=True,)
    return elements

def chunk(elements:list) -> list:
    chunked_elements = chunk_by_title(
        elements=elements, 
        max_characters=1500,       # max chunk size
        new_after_n_chars=1000,    # soft limit — break early if a new title appears
        combine_text_under_n_chars=300)  # combine tiny fragments

    return [c for c in chunked_elements if c.text.strip()]

def embed(chunks:list[str]) -> list[list[float]]:
    try:
        embedded = embeddings.embed_documents([element.text for element in chunks])
        return embedded
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IOError:
        print(f"Error: Unable to access file '{file_path}'.")



def main():
    doc = ingest(f"{file_path}/{base_file_name}.pdf")
    print(doc)


if __name__ == "__main__":
    main()