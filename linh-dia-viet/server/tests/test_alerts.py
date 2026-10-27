"""Cảnh báo: thiết bị mất kết nối (mất điện/mạng) khi sắp có lễ → báo admin/nhân sự (trang Quản lý + Telegram)."""
from datetime import timedelta

import httpx
from sqlalchemy import select

from app import alerts, devices
from app.config import get_settings
from app.models import AuditLog, Device, Order, Setting, utcnow
from conftest import P, login
from helpers import confirm_and_pay, create_booking


def _scheduled_order(user_client, db, minutes):
    ref = create_booking(user_client, db, minutes=minutes)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    return db.scalar(select(Order).where(Order.booking_ref == ref))


def test_offline_device_with_upcoming_order_alerts_once_and_recovers(user_client, db, monkeypatch):
    sent = []
    monkeypatch.setattr(get_settings(), "telegram_bot_token", "bot123")
    monkeypatch.setattr(get_settings(), "telegram_chat_id", "42")
    monkeypatch.setattr(alerts.httpx, "post", lambda url, json=None, timeout=None: (sent.append((url, json)),
                                                                                   httpx.Response(200))[1])
    o = _scheduled_order(user_client, db, minutes=30)
    dev = db.get(Device, "pi-demo-01")
    dev.online, dev.last_seen_at = False, utcnow() - timedelta(minutes=10)
    db.commit()
    devices.tick(db)
    db.commit()
    assert len(sent) == 1 and "bot123/sendMessage" in sent[0][0] and sent[0][1]["chat_id"] == "42"
    text = sent[0][1]["text"]
    assert "pi-demo-01" in text and "Đền Ngọc Sơn" in text and f"#{o.id}" in text
    assert "Nguyễn Văn A" not in text  # không lộ thông tin khách
    devices.tick(db)
    db.commit()
    assert len(sent) == 1  # chỉ báo 1 lần cho 1 sự cố
    # trang Quản lý của admin hiện cảnh báo
    user_client.post(f"{P}/dang-xuat", data={"csrf_token": user_client.csrf})
    login(user_client, "admin@example.com", "admin12345")
    assert "mất kết nối" in user_client.get(f"{P}/admin").text
    # thiết bị có lại → báo đã kết nối lại, đóng cảnh báo
    dev = db.get(Device, "pi-demo-01")
    dev.online, dev.last_seen_at = True, utcnow()
    db.commit()
    devices.tick(db)
    db.commit()
    assert len(sent) == 2 and "kết nối lại" in sent[1][1]["text"]
    assert db.get(Setting, "alert:device:pi-demo-01") is None
    assert db.scalar(select(AuditLog).where(AuditLog.action == "alert"))


def test_no_alert_when_no_upcoming_order_or_far_away(user_client, db, monkeypatch):
    sent = []
    monkeypatch.setattr(alerts, "send_telegram", lambda text: sent.append(text))
    _scheduled_order(user_client, db, minutes=24 * 60)  # lễ còn xa
    dev = db.get(Device, "pi-demo-01")
    dev.online = False
    db.commit()
    devices.tick(db)
    db.commit()
    assert sent == [] and db.get(Setting, "alert:device:pi-demo-01") is None


def test_telegram_not_configured_is_noop(monkeypatch):
    monkeypatch.setattr(get_settings(), "telegram_bot_token", "")
    assert alerts.send_telegram("x") is False
