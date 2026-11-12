"""danh muc than thanh

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-13 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0015'
down_revision: Union[str, Sequence[str], None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deities',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('aliases', sa.String(length=300), nullable=False),
        sa.Column('group_code', sa.String(length=10), nullable=False),
        sa.Column('group_name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('places', sa.Text(), nullable=False),
        sa.Column('province_old', sa.String(length=200), nullable=False),
        sa.Column('province_new', sa.String(length=200), nullable=False),
        sa.Column('reliability', sa.String(length=40), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('deities')
