"""thu nhang duyet don, kiosk cua don

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-12 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0011'
down_revision: Union[str, Sequence[str], None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('temples') as b:
        b.add_column(sa.Column('require_approval', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('orders') as b:
        b.add_column(sa.Column('vendor_id', sa.Integer(), nullable=True))
        b.add_column(sa.Column('accept_by', sa.DateTime(timezone=True), nullable=True))
        b.add_column(sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
        b.create_index('ix_orders_vendor_id', ['vendor_id'])
        b.create_foreign_key('fk_orders_vendor', 'users', ['vendor_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('orders') as b:
        b.drop_constraint('fk_orders_vendor', type_='foreignkey')
        b.drop_index('ix_orders_vendor_id')
        b.drop_column('accepted_at')
        b.drop_column('accept_by')
        b.drop_column('vendor_id')
    with op.batch_alter_table('temples') as b:
        b.drop_column('require_approval')
