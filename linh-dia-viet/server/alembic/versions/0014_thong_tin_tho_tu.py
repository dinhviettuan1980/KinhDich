"""danh ba dinh chua: thong tin tho tu (than linh, hang thanh, dieu cau, le hoi, bac uu tien, vi tri gan dung)

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-12 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0014'
down_revision: Union[str, Sequence[str], None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sacred_places') as b:
        b.add_column(sa.Column('deity', sa.String(length=300), nullable=False, server_default=''))
        b.add_column(sa.Column('deity_groups', sa.String(length=100), nullable=False, server_default=''))
        b.add_column(sa.Column('intents', sa.String(length=100), nullable=False, server_default=''))
        b.add_column(sa.Column('festival', sa.Text(), nullable=False, server_default=''))
        b.add_column(sa.Column('priority', sa.Integer(), nullable=True))
        b.add_column(sa.Column('approx_location', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table('sacred_places') as b:
        for c in ('approx_location', 'priority', 'festival', 'intents', 'deity_groups', 'deity'):
            b.drop_column(c)
