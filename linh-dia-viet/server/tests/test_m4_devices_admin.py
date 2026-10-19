import re

from sqlalchemy import select

from app.config import get_settings
from app.models import AuditLog, Device
from conftest import P
from ld_agent.camera import Camera


def _photo(tmp_path):
    p = tmp_path / "x.jpg"
    Camera("simulate").capture(p, "t")
    return p.read_bytes()


def test_create_rotate_revoke_device(admin_client, db, tmp_path, monkeypatch):
    pw = tmp_path / "extra" / "devices.passwd"
    monkeypatch.setattr(get_settings(), "mqtt_passwd_file", str(pw))
    c = admin_client
    r = c.post(f"{P}/admin/thiet-bi/moi", data={"device_id": "pi-ngoc-son-02", "name": "Ngọc Sơn 2",
                                              "csrf_token": c.csrf}, follow_redirects=True)
    token = re.search(r"LD_DEVICE_TOKEN=([\w\-]+)", r.text).group(1)
    assert "LD_DEVICE_TOKEN" not in c.get(f"{P}/admin/thiet-bi").text  # chỉ hiện 1 lần
    dev = db.get(Device, "pi-ngoc-son-02")
    assert dev.token_hash != token and token not in pw.read_text()
    assert re.fullmatch(r"pi-ngoc-son-02:\$7\$101\$[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+\n", pw.read_text())
    assert "pi-demo-01" not in pw.read_text()  # thiết bị demo lấy từ env của mosquitto
    up = lambda tok: c.post(f"{P}/api/device/evidence", headers={"Authorization": f"Bearer {tok}",  # noqa: E731
                                                                 "X-Device-Id": "pi-ngoc-son-02"},
                            data={"phase": "test"}, files={"file": ("a.jpg", _photo(tmp_path), "image/jpeg")})
    assert up(token).status_code == 200
    r = c.post(f"{P}/admin/thiet-bi/pi-ngoc-son-02/token", data={"action": "rotate", "csrf_token": c.csrf},
               follow_redirects=True)
    token2 = re.search(r"LD_DEVICE_TOKEN=([\w\-]+)", r.text).group(1)
    assert up(token).status_code == 401 and up(token2).status_code == 200
    c.post(f"{P}/admin/thiet-bi/pi-ngoc-son-02/token", data={"action": "revoke", "csrf_token": c.csrf})
    assert up(token2).status_code == 401 and pw.read_text() == ""
    assert db.scalar(select(AuditLog).where(AuditLog.action == "device.token_revoke"))


def test_invalid_device_id(admin_client):
    r = admin_client.post(f"{P}/admin/thiet-bi/moi", data={"device_id": "Bad ID!", "csrf_token": admin_client.csrf})
    assert r.status_code == 400
    r = admin_client.post(f"{P}/admin/thiet-bi/moi", data={"device_id": "ld-server", "csrf_token": admin_client.csrf})
    assert r.status_code == 400


def test_admin_device_commands(admin_client, db):
    c = admin_client
    for t in ("test_tone", "capture", "stop"):
        r = c.post(f"{P}/admin/thiet-bi/pi-demo-01/lenh", data={"type": t, "csrf_token": c.csrf}, follow_redirects=False)
        assert r.status_code == 303
    assert [p["type"] for d, p in db.bus.sent] == ["test_tone", "capture", "stop"]
    assert len(db.scalars(select(AuditLog).where(AuditLog.action == "device.cmd")).all()) == 3
    assert c.post(f"{P}/admin/thiet-bi/pi-demo-01/lenh", data={"type": "rm -rf", "csrf_token": c.csrf}).status_code == 400


def test_device_page_and_test_photo(admin_client, db, tmp_path):
    c = admin_client
    r = c.post(f"{P}/api/device/evidence", headers={"Authorization": "Bearer dev-device-token-change-me",
                                                     "X-Device-Id": "pi-demo-01"},
               data={"phase": "test"}, files={"file": ("a.jpg", _photo(tmp_path), "image/jpeg")})
    assert r.status_code == 200
    page = c.get(f"{P}/admin/thiet-bi").text
    assert "pi-demo-01" in page and "Đền Ngọc Sơn" in page and "anh-thu" in page
    assert c.get(f"{P}/admin/thiet-bi/pi-demo-01/anh-thu").headers["content-type"] == "image/jpeg"


def test_staff_cannot_manage_devices(client, db):
    from conftest import login
    tok = login(client, "quanly@example.com", "demo12345")
    assert client.get(f"{P}/admin/thiet-bi").status_code == 403
    assert client.post(f"{P}/admin/thiet-bi/pi-demo-01/lenh", data={"type": "stop", "csrf_token": tok}).status_code == 403


def test_cli_add_device(db, capsys):
    from app.cli import main
    main(["add-device", "pi-cli-01", "CLI"])
    out = capsys.readouterr().out
    assert "LD_DEVICE_ID=pi-cli-01" in out and "LD_DEVICE_TOKEN=" in out
    db.expire_all()
    assert db.get(Device, "pi-cli-01").mqtt_hash.startswith("$7$")
