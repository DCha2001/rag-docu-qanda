"""switch embeddings to voyage-4-lite (1024-dim)

Revision ID: c3e7d2a91c05
Revises: b3e7d2a91c05
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy

revision: str = 'c3e7d2a91c05'
down_revision: Union[str, Sequence[str], None] = 'b3e7d2a91c05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing embeddings are 384-dim — incompatible with 512-dim.
    # Clear all chunks so documents get re-embedded on next ingest.
    op.execute("DELETE FROM chunks")
    op.execute("UPDATE documents SET status = 'uploaded', chunk_count = 0 WHERE status = 'completed'")

    op.alter_column(
        "chunks",
        "embedding",
        type_=pgvector.sqlalchemy.Vector(1024),
        postgresql_using="NULL",
    )


def downgrade() -> None:
    op.execute("DELETE FROM chunks")
    op.execute("UPDATE documents SET status = 'uploaded', chunk_count = 0 WHERE status = 'completed'")

    op.alter_column(
        "chunks",
        "embedding",
        type_=pgvector.sqlalchemy.Vector(512),
        postgresql_using="NULL",
    )
