"""update_vector_dimension

Revision ID: 92a35607db7a
Revises: 6a6d4579355d
Create Date: 2026-05-20 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92a35607db7a'
down_revision: Union[str, Sequence[str], None] = '6a6d4579355d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Alter the embedding vector dimension to 1024
        op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN embedding TYPE vector(1024)")
        # Re-create HNSW index for the 1024 dimension vector
        op.execute("""
            CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
                ON rag.document_chunks
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
        """)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Drop the HNSW index
        op.execute("DROP INDEX IF EXISTS rag.document_chunks_embedding_idx")
        # Revert the embedding vector dimension to 768
        op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN embedding TYPE vector(768)")
