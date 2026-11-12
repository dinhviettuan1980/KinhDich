"""nhu cau cau le va toa do cua den

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-12 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0009'
down_revision: Union[str, Sequence[str], None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('temples', schema=None) as batch_op:
        batch_op.add_column(sa.Column('purposes', sa.String(length=200), server_default='', nullable=False))
        batch_op.add_column(sa.Column('lat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('lng', sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('temples', schema=None) as batch_op:
        batch_op.drop_column('lng')
        batch_op.drop_column('lat')
        batch_op.drop_column('purposes')
