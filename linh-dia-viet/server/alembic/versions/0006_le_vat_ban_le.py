"""le vat ban le (chon tung mon thay cho combo)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-27 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITEMS = [  # bản chụp app/seed.py lúc viết migration
    dict(name="Hương (nhang)", unit="bó", price=20_000, max_qty=10, description="Hương trầm, 1 bó khoảng 100 nén."),
    dict(name="Nến", unit="đôi", price=20_000, max_qty=10, description="Đôi nến đỏ thắp hai bên ban thờ."),
    dict(name="Hoa tươi", unit="bó", price=60_000, max_qty=5, description="Hoa cúc vàng, hoa hồng hoặc hoa sen theo mùa."),
    dict(name="Ngũ quả", unit="mâm", price=150_000, max_qty=3, description="Năm loại quả tươi bày trên đĩa."),
    dict(name="Trầu cau", unit="cơi", price=30_000, max_qty=5, description="Lá trầu têm cánh phượng và quả cau."),
    dict(name="Oản", unit="cặp", price=30_000, max_qty=5, description="Oản đường hình tháp, dùng cho lễ chay."),
    dict(name="Xôi gấc", unit="đĩa", price=60_000, max_qty=5, description="Xôi gấc đỏ (có thể đổi xôi đỗ)."),
    dict(name="Gà luộc", unit="con", price=280_000, max_qty=3, description="Gà trống luộc nguyên con, cài hoa hồng."),
    dict(name="Rượu trắng", unit="chai", price=40_000, max_qty=5, description="Rượu nếp nhỏ."),
    dict(name="Bánh kẹo", unit="gói", price=30_000, max_qty=5, description="Bánh kẹo, chè lam."),
    dict(name="Vàng mã", unit="bộ", price=50_000, max_qty=5, description="Tiền vàng, sớ giấy (đốt sau lễ)."),
    dict(name="Nước sạch", unit="chai", price=10_000, max_qty=5, description="Chai nước tinh khiết."),
]

OLD_COMBOS = ["Lễ chay thanh tịnh", "Lễ hoa quả", "Lễ mặn đầy đủ", "Lễ dâng sao giải hạn"]


def upgrade() -> None:
    with op.batch_alter_table('offering_packages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit', sa.String(length=30), nullable=False, server_default='phần'))
        batch_op.add_column(sa.Column('max_qty', sa.Integer(), nullable=False, server_default='10'))
        batch_op.add_column(sa.Column('sort', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('package_id', existing_type=sa.Integer(), nullable=True)

    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['package_id'], ['offering_packages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)

    # Dữ liệu: tắt 4 combo mẫu cũ (đơn cũ vẫn trỏ tới được), thêm danh mục lễ vật bán lẻ dùng chung.
    pk = sa.table('offering_packages', sa.column('name'), sa.column('active', sa.Boolean), sa.column('temple_id'),
                  sa.column('description'), sa.column('price'), sa.column('unit'), sa.column('max_qty'),
                  sa.column('sort'), sa.column('image_url'))
    op.execute(pk.update().where(pk.c.name.in_(OLD_COMBOS), pk.c.temple_id.is_(None)).values(active=False))
    conn = op.get_bind()
    if conn.execute(sa.select(sa.func.count()).select_from(pk)).scalar():  # DB mới tinh thì để seed lo
        op.bulk_insert(pk, [dict(it, active=True, temple_id=None, image_url="", sort=i)
                            for i, it in enumerate(ITEMS)])


def downgrade() -> None:
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')
    with op.batch_alter_table('offering_packages', schema=None) as batch_op:
        batch_op.drop_column('sort')
        batch_op.drop_column('max_qty')
        batch_op.drop_column('unit')
