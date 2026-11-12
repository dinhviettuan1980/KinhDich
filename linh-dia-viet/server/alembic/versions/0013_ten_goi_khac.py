"""danh ba dinh chua: ten goi khac (aliases) + tu khoa (keywords) de tim kiem

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-12 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0013'
down_revision: Union[str, Sequence[str], None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sacred_places') as b:
        b.add_column(sa.Column('aliases', sa.Text(), nullable=False, server_default=''))
        b.add_column(sa.Column('keywords', sa.Text(), nullable=False, server_default=''))


def downgrade() -> None:
    with op.batch_alter_table('sacred_places') as b:
        b.drop_column('keywords')
        b.drop_column('aliases')
