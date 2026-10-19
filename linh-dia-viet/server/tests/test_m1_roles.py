"""3 nhóm người dùng: khách hàng, người bán hàng kiosk, người quản lý đền (+ admin hệ thống)."""
from sqlalchemy import select

from app.models import OfferingPackage, Temple, User
from conftest import P, csrf_of, login


def _ngoc_son(db):
    return db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))


def test_new_signup_is_customer(client, db):
    tok = csrf_of(client, f"{P}/dang-ky")
    client.post(f"{P}/dang-ky", data={"name": "Khách", "identifier": "khach@example.com", "password": "abcdefgh",
                                     "csrf_token": tok})
    assert db.scalar(select(User).where(User.email == "khach@example.com")).role == "customer"


def test_customer_has_no_backoffice(user_client):
    assert user_client.get(f"{P}/admin").status_code == 403
    assert user_client.get(f"{P}/admin/goi-le").status_code == 403


def test_vendor_manages_only_own_temple_packages(client, db):
    tok = login(client, "kiosk@example.com", "demo12345")
    ns = _ngoc_son(db)
    other = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    assert client.get(f"{P}/admin").status_code == 200
    assert client.get(f"{P}/admin/den").status_code == 403  # vendor không sửa thông tin đền
    r = client.post(f"{P}/admin/goi-le/moi", data={"name": "Mâm kiosk", "price": "200000", "temple_id": str(ns.id),
                                                  "active": "true", "csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    pkg = db.scalar(select(OfferingPackage).where(OfferingPackage.name == "Mâm kiosk"))
    assert pkg.temple_id == ns.id
    r = client.post(f"{P}/admin/goi-le/moi", data={"name": "X", "price": "1", "temple_id": str(other.id),
                                                  "csrf_token": tok})
    assert r.status_code == 403
    r = client.post(f"{P}/admin/goi-le/moi", data={"name": "X", "price": "1", "temple_id": "", "csrf_token": tok})
    assert r.status_code == 403  # không tạo gói dùng chung
    shared = db.scalar(select(OfferingPackage).where(OfferingPackage.temple_id.is_(None)))
    assert client.get(f"{P}/admin/goi-le/{shared.id}").status_code == 403
    assert "Mâm kiosk" in client.get(f"{P}/admin/goi-le").text
    assert client.get(f"{P}/admin/nguoi-dung").status_code == 403


def test_manager_edits_own_temple_but_not_device(client, db):
    tok = login(client, "quanly@example.com", "demo12345")
    ns = _ngoc_son(db)
    other = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    r = client.post(f"{P}/admin/den/{ns.id}", data={"name": "Đền Ngọc Sơn", "description": "Mô tả mới",
                                                  "device_id": "", "status": "hidden", "csrf_token": tok},
                    follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    ns = _ngoc_son(db)
    assert ns.description == "Mô tả mới"
    assert ns.device_id == "pi-demo-01" and ns.status == "active"  # field chỉ admin được đổi
    assert client.get(f"{P}/admin/den/{other.id}").status_code == 403
    assert client.get(f"{P}/admin/den/moi").status_code == 403


def test_admin_assigns_roles_and_locks_user(admin_client, db, user):
    c = admin_client
    ns = _ngoc_son(db)
    r = c.post(f"{P}/admin/nguoi-dung/{user.id}", data={"name": user.name, "role": "temple_manager",
                                                       "temple_ids": [str(ns.id)], "active": "1",
                                                       "csrf_token": c.csrf}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    u = db.get(User, user.id)
    assert u.role == "temple_manager" and u.temple_ids == {ns.id}
    # lưu lại cùng đền không lỗi trùng khoá; đổi về khách hàng thì bỏ gán đền
    c.post(f"{P}/admin/nguoi-dung/{user.id}", data={"name": user.name, "role": "temple_manager",
                                                   "temple_ids": [str(ns.id)], "active": "1", "csrf_token": c.csrf})
    c.post(f"{P}/admin/nguoi-dung/{user.id}", data={"name": user.name, "role": "customer", "temple_ids": [str(ns.id)],
                                                   "csrf_token": c.csrf})
    db.expire_all()
    u = db.get(User, user.id)
    assert u.role == "customer" and u.temple_ids == set() and not u.active
    tok = csrf_of(c)
    c.post(f"{P}/dang-xuat", data={"csrf_token": c.csrf})
    r = c.post(f"{P}/dang-nhap", data={"identifier": "a@example.com", "password": "matkhau123",
                                      "csrf_token": csrf_of(c)})
    assert r.status_code == 400  # tài khoản bị khóa


def test_admin_cannot_demote_self(admin_client, db):
    admin = db.scalar(select(User).where(User.role == "admin"))
    r = admin_client.post(f"{P}/admin/nguoi-dung/{admin.id}", data={"name": "x", "role": "customer", "active": "1",
                                                                  "csrf_token": admin_client.csrf})
    assert r.status_code == 400


def test_admin_creates_vendor(admin_client, db):
    c = admin_client
    ns = _ngoc_son(db)
    r = c.post(f"{P}/admin/nguoi-dung/moi", data={"name": "Kiosk 2", "identifier": "0901234567", "password": "abcdefgh",
                                                "role": "vendor", "temple_ids": [str(ns.id)], "active": "1",
                                                "csrf_token": c.csrf}, follow_redirects=False)
    assert r.status_code == 303
    v = db.scalar(select(User).where(User.phone == "0901234567"))
    assert v.role == "vendor" and v.temple_ids == {ns.id}
