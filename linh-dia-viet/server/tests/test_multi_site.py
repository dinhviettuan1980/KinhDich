"""Một lần đặt ở nhiều đền: cùng giờ phát, điện thoại làm thiết bị đền (kênh HTTP), trang "Lễ đồng thời"."""
import re
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

from app import devices
from app.models import Order, utcnow
from conftest import P
from helpers import TXN, booking_data, confirm_and_pay, create_booking

TWO = ("den-ngoc-son", "chua-tran-quoc")


def auth(device_id: str) -> dict:
    token = "dev-device-token-change-me" if device_id == "pi-demo-01" else "tok-" + device_id[-1]
    return {"Authorization": f"Bearer {token}", "X-Device-Id": device_id}


def book_asap(user_client, db, temples=TWO):
    ref = create_booking(user_client, db, temples=temples, khi_nao="ngay")
    confirm_and_pay(user_client, ref)
    db.expire_all()
    return ref, list(db.scalars(select(Order).where(Order.booking_ref == ref).order_by(Order.id)))


def test_asap_multi_temple_same_play_time(user_client, db):
    ref, orders = book_asap(user_client, db)
    assert len(orders) == 2 and all(o.status == "scheduled" for o in orders)
    assert orders[0].scheduled_at == orders[1].scheduled_at          # cùng một giờ phát
    assert orders[0].jobs[-1].play_at == orders[1].jobs[-1].play_at
    # chừa đủ thời gian cho thiết bị chậm tải file
    assert orders[0].scheduled_at >= utcnow() - timedelta(seconds=5)


def test_phone_poll_gets_job_and_acks(user_client, client, db):
    ref, orders = book_asap(user_client, db)
    o = orders[1]
    dev_id = o.temple.device_id
    r = client.post(f"{P}/api/device/poll", json={"net": "wifi", "battery": 80, "kind": "phone"}, headers=auth(dev_id))
    assert r.status_code == 200
    body = r.json()
    assert len(body["jobs"]) == 1 and body["jobs"][0]["job_id"] == o.jobs[-1].id
    assert body["jobs"][0]["audio_url"] and body["jobs"][0]["sha256"] == o.audio_sha256
    assert "server_time" in body and body["locked"] is False
    db.expire_all()
    assert db.get(type(o.temple.device), dev_id).online is True
    assert db.get(type(o.temple.device), dev_id).last_status["kind"] == "phone"
    # ACK qua HTTP, thiết bị tự báo giờ phát
    ts = (utcnow() + timedelta(seconds=2)).isoformat()
    for state in ("received", "downloaded", "playing"):
        a = client.post(f"{P}/api/device/ack", json={"job_id": o.jobs[-1].id, "state": state, "ts": ts},
                        headers=auth(dev_id))
        assert a.status_code == 200
    db.expire_all()
    o = db.get(Order, o.id)
    assert o.status == "playing" and abs((o.jobs[-1].playing_at - utcnow()).total_seconds() - 2) < 3
    # job đã phát thì không giao lại
    assert client.post(f"{P}/api/device/poll", json={}, headers=auth(dev_id)).json()["jobs"] == []


def test_phone_poll_rejects_bad_token_and_other_devices_jobs(user_client, client, db):
    ref, orders = book_asap(user_client, db)
    bad = client.post(f"{P}/api/device/poll", json={}, headers={**auth("pi-demo-01"), "Authorization": "Bearer x"})
    assert bad.status_code == 401
    other = orders[1].temple.device_id
    # thiết bị A không ACK được job của thiết bị B
    client.post(f"{P}/api/device/ack", json={"job_id": orders[0].jobs[-1].id, "state": "playing"}, headers=auth(other))
    db.expire_all()
    assert db.get(Order, orders[0].id).status == "scheduled"


def test_phone_control_commands_and_lock(user_client, client, db):
    ref, orders = book_asap(user_client, db)
    dev_id = orders[1].temple.device_id
    devices.send_command(db, dev_id, {"type": "test_tone"}, "admin")
    db.commit()
    c = client.post(f"{P}/api/device/poll", json={}, headers=auth(dev_id)).json()["control"]
    assert [x["type"] for x in c] == ["test_tone"]
    assert client.post(f"{P}/api/device/poll", json={}, headers=auth(dev_id)).json()["control"] == []
    devices.set_system_lock(db, True, "admin")
    db.commit()
    locked = client.post(f"{P}/api/device/poll", json={}, headers=auth(dev_id)).json()
    assert locked["locked"] is True and locked["jobs"] == []


def test_group_page_shows_simultaneous_proof(user_client, client, db):
    ref, orders = book_asap(user_client, db)
    r = user_client.get(f"{P}/don/lo/{ref}")
    assert r.status_code == 200 and "2 nơi" in r.text
    base = utcnow() - timedelta(seconds=30)
    for i, o in enumerate(orders):
        dev_id = o.temple.device_id
        for state, shift in (("received", 0), ("downloaded", 0), ("playing", 0.8 * i), ("done", 10 + 0.8 * i)):
            client.post(f"{P}/api/device/ack", json={"job_id": o.jobs[-1].id, "state": state,
                                                     "ts": (base + timedelta(seconds=shift)).isoformat()},
                        headers=auth(dev_id))
    page = user_client.get(f"{P}/don/lo/{ref}/trang-thai").text
    assert "Đã khấn đồng thời tại 2 nơi" in page and "0.8 giây" in page
    assert "Raspberry Pi" in page or "Điện thoại Android" in page
    # lịch sử gom nhóm + người khác không xem được
    assert f"/don/lo/{ref}" in user_client.get(f"{P}/don").text
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as anon:  # chưa đăng nhập thì không xem được dữ liệu cá nhân
        assert anon.get(f"{P}/don/lo/{ref}", follow_redirects=False).status_code in (303, 401, 404)


def test_webm_converted_to_mp4(user_client, client, db, tmp_path):
    import subprocess
    ref, orders = book_asap(user_client, db)
    o, dev_id = orders[1], orders[1].temple.device_id
    webm = tmp_path / "v.webm"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=400:duration=2", "-c:v", "libvpx", "-c:a", "libopus",
                    str(webm)], check=True)
    r = client.post(f"{P}/api/device/evidence", data={"job_id": o.jobs[-1].id, "phase": "video"},
                    files={"file": ("v.webm", webm.read_bytes(), "video/webm")}, headers=auth(dev_id))
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Order, o.id).video is not None


# ---------- Mâm lễ riêng từng đền ----------

def _pkgs(db):
    from app.models import OfferingPackage
    return list(db.scalars(select(OfferingPackage).where(OfferingPackage.temple_id.is_(None))
                           .order_by(OfferingPackage.id)))


def _book(user_client, db, extra, temples=TWO):
    data = booking_data(db, temples=temples, khi_nao="ngay")
    data.update(extra)
    r = user_client.post(f"{P}/dat-le", data=data, headers={"X-CSRF-Token": user_client.csrf})
    if r.status_code == 200:
        TXN[r.json()["ref"]] = r.json()["txn"]
    return r


def _items(db, ref):
    return {o.temple.slug: sorted((i.package_id, i.qty) for i in o.items)
            for o in db.scalars(select(Order).where(Order.booking_ref == ref))}


def test_second_temple_same_as_first_by_default(user_client, db):
    a, b = _pkgs(db)[:2]
    r = _book(user_client, db, {f"sl_{a.id}": "1", f"sl_{b.id}": "2"})
    assert r.status_code == 200, r.text
    it = _items(db, r.json()["ref"])
    assert it["den-ngoc-son"] == it["chua-tran-quoc"] == sorted([(a.id, 1), (b.id, 2)])


def test_second_temple_own_tray(user_client, db):
    a, b = _pkgs(db)[:2]
    from app.models import Temple
    t2 = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    r = _book(user_client, db, {f"sl_{a.id}": "1", f"mam_{t2.id}": "rieng", f"sx_{t2.id}_{b.id}": "3"})
    assert r.status_code == 200, r.text
    ref = r.json()["ref"]
    assert _items(db, ref) == {"den-ngoc-son": [(a.id, 1)], "chua-tran-quoc": [(b.id, 3)]}
    totals = {o.temple.slug: o.total for o in db.scalars(select(Order).where(Order.booking_ref == ref))}
    assert totals["den-ngoc-son"] == a.price and totals["chua-tran-quoc"] == b.price * 3
    # bài khấn của mỗi đền ghi đúng lễ vật của đền đó
    confirm_and_pay(user_client, ref)
    db.expire_all()
    scripts = {o.temple.slug: o.script_text for o in db.scalars(select(Order).where(Order.booking_ref == ref))}
    assert b.name.lower() in scripts["chua-tran-quoc"].lower()
    assert scripts["den-ngoc-son"] != scripts["chua-tran-quoc"]


def test_third_temple_copies_second_custom_tray(user_client, db):
    from app.models import Temple
    a, b = _pkgs(db)[:2]
    t2 = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    t3 = db.scalar(select(Temple).where(Temple.slug == "den-ba-chua-xu"))
    r = _book(user_client, db, {f"sl_{a.id}": "1", f"mam_{t2.id}": "rieng", f"sx_{t2.id}_{b.id}": "2",
                                f"mam_{t3.id}": f"giong_{t2.id}"}, temples=("den-ngoc-son", "chua-tran-quoc", "den-ba-chua-xu"))
    assert r.status_code == 200, r.text
    it = _items(db, r.json()["ref"])
    assert it["den-ba-chua-xu"] == it["chua-tran-quoc"] == [(b.id, 2)] and it["den-ngoc-son"] == [(a.id, 1)]


def test_circular_copy_falls_back_and_empty_custom_rejected(user_client, db):
    from app.models import Temple
    a, _b = _pkgs(db)[:2]
    t2 = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    t3 = db.scalar(select(Temple).where(Temple.slug == "den-ba-chua-xu"))
    r = _book(user_client, db, {f"sl_{a.id}": "1", f"mam_{t2.id}": f"giong_{t3.id}", f"mam_{t3.id}": f"giong_{t2.id}"},
              temples=("den-ngoc-son", "chua-tran-quoc", "den-ba-chua-xu"))
    assert r.status_code == 200
    assert all(v == [(a.id, 1)] for v in _items(db, r.json()["ref"]).values())
    bad = _book(user_client, db, {f"sl_{a.id}": "1", f"mam_{t2.id}": "rieng"})
    assert bad.status_code == 400 and "mâm riêng" in bad.json()["error"]


def test_package_options_renders_per_temple_choice(user_client, db):
    from app.models import Temple
    t1 = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    t2 = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    html = user_client.get(f"{P}/dat-le/goi-le?den={t1.id}&den={t2.id}").text
    assert f'name="mam_{t2.id}"' in html and "Giống mâm đền" in html and "Tự chọn mâm mới" in html
    assert 'name="mam_' not in user_client.get(f"{P}/dat-le/goi-le?den={t1.id}").text


def test_booking_form_prechosen_multi_shows_tray_choice(user_client, db):
    from app.models import Temple
    ids = [db.scalar(select(Temple).where(Temple.slug == x)).id for x in TWO]
    html = user_client.get(f"{P}/dat-le?den={ids[0]}&den={ids[1]}").text
    assert f'name="mam_{ids[1]}"' in html and 'data-scope="base"' in html


def test_reorder_restores_per_temple_trays(user_client, db):
    from app.models import Temple
    a, b = _pkgs(db)[:2]
    t2 = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    r = _book(user_client, db, {f"sl_{a.id}": "1", f"mam_{t2.id}": "rieng", f"sx_{t2.id}_{b.id}": "3"})
    first = db.scalar(select(Order).where(Order.booking_ref == r.json()["ref"]).order_by(Order.id))
    html = user_client.get(f"{P}/dat-le?tu_don={first.id}").text
    assert 'value="rieng" selected' in html and f'name="sx_{t2.id}_{b.id}" value="3"' in html


def test_phone_page_checks_camera_before_capture(client):
    """Camera điện thoại đứng hình sau khi màn hình tắt (demo thật: 3 ảnh chụp thử giống hệt từng byte) →
    phone.js phải kiểm tra/mở lại camera trước mỗi lần chụp và trước khi quay; trang nạp đúng phiên bản script."""
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "phone.js").read_text(encoding="utf-8")
    version = re.search(r'const VERSION = "phone-(\d+)"', js).group(1)
    assert f"phone.js?v={version}" in client.get(f"{P}/may").text
    shoot = js[js.index("async function shoot("):]
    assert shoot.index("ensureCamera()") < shoot.index("photo()")
    run = js[js.index("async function runJob("):]
    assert run.index("ensureCamera()") < run.index("startRecording()")
    assert "frameMoving" in js and '"ended"' in js


def test_admin_switches_phone_camera(user_client, client, db, admin_client):
    """Điện thoại đặt trên giá ngược chiều mâm (demo thật) → admin đổi sang camera trước từ xa, không phải chạm máy."""
    ref, orders = book_asap(user_client, db)
    dev_id = orders[1].temple.device_id
    client.post(f"{P}/api/device/poll", json={"kind": "phone", "camera": "phone"}, headers=auth(dev_id))
    page = admin_client.get(f"{P}/admin/thiet-bi").text
    assert page.count("camera_front") == 1  # chỉ điện thoại có nút đổi camera, Pi không có
    r = admin_client.post(f"{P}/admin/thiet-bi/{dev_id}/lenh", data={"csrf_token": admin_client.csrf, "type": "camera_front"})
    assert r.status_code == 200 and "camera trước" in r.text
    c = client.post(f"{P}/api/device/poll", json={}, headers=auth(dev_id)).json()["control"]
    assert [(x["type"], x["camera"]) for x in c] == [("config", "user")]
    assert admin_client.post(f"{P}/admin/thiet-bi/{dev_id}/lenh",
                             data={"csrf_token": admin_client.csrf, "type": "reboot"}).status_code == 400


def test_phone_reports_step_and_log_and_record_toggle(user_client, client, db, admin_client):
    """Demo thật: điện thoại treo ngay lúc bắt đầu quay mà không thấy được màn hình → máy gửi bước đang làm + nhật ký
    về server (admin xem từ xa); admin tắt/bật quay video cho máy yếu."""
    ref, orders = book_asap(user_client, db)
    dev_id = orders[1].temple.device_id
    status = {"kind": "phone", "camera": "phone", "record": True, "step": "chờ giờ phát",
              "log": [f"00:00:{i:02d} dòng {i}" for i in range(30)] + ["x" * 500]}
    client.post(f"{P}/api/device/poll", json=status, headers=auth(dev_id))
    db.expire_all()
    from app.models import Device
    st = db.get(Device, dev_id).last_status
    assert st["step"] == "chờ giờ phát" and len(st["log"]) == 20 and len(st["log"][-1]) == 160
    page = admin_client.get(f"{P}/admin/thiet-bi").text
    assert "Nhật ký điện thoại" in page and "đang: chờ giờ phát" in page and "record_off" in page
    admin_client.post(f"{P}/admin/thiet-bi/{dev_id}/lenh", data={"csrf_token": admin_client.csrf, "type": "record_off"})
    c = client.post(f"{P}/api/device/poll", json={"log": "không phải danh sách"}, headers=auth(dev_id)).json()["control"]
    assert [(x["type"], x.get("record")) for x in c] == [("config", False)]
    db.expire_all()
    assert db.get(Device, dev_id).last_status["log"] is None
