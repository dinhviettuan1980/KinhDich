"""ket qua nhan dien mam le tren anh

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-27 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('evidence', schema=None) as batch_op:
        batch_op.add_column(sa.Column('analysis', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('evidence', schema=None) as batch_op:
        batch_op.drop_column('analysis')
