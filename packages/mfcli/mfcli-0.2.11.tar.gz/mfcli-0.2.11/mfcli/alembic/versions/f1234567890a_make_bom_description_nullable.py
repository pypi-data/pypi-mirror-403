"""Make BOM description field nullable

Revision ID: f1234567890a
Revises: e0f2b5765c72
Create Date: 2026-01-18 18:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1234567890a'
down_revision: Union[str, Sequence[str], None] = 'e0f2b5765c72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - make description nullable."""
    # Make description field nullable
    with op.batch_alter_table('bom', schema=None) as batch_op:
        batch_op.alter_column('description',
                              existing_type=sa.String(length=600),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema - make description non-nullable."""
    # Make description field non-nullable again
    with op.batch_alter_table('bom', schema=None) as batch_op:
        batch_op.alter_column('description',
                              existing_type=sa.String(length=600),
                              nullable=False)
