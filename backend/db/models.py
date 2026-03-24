import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from sqlalchemy import Index


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


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    documents: Mapped[list["Document"]] = relationship("Document", secondary="session_documents")


class SessionDocument(Base):
    __tablename__ = "session_documents"
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)   # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["Session"] = relationship("Session", back_populates="messages")


# On messages — you'll always query "give me all messages for session X, ordered by time"
Index("ix_messages_session_created", Message.session_id, Message.created_at)