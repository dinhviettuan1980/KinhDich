from sqlalchemy import select

from app.models import Order, PrayerTemplate
from conftest import P, csrf_of, login
from helpers import confirm_and_pay, create_booking, temple_id


def _paid_order(client, db, user_login=("a@example.com", "matkhau123"), slug="den-ngoc-son"):
    client.csrf = login(client, *user_login)
    ref = create_booking(client, db, temples=(slug,))
    confirm_and_pay(client, ref)
    client.post(f"{P}/dang-xuat", data={"csrf_token": client.csrf})
    db.expire_all()
    return db.scalar(select(Order).where(Order.booking_ref == ref))


def test_vendor_sees_schedule_without_pii(client, db, user):
    o = _paid_order(client, db)
    other = _paid_order(client, db, slug="chua-tran-quoc")
    tok = login(client, "kiosk@example.com", "demo12345")
    html = client.get(f"{P}/admin/lich-le").text
    assert f"#{o.id}" in html and f"#{other.id}" not in html
    assert "Nguyễn Văn A" not in html and "a@example.com" not in html
    r = client.post(f"{P}/admin/don/{o.id}/mam-le", data={"csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.get(Order, o.id).tray_ready_at is not None
    assert client.post(f"{P}/admin/don/{o.id}/tu-choi", data={"csrf_token": tok, "ly_do": "x"}).status_code == 403
    assert client.post(f"{P}/admin/don/{other.id}/mam-le", data={"csrf_token": tok}).status_code == 403


def test_manager_rejects_then_admin_refunds(client, db, user):
    o = _paid_order(client, db)
    tok = login(client, "quanly@example.com", "demo12345")
    assert client.post(f"{P}/admin/don/{o.id}/tu-choi", data={"csrf_token": tok, "ly_do": ""}).status_code == 400
    r = client.post(f"{P}/admin/don/{o.id}/tu-choi", data={"csrf_token": tok, "ly_do": "Đền đóng cửa trùng tu"},
                    follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "refund_requested" and o.note == "Đền đóng cửa trùng tu"
    assert client.post(f"{P}/admin/don/{o.id}/hoan-tien", data={"csrf_token": tok}).status_code == 403
    client.post(f"{P}/dang-xuat", data={"csrf_token": tok})
    tok = login(client, "admin@example.com", "admin12345")
    assert "Nguyễn Văn A" in client.get(f"{P}/admin/lich-le").text  # admin thấy thông tin khách
    client.post(f"{P}/admin/don/{o.id}/hoan-tien", data={"csrf_token": tok})
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "refunded" and o.payments[0].status == "refunded"


def test_manager_edits_own_template_only(client, db):
    tok = login(client, "quanly@example.com", "demo12345")
    ns = temple_id(db)
    other = temple_id(db, "chua-tran-quoc")
    assert client.get(f"{P}/admin/mau-so/chung").status_code == 403
    assert client.get(f"{P}/admin/mau-so/{other}").status_code == 403
    assert client.post(f"{P}/admin/mau-so/{ns}", data={"csrf_token": tok, "body": "Sai {bien}"}).status_code == 400
    r = client.post(f"{P}/admin/mau-so/{ns}", data={"csrf_token": tok, "body": "Kính lạy {than_linh}, {ho_ten}."},
                    follow_redirects=False)
    assert r.status_code == 303
    assert db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id == ns)).body == "Kính lạy {than_linh}, {ho_ten}."
    client.post(f"{P}/admin/mau-so/{ns}", data={"csrf_token": tok, "body": "x", "xoa": "1"})
    db.expire_all()
    assert db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id == ns)) is None


def test_vendor_cannot_edit_templates(client, db):
    login(client, "kiosk@example.com", "demo12345")
    assert client.get(f"{P}/admin/mau-so").status_code == 403
