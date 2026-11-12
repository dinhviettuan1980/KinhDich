"""Chia tiền theo vai trò cho đơn đã hoàn tất (tính khi xem, chưa có chi trả thật).
  tiền hàng của kiosk  → kiosk (trừ phí nền tảng)
  hàng dùng chung + phí đọc sớ → đền / thủ nhang (trừ phí nền tảng)
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Order, User


def split(order: Order, pct: int) -> dict:
    fee = order.total * pct // 100
    net = order.total - fee
    goods = order.total - order.service_fee
    kiosk_share = (goods * (100 - pct) // 100) if order.vendor_id else 0
    return {"platform": fee, "kiosk": kiosk_share, "temple": net - kiosk_share}


def report(db: Session, user: User) -> dict:
    pct = get_settings().platform_fee_pct
    q = select(Order).where(Order.status == "completed").order_by(Order.id.desc())
    if user.role == "vendor" and not user.is_admin:
        q = q.where(Order.vendor_id == user.id)
    elif not user.is_admin:
        q = q.where(Order.temple_id.in_(user.temple_ids or {-1}))
    rows, tot = [], defaultdict(int)
    for o in db.scalars(q.limit(500)).all():
        s = split(o, pct)
        rows.append({"o": o, **s})
        for k, v in s.items():
            tot[k] += v
        tot["gross"] += o.total
    return {"rows": rows, "total": dict(tot), "pct": pct}
