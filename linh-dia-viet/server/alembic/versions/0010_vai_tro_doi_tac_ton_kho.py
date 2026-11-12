"""duyet tai khoan doi tac, kiosk va ton kho

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-12 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0010'
down_revision: Union[str, Sequence[str], None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as b:
        b.add_column(sa.Column('approval', sa.String(length=10), nullable=False, server_default='approved'))
    with op.batch_alter_table('offering_packages') as b:
        b.add_column(sa.Column('vendor_id', sa.Integer(), nullable=True))
        b.add_column(sa.Column('stock', sa.Integer(), nullable=True))
        b.create_index('ix_offering_packages_vendor_id', ['vendor_id'])
        b.create_foreign_key('fk_offering_packages_vendor', 'users', ['vendor_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('offering_packages') as b:
        b.drop_constraint('fk_offering_packages_vendor', type_='foreignkey')
        b.drop_index('ix_offering_packages_vendor_id')
        b.drop_column('stock')
        b.drop_column('vendor_id')
    with op.batch_alter_table('users') as b:
        b.drop_column('approval')
