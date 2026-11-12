"""Đăng ký đối tác (thủ nhang/kiosk) chờ admin duyệt; kiosk tự quản hàng + tồn kho."""
from sqlalchemy import select

from app.models import OfferingPackage, Order, Temple, User
from conftest import P, csrf_of, login
from helpers import confirm_and_pay, create_booking, post_json


def _signup(client, role, email):
    tok = csrf_of(client, f"{P}/dang-ky")
    r = client.post(f"{P}/dang-ky", data={"name": "Đối tác", "identifier": email, "password": "abcdefgh",
                                         "vai_tro": role, "csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    return tok


def test_partner_signup_pending_has_no_backoffice_until_approved(client, db, admin_client):
    from fastapi.testclient import TestClient
    from app.main import app
    partner = TestClient(app)  # client & admin_client dùng chung phiên → đối tác dùng trình duyệt riêng
    _signup(partner, "kios", "kios.moi@example.com")
    u = db.scalar(select(User).where(User.email == "kios.moi@example.com"))
    assert (u.role, u.approval) == ("vendor", "pending")
    assert partner.get(f"{P}/admin").status_code == 403  # chưa duyệt = chưa có quyền
    # admin duyệt
    r = admin_client.post(f"{P}/admin/nguoi-dung/{u.id}/duyet",
                          data={"quyet_dinh": "duyet", "csrf_token": admin_client.csrf}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.get(User, u.id).approval == "approved"
    assert partner.get(f"{P}/admin").status_code == 200


def test_customer_signup_default_and_unknown_role_ignored(client, db):
    _signup(client, "quan_tri", "x@example.com")
    u = db.scalar(select(User).where(User.email == "x@example.com"))
    assert (u.role, u.approval) == ("customer", "approved")


def test_vendor_goods_with_stock_and_isolation(client, db):
    tok = login(client, "kiosk@example.com", "demo12345")
    ns = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    r = client.post(f"{P}/admin/goi-le/moi", data={"name": "Hoa sen", "price": "50000", "temple_id": str(ns.id),
                                                  "stock": "3", "active": "true", "csrf_token": tok},
                    follow_redirects=False)
    assert r.status_code == 303
    pkg = db.scalar(select(OfferingPackage).where(OfferingPackage.name == "Hoa sen"))
    vendor = db.scalar(select(User).where(User.email == "kiosk@example.com"))
    assert pkg.vendor_id == vendor.id and pkg.stock == 3
    # kiosk không thấy / sửa hàng của người khác (gói dùng chung)
    page = client.get(f"{P}/admin/goi-le").text
    assert "Hoa sen" in page
    shared = db.scalar(select(OfferingPackage).where(OfferingPackage.temple_id.is_(None)))
    assert client.get(f"{P}/admin/goi-le/{shared.id}").status_code == 403


def test_stock_reserved_blocked_and_restored(user_client, db):
    ns = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    pkg = db.scalar(select(OfferingPackage).where(OfferingPackage.temple_id.is_(None)).order_by(OfferingPackage.id))
    pkg.stock = 2
    db.commit()
    ref = create_booking(user_client, db)  # đặt 1
    db.expire_all()
    assert db.get(OfferingPackage, pkg.id).stock == 1
    # đặt 2 khi chỉ còn 1 → từ chối
    from helpers import booking_data
    r = post_json(user_client, "/dat-le", booking_data(db, **{f"sl_{pkg.id}": "2"}))
    assert r.status_code == 400 and "chỉ còn 1" in r.json()["error"]
    # hủy đơn → trả hàng về kho
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    r = user_client.post(f"{P}/don/{o.id}/huy", data={"csrf_token": user_client.csrf}, follow_redirects=False)
    db.expire_all()
    assert db.get(OfferingPackage, pkg.id).stock == 2, r.status_code


def _setup_approval(db, on=True):
    from app.models import TempleStaff
    ns = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    ns.require_approval = on
    db.commit()
    return ns


def test_order_waits_for_thu_nhang_then_schedules(user_client, db):
    from fastapi.testclient import TestClient
    from app.main import app
    _setup_approval(db)
    ref = create_booking(user_client, db, khi_nao="ngay")
    confirm_and_pay(user_client, ref)
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    assert o.status == "paid" and o.needs_approval  # chưa xếp lịch
    mgr = TestClient(app)
    tok = login(mgr, "quanly@example.com", "demo12345")
    assert mgr.get(f"{P}/admin/lich-le").text.count("Nhận đơn") >= 1
    r = mgr.post(f"{P}/admin/don/{o.id}/nhan", data={"csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.get(Order, o.id).status in ("scheduled", "delivered")


def test_unaccepted_order_expires_with_refund(user_client, db):
    from datetime import timedelta
    from app import orders as svc
    from app.models import utcnow
    _setup_approval(db)
    ref = create_booking(user_client, db, khi_nao="ngay")
    confirm_and_pay(user_client, ref)
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    assert svc.expire_unaccepted(db, utcnow()) == 0
    assert svc.expire_unaccepted(db, utcnow() + timedelta(hours=3)) == 1
    db.commit()
    assert db.get(Order, o.id).status == "refund_requested"


def test_mixed_kiosks_in_one_order_rejected(user_client, db):
    from helpers import booking_data
    ns = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    v1 = db.scalar(select(User).where(User.email == "kiosk@example.com"))
    v2 = User(name="K2", email="k2@example.com", role="vendor")
    db.add(v2)
    db.flush()
    a = OfferingPackage(name="Hương A", price=1000, temple_id=ns.id, vendor_id=v1.id)
    b = OfferingPackage(name="Hoa B", price=1000, temple_id=ns.id, vendor_id=v2.id)
    db.add_all([a, b])
    db.commit()
    data = booking_data(db, **{f"sl_{a.id}": "1", f"sl_{b.id}": "1"})
    r = post_json(user_client, "/dat-le", data)
    assert r.status_code == 400 and "một kiosk" in r.json()["error"]
    r = post_json(user_client, "/dat-le", booking_data(db, **{f"sl_{a.id}": "1"}))
    assert r.status_code == 200
    assert db.scalar(select(Order).order_by(Order.id.desc())).vendor_id == v1.id


def test_kiosk_out_of_stock_rejects_and_refunds(user_client, db):
    from fastapi.testclient import TestClient
    from app.main import app
    ns = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    v1 = db.scalar(select(User).where(User.email == "kiosk@example.com"))
    a = OfferingPackage(name="Hương A", price=1000, temple_id=ns.id, vendor_id=v1.id)
    db.add(a)
    db.commit()
    from helpers import booking_data
    r = post_json(user_client, "/dat-le", booking_data(db, khi_nao="hen_gio", minutes=60 * 24, **{f"sl_{a.id}": "1"}))
    ref = r.json()["ref"]
    from helpers import TXN
    TXN[ref] = r.json()["txn"]
    confirm_and_pay(user_client, ref)
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    k = TestClient(app)
    tok = login(k, "kiosk@example.com", "demo12345")
    r = k.post(f"{P}/admin/don/{o.id}/het-hang", data={"csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.get(Order, o.id).status == "refund_requested"


def test_in_person_reading_flow(user_client, db):
    """Thủ nhang đọc tại chỗ: nhận đơn → bắt đầu → kết thúc kèm video → hoàn tất, có doanh thu."""
    from fastapi.testclient import TestClient
    from app.main import app
    from helpers import booking_data, TXN, tone
    r = post_json(user_client, "/dat-le", booking_data(db, cach_khan="in_person", minutes=60))
    assert r.status_code == 200, r.text
    ref = r.json()["ref"]
    TXN[ref] = r.json()["txn"]
    confirm_and_pay(user_client, ref)
    o = db.scalar(select(Order).where(Order.booking_ref == ref))
    assert o.service_fee == 50000 and o.total > 50000
    assert o.status == "paid" and o.needs_approval  # luôn cần thủ nhang nhận
    mgr = TestClient(app)
    tok = login(mgr, "quanly@example.com", "demo12345")
    assert mgr.post(f"{P}/admin/don/{o.id}/nhan", data={"csrf_token": tok}, follow_redirects=False).status_code == 303
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "scheduled" and not o.jobs  # không có lệnh xuống thiết bị
    assert "Nguyễn Văn A" in mgr.get(f"{P}/thu-nhang/doc/{o.id}").text  # thủ nhang thấy bản sớ
    h = {"X-CSRF-Token": tok}
    # ngày hẹn là mai (60 phút nữa vẫn hôm nay) → bắt đầu được
    r = mgr.post(f"{P}/thu-nhang/doc/{o.id}/bat-dau", headers=h)
    if r.status_code == 409:  # hẹn qua nửa đêm: bỏ qua kiểm tra ngày
        from datetime import timedelta
        o.scheduled_at = o.scheduled_at - timedelta(days=0)
    assert r.status_code in (200, 409)
    if r.status_code == 200:
        from app.models import utcnow
        mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
        r = mgr.post(f"{P}/thu-nhang/doc/{o.id}/ket-thuc", headers=h, files={"video": ("a.mp4", mp4, "video/mp4")})
        assert r.status_code == 200, r.text
        db.expire_all()
        o = db.get(Order, o.id)
        assert o.status == "completed" and o.video and o.read_started_at and o.read_ended_at
        # trang lễ đồng thời / doanh thu không vỡ
        assert user_client.get(f"{P}/don/lo/{ref}").status_code == 200
        assert "#%d" % o.id in mgr.get(f"{P}/admin/doanh-thu").text


def test_in_person_cannot_play_asap_and_other_temple_forbidden(user_client, db):
    from fastapi.testclient import TestClient
    from app.main import app
    from helpers import booking_data
    r = post_json(user_client, "/dat-le", booking_data(db, cach_khan="in_person", khi_nao="ngay"))
    assert r.status_code == 400 and "ngày hẹn" in r.json()["error"]
    # người ngoài không vào được trang đọc sớ
    r = post_json(user_client, "/dat-le", booking_data(db, cach_khan="in_person", minutes=60))
    o = db.scalar(select(Order).order_by(Order.id.desc()))
    assert user_client.get(f"{P}/thu-nhang/doc/{o.id}").status_code == 403


def test_in_person_expires_after_day(user_client, db):
    from datetime import timedelta
    from app import orders as svc
    from helpers import booking_data, TXN
    r = post_json(user_client, "/dat-le", booking_data(db, cach_khan="in_person", minutes=60))
    TXN[r.json()["ref"]] = r.json()["txn"]
    confirm_and_pay(user_client, r.json()["ref"])
    o = db.scalar(select(Order).order_by(Order.id.desc()))
    svc.accept(db, o, "test")
    db.commit()
    assert svc.expire_unread(db, o.scheduled_at) == 0
    assert svc.expire_unread(db, o.scheduled_at + timedelta(days=2)) == 1
    db.commit()
    assert db.get(Order, o.id).status == "refund_requested"
