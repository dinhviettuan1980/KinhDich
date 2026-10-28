"""Cảnh báo vận hành: thiết bị ở đền mất kết nối (mất điện / mất mạng) trong khi có lễ sắp tới giờ.

Báo 1 lần khi sự cố bắt đầu và 1 lần khi thiết bị kết nối lại (trạng thái lưu ở bảng settings, khoá "alert:device:<id>").
Kênh báo: trang Quản lý (admin + nhân sự của đền đó) và Telegram nếu cấu hình TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID.
Tin nhắn không chứa thông tin khách (chỉ đền, thiết bị, số lễ, giờ).
"""
import json
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Device, Order, Setting, Temple, utcnow
from .state_machine import OrderStatus as S
from .web import audit, fmt_local

log = logging.getLogger("linhdia.alerts")

PREFIX = "alert:device:"
WATCH = (S.SCHEDULED, S.DELIVERED)  # đơn còn chờ thiết bị phát


def send_telegram(text: str) -> bool:
    s = get_settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        return False
    try:
        r = httpx.post(f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage", timeout=10,
                       json={"chat_id": s.telegram_chat_id, "text": text, "disable_web_page_preview": True})
        return r.status_code == 200
    except httpx.HTTPError as e:
        log.warning("Gửi Telegram lỗi: %s", e)
        return False


def notify(db: Session, text: str, target: str) -> None:
    audit(db, "system", "alert", target, text=text)
    log.warning("CẢNH BÁO: %s", text)
    send_telegram(text)


def check_devices(db: Session, now: datetime | None = None) -> None:
    """Gọi trong vòng nền. Thiết bị offline + có lễ trong ALERT_LEAD phút tới (hoặc đã quá giờ) → báo."""
    from .routers.public import device_online
    now = now or utcnow()
    lead = timedelta(minutes=get_settings().alert_lead_minutes)
    for dev in db.scalars(select(Device).where(Device.revoked.is_(False))).all():
        key = PREFIX + dev.id
        state = db.get(Setting, key)
        temples = list(db.scalars(select(Temple).where(Temple.device_id == dev.id)))
        upcoming = list(db.scalars(select(Order).where(
            Order.temple_id.in_([t.id for t in temples] or [-1]), Order.status.in_([s.value for s in WATCH]),
            Order.scheduled_at <= now + lead).order_by(Order.scheduled_at)))
        names = ", ".join(t.name for t in temples) or dev.id
        if not device_online(dev) and upcoming and not state:
            first = upcoming[0]
            since = fmt_local(dev.last_seen_at, first.timezone, "%H:%M %d/%m") if dev.last_seen_at else "chưa từng"
            text = (f"⚠️ Thiết bị {dev.id} ({names}) mất kết nối từ {since} — có {len(upcoming)} lễ chờ phát, "
                    f"gần nhất #{first.id} lúc {fmt_local(first.scheduled_at, first.timezone, '%H:%M %d/%m')}. "
                    "Kiểm tra điện / mạng tại đền.")
            db.add(Setting(key=key, value=json.dumps({"since": now.isoformat(), "text": text,
                                                      "temple_ids": [t.id for t in temples]}, ensure_ascii=False)))
            notify(db, text, f"device:{dev.id}")
        elif state and device_online(dev):
            db.delete(state)
            notify(db, f"✅ Thiết bị {dev.id} ({names}) đã kết nối lại.", f"device:{dev.id}")


TRAY_PREFIX = "alert:tray:"
TRAY_SHOW = timedelta(hours=12)


def tray_mismatch(db: Session, order: Order, text: str, now: datetime | None = None) -> None:
    """Mâm lễ không khớp đơn: chỉ hiện ở trang Quản lý cho admin + nhân sự đền đó (quản lý, kiosk) trong 12 giờ.
    Không gửi Telegram (thông báo phụ); khách tự xem kết quả trên trang lễ."""
    now = now or utcnow()
    key = TRAY_PREFIX + str(order.id)
    st = db.get(Setting, key) or Setting(key=key)
    st.value = json.dumps({"text": text, "temple_ids": [order.temple_id], "until": (now + TRAY_SHOW).isoformat()},
                          ensure_ascii=False)
    db.add(st)
    audit(db, "system", "alert", f"order:{order.id}", text=text)
    log.info("Mâm lễ chưa khớp: %s", text)


def active(db: Session, user, now: datetime | None = None) -> list[dict]:
    """Cảnh báo đang mở mà user được xem (admin: tất cả; nhân sự: đền của mình)."""
    now = now or utcnow()
    out = []
    for st in db.scalars(select(Setting).where(Setting.key.startswith("alert:"))).all():
        try:
            d = json.loads(st.value)
        except ValueError:
            continue
        if d.get("until") and datetime.fromisoformat(d["until"]) < now:
            continue
        if user.is_admin or set(d.get("temple_ids") or []) & user.temple_ids:
            out.append(d)
    return out
