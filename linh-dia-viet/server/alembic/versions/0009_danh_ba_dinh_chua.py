"""danh ba dinh chua toan quoc (ban do)

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
    op.create_table(
        'sacred_places',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('source_id', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('religion', sa.String(length=30), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('province', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=300), nullable=False),
        sa.Column('phone', sa.String(length=60), nullable=False),
        sa.Column('website', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('description_source', sa.String(length=300), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('wikidata', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('edited', sa.Boolean(), nullable=False),
        sa.Column('temple_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['temple_id'], ['temples.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_id'),
        sa.UniqueConstraint('temple_id'),
    )
    with op.batch_alter_table('sacred_places', schema=None) as batch_op:
        batch_op.create_index('ix_sacred_places_kind', ['kind'])
        batch_op.create_index('ix_sacred_places_lat', ['lat'])
        batch_op.create_index('ix_sacred_places_lng', ['lng'])
        batch_op.create_index('ix_sacred_places_province', ['province'])


def downgrade() -> None:
    op.drop_table('sacred_places')
