"""switch embeddings to voyage-3-lite (512-dim)

Revision ID: b3e7d2a91c05
Revises: f942bcb9a26c
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy

revision: str = 'b3e7d2a91c05'
down_revision: Union[str, Sequence[str], None] = 'f942bcb9a26c'
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
        type_=pgvector.sqlalchemy.Vector(512),
        postgresql_using="NULL",
    )


def downgrade() -> None:
    op.execute("DELETE FROM chunks")
    op.execute("UPDATE documents SET status = 'uploaded', chunk_count = 0 WHERE status = 'completed'")

    op.alter_column(
        "chunks",
        "embedding",
        type_=pgvector.sqlalchemy.Vector(384),
        postgresql_using="NULL",
    )
