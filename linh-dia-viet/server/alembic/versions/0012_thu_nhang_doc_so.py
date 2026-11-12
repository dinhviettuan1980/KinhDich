"""thu nhang doc so tai cho: phi, gio doc

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-12 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0012'
down_revision: Union[str, Sequence[str], None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('orders') as b:
        b.add_column(sa.Column('service_fee', sa.Integer(), nullable=False, server_default='0'))
        b.add_column(sa.Column('read_started_at', sa.DateTime(timezone=True), nullable=True))
        b.add_column(sa.Column('read_ended_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('orders') as b:
        b.drop_column('read_ended_at')
        b.drop_column('read_started_at')
        b.drop_column('service_fee')
