"""ho so tin chu (ngay sinh) va the thanh toan gia lap

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-27 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('birth_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('card_brand', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('card_last4', sa.String(length=4), nullable=True))
        batch_op.add_column(sa.Column('card_exp', sa.String(length=5), nullable=True))
        batch_op.add_column(sa.Column('card_holder', sa.String(length=120), nullable=True))
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('clip_key', sa.String(length=300), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('clip_key')
    with op.batch_alter_table('users', schema=None) as batch_op:
        for c in ('card_holder', 'card_exp', 'card_last4', 'card_brand', 'birth_date'):
            batch_op.drop_column(c)
