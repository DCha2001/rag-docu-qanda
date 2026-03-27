"""add user_id to documents and sessions

Revision ID: e1a2b3c4d5e6
Revises: f942bcb9a26c
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'f942bcb9a26c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id to documents (nullable — demo docs have NULL user_id)
    op.add_column('documents', sa.Column('user_id', sa.String(255), nullable=True))
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])

    # Add user_id to sessions (nullable for backward compat with existing rows)
    op.add_column('sessions', sa.Column('user_id', sa.String(255), nullable=True))
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_sessions_user_id', table_name='sessions')
    op.drop_column('sessions', 'user_id')

    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_column('documents', 'user_id')
