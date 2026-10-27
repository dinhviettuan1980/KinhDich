from datetime import timedelta

from sqlalchemy import select

from app import devices
from app.config import get_settings
from app.models import AuditLog, Device, Order, Temple, utcnow
from conftest import P, login
from helpers import booking_data, confirm_and_pay, create_booking, post_json, tone


def _recorded_paid_order(user_client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "auto_approve_recordings", False)
    key = post_json(user_client, "/dat-le/ghi-am",
                    files={"file": ("r.wav", tone(tmp_path / "r.wav").read_bytes(), "audio/wav")}).json()["key"]
    ref = create_booking(user_client, db, cach_khan="recorded", ghi_am=key)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    return db.scalar(select(Order).where(Order.booking_ref == ref))


def _as_admin(client):
    client.post(f"{P}/dang-xuat", data={"csrf_token": client.csrf})
    client.csrf = login(client, "admin@example.com", "admin12345")
    return client


def test_moderation_approve_schedules(user_client, db, tmp_path, monkeypatch):
    o = _recorded_paid_order(user_client, db, tmp_path, monkeypatch)
    assert o.status == "paid" and not o.jobs
    c = _as_admin(user_client)
    page = c.get(f"{P}/admin/kiem-duyet").text
    assert f"Bản ghi #{o.prayer_id}" in page
    assert c.get(f"{P}/admin/kiem-duyet/{o.prayer_id}/audio").status_code == 200
    assert "1 chờ duyệt" in c.get(f"{P}/admin").text
    c.post(f"{P}/admin/kiem-duyet/{o.prayer_id}", data={"quyet_dinh": "duyet", "csrf_token": c.csrf})
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "scheduled" and o.prayer.moderation == "approved" and o.jobs[-1].state == "queued"
    assert "Không có bản ghi nào" in c.get(f"{P}/admin/kiem-duyet").text


def test_moderation_reject_refunds(user_client, db, tmp_path, monkeypatch):
    o = _recorded_paid_order(user_client, db, tmp_path, monkeypatch)
    c = _as_admin(user_client)
    assert c.post(f"{P}/admin/kiem-duyet/{o.prayer_id}", data={"quyet_dinh": "tu_choi", "csrf_token": c.csrf}).status_code == 400
    c.post(f"{P}/admin/kiem-duyet/{o.prayer_id}", data={"quyet_dinh": "tu_choi", "ly_do": "Âm thanh không rõ",
                                                       "csrf_token": c.csrf})
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "refund_requested" and "Âm thanh không rõ" in o.note
    assert db.scalar(select(AuditLog).where(AuditLog.action == "prayer.reject"))


def test_moderation_admin_only(client, db):
    tok = login(client, "quanly@example.com", "demo12345")
    assert client.get(f"{P}/admin/kiem-duyet").status_code == 403
    assert client.post(f"{P}/admin/khoa-khan-cap", data={"khoa": "1", "csrf_token": tok}).status_code == 403


def test_emergency_lock(user_client, db):
    ref = create_booking(user_client, db)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    o.jobs[-1].play_at = o.scheduled_at = utcnow() + timedelta(seconds=30)
    db.commit()
    c = _as_admin(user_client)
    db.bus.sent.clear()
    c.post(f"{P}/admin/khoa-khan-cap", data={"khoa": "1", "csrf_token": c.csrf})
    sent = db.bus.sent[:]
    assert {d for d, p in sent} == {"pi-demo-01", "pi-test-02", "pi-test-03"} and all(p == {"type": "stop"} for _, p in sent)
    assert "ĐANG KHÓA KHẨN CẤP" in c.get(f"{P}/admin").text
    devices.tick(db)  # không gửi lệnh play khi đang khóa
    db.commit()
    assert db.bus.sent == sent
    c.post(f"{P}/admin/thiet-bi/pi-demo-01/lenh", data={"type": "test_tone", "csrf_token": c.csrf})
    assert db.bus.sent == sent
    assert db.scalar(select(AuditLog).where(AuditLog.action == "device.cmd_blocked"))
    c.post(f"{P}/admin/thiet-bi/pi-demo-01/lenh", data={"type": "stop", "csrf_token": c.csrf})
    assert db.bus.sent[-1] == ("pi-demo-01", {"type": "stop"})  # lệnh dừng luôn được phép
    assert c.post(f"{P}/admin/don/{o.id}/gui-lai", data={"csrf_token": c.csrf}).status_code == 409
    c.post(f"{P}/admin/khoa-khan-cap", data={"khoa": "0", "csrf_token": c.csrf})
    devices.tick(db)
    db.commit()
    assert db.bus.sent[-1][1]["type"] == "play"


def test_admin_order_detail_and_resend(user_client, db):
    ref = create_booking(user_client, db)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    c = _as_admin(user_client)
    page = c.get(f"{P}/admin/don/{o.id}").text
    assert o.jobs[-1].id in page and "Gửi lại job" in page and "Nguyễn Văn A" in page
    r = c.post(f"{P}/admin/don/{o.id}/gui-lai", data={"csrf_token": c.csrf}, follow_redirects=False)
    assert r.status_code == 303 and db.bus.sent[-1][1]["job_id"] == o.jobs[-1].id


def test_order_json(user_client, db):
    ref = create_booking(user_client, db)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    j = user_client.get(f"{P}/don/{o.id}/json").json()
    assert j["status"] == "scheduled" and [e["status"] for e in j["events"]][-1] == "scheduled"


def test_book_100_temples(user_client, db):
    for i in range(97):
        db.add(Device(id=f"pi-bulk-{i}", name="bulk", token_hash="x"))
        db.add(Temple(slug=f"den-{i}", name=f"Đền số {i}", device_id=f"pi-bulk-{i}"))
    db.commit()
    slugs = [t.slug for t in db.scalars(select(Temple).order_by(Temple.id))]
    assert len(slugs) == 100
    ref = create_booking(user_client, db, temples=slugs)
    db.expire_all()
    orders = db.scalars(select(Order).where(Order.booking_ref == ref)).all()
    assert len(orders) == 100 and len({o.prayer_id for o in orders}) == 1
    from helpers import TXN
    page = user_client.get(f"{P}/thanh-toan/{TXN[ref]}").text
    assert "2.000.000 ₫" in page  # 100 × 20.000


def test_kinh_dich_link_and_prefix(user_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "home_url", "/kinhdich/van-khan")
    html = user_client.get(f"{P}/").text
    assert 'href="/kinhdich/van-khan"' in html and "Kinh Dịch" in html
    assert 'class="ld"' in html  # style bọc trong .ld


def test_change_password(user_client, db):
    c = user_client
    assert "Đổi mật khẩu" in c.get(f"{P}/tai-khoan").text
    c.post(f"{P}/tai-khoan/mat-khau", data={"old": "sai", "new": "moi12345", "csrf_token": c.csrf})
    c.post(f"{P}/tai-khoan/mat-khau", data={"old": "matkhau123", "new": "moi12345", "csrf_token": c.csrf})
    c.post(f"{P}/dang-xuat", data={"csrf_token": c.csrf})
    login(c, "a@example.com", "moi12345")


def test_cli_create_staff(db, capsys):
    from app.cli import main
    main(["create-user", "kiosk2@example.com", "--role", "vendor", "--temple", "den-ngoc-son", "--password", "abc12345"])
    assert "kiosk2@example.com / abc12345" in capsys.readouterr().out
    db.expire_all()
    from app.models import User
    u = db.scalar(select(User).where(User.email == "kiosk2@example.com"))
    assert u.role == "vendor" and len(u.temple_ids) == 1


def test_temple_page_lists_items_and_book_link(user_client, db):
    html = user_client.get(f"{P}/den/den-ngoc-son").text
    assert "Sắm lễ và đặt lễ" in html and "&goi=" not in html and "/bó" in html


def test_recorded_booking_keeps_read_text(user_client, db, tmp_path):
    key = post_json(user_client, "/dat-le/ghi-am",
                    files={"file": ("r.wav", tone(tmp_path / "r.wav").read_bytes(), "audio/wav")}).json()["key"]
    d = booking_data(db, cach_khan="recorded", ghi_am=key, van_ban_goc="Bài gốc.", van_ban="Bài gốc, con xin đọc.")
    r = post_json(user_client, "/dat-le", d)
    assert r.status_code == 200
    from app.models import Prayer
    assert db.scalars(select(Prayer)).all()[-1].text == "Bài gốc, con xin đọc."
