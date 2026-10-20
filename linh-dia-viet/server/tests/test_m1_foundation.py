import logging
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, select

from app.db import Base
from app.models import AuditLog, Device, OfferingPackage, Temple, User
from conftest import P, csrf_of, login


def test_seed_data(db):
    assert db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son")).device_id == "pi-demo-01"
    assert len(db.scalars(select(Temple)).all()) == 3
    assert len(db.scalars(select(OfferingPackage)).all()) == 4
    assert db.get(Device, "pi-demo-01").token_hash != "dev-device-token-change-me"
    admin = db.scalar(select(User).where(User.role == "admin"))
    assert admin.password_hash.startswith("$argon2")


def test_home_lists_temples_and_search(client):
    r = client.get(f"{P}/")
    assert r.status_code == 200
    assert "Đền Ngọc Sơn" in r.text and "Chùa Trấn Quốc" in r.text
    r = client.get(f"{P}/?q=An Giang", headers={"HX-Request": "true"})
    assert "Bà Chúa Xứ" in r.text and "Ngọc Sơn" not in r.text


def test_root_redirects_to_prefix(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == f"{P}/"


def test_temple_detail(client):
    r = client.get(f"{P}/den/den-ngoc-son")
    assert r.status_code == 200 and "Lễ hoa quả" in r.text
    assert client.get(f"{P}/den/khong-co").status_code == 404


def test_register_login_logout(client, db):
    tok = csrf_of(client, f"{P}/dang-ky")
    r = client.post(f"{P}/dang-ky", data={"name": "Trần B", "identifier": "0912 345 678", "password": "abcdefgh",
                                         "csrf_token": tok}, follow_redirects=False)
    assert r.status_code == 303
    u = db.scalar(select(User).where(User.phone == "0912345678"))
    assert u and u.password_hash.startswith("$argon2")
    tok = csrf_of(client, f"{P}/")
    client.post(f"{P}/dang-xuat", data={"csrf_token": tok})
    login(client, "+84912345678", "abcdefgh")


def test_wrong_password_and_rate_limit(client, user):
    tok = csrf_of(client)
    codes = [client.post(f"{P}/dang-nhap", data={"identifier": "a@example.com", "password": "sai",
                                                 "csrf_token": tok}).status_code for _ in range(11)]
    assert codes[:10] == [400] * 10 and codes[10] == 429


def test_csrf_required(client, user):
    r = client.post(f"{P}/dang-nhap", data={"identifier": "a@example.com", "password": "matkhau123"})
    assert r.status_code == 403


def test_otp_login_creates_user(client, db, caplog):
    tok = csrf_of(client)
    with caplog.at_level(logging.WARNING, logger="linhdia.auth"):
        r = client.post(f"{P}/otp/gui", data={"identifier": "moi@example.com", "csrf_token": tok})
    assert r.status_code == 200
    code = re.search(r"OTP giả lập cho moi@example.com: (\d{6})", caplog.text).group(1)
    r = client.post(f"{P}/otp/xac-nhan", data={"identifier": "moi@example.com", "code": "000000" if code != "000000" else "111111",
                                              "csrf_token": tok})
    assert r.status_code == 400
    r = client.post(f"{P}/otp/xac-nhan", data={"identifier": "moi@example.com", "code": code, "csrf_token": tok},
                    follow_redirects=False)
    assert r.status_code == 303
    assert db.scalar(select(User).where(User.email == "moi@example.com"))


def test_admin_requires_role(user_client):
    assert user_client.get(f"{P}/admin/den").status_code == 403


def test_admin_redirects_anonymous(client):
    r = client.get(f"{P}/admin/den", follow_redirects=False)
    assert r.status_code == 303 and "/dang-nhap?next=" in r.headers["location"]


def test_admin_crud_temple_and_package(admin_client, db):
    c = admin_client
    r = c.post(f"{P}/admin/den/moi", data={"name": "Phủ Tây Hồ", "province": "Hà Nội", "deity": "Thánh Mẫu Liễu Hạnh",
                                         "status": "active", "device_id": "", "csrf_token": c.csrf}, follow_redirects=False)
    assert r.status_code == 303
    t = db.scalar(select(Temple).where(Temple.slug == "phu-tay-ho"))
    assert t and t.deity == "Thánh Mẫu Liễu Hạnh"
    r = c.post(f"{P}/admin/goi-le/moi", data={"name": "Lễ Mẫu", "price": "300000", "temple_id": str(t.id),
                                            "active": "true", "csrf_token": c.csrf}, follow_redirects=False)
    assert r.status_code == 303
    assert "Lễ Mẫu" in c.get(f"{P}/den/phu-tay-ho").text
    assert "Lễ Mẫu" not in c.get(f"{P}/den/den-ngoc-son").text  # gói riêng không lộ sang đền khác
    db.expire_all()
    assert db.scalar(select(AuditLog).where(AuditLog.action == "package.save"))


def test_alembic_matches_models(tmp_path):
    url = f"sqlite:///{tmp_path}/mig.db"
    server = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "alembic", "-x", "noop=1", "upgrade", "head"], cwd=server, check=True,
                   env={"DATABASE_URL": url, "PATH": "/usr/bin:/bin"}, capture_output=True)
    insp = inspect(create_engine(url))
    for table in Base.metadata.sorted_tables:
        cols = {c["name"] for c in insp.get_columns(table.name)}
        assert cols == {c.name for c in table.columns}, table.name


def test_runtime_files_not_gitignored():
    """File dữ liệu trong app/ phải được commit (lỗi cũ: 'data/' trong .gitignore nuốt mất app/data/)."""
    server = Path(__file__).resolve().parents[1]
    for f in (server / "app").rglob("*"):
        if f.is_file() and "__pycache__" not in f.parts:
            r = subprocess.run(["git", "check-ignore", "-q", str(f)], cwd=server)
            assert r.returncode == 1, f"{f} bị .gitignore bỏ qua"
