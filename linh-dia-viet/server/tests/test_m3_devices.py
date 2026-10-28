"""Tích hợp server ↔ pi-agent (--simulate) qua InMemoryDeviceBus, HTTP qua TestClient."""
import time
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import devices
from app.config import get_settings
from app.models import AuditLog, Device, DeviceJob, Order, utcnow
from conftest import P
from helpers import confirm_and_pay, create_booking
from ld_agent.agent import Agent
from ld_agent.camera import Camera
from ld_agent.config import Config
from ld_agent.player import SimPlayer
from ld_agent.transport import InMemoryTransport


@pytest.fixture
def setup(user_client, db, tmp_path):
    """Đơn đã thanh toán ở Đền Ngọc Sơn (pi-demo-01) + agent giả lập nối với server."""
    ref = create_booking(user_client, db)
    confirm_and_pay(user_client, ref)
    db.expire_all()
    order = db.scalar(select(Order).where(Order.booking_ref == ref))
    clock = {"t": time.time()}
    cfg = Config(server_url=f"http://testserver{P}", device_id="pi-demo-01", device_token="dev-device-token-change-me",
                 data_dir=tmp_path / "pi", simulate=True, simulate_play_seconds=5,
                 quiet_start=__import__("datetime").time(0, 0), quiet_end=__import__("datetime").time(0, 0))
    agent = Agent(cfg, InMemoryTransport(db.bus, "pi-demo-01"), user_client, SimPlayer(5), Camera("simulate"),
                  clock=lambda: clock["t"])
    agent.start()
    return order, agent, clock


def move_play_time(db, order, seconds_from_now=5):
    at = utcnow() + timedelta(seconds=seconds_from_now)
    order.scheduled_at = at
    order.jobs[-1].play_at = at
    db.commit()
    return at


def run(db, agent, clock, t=None):
    """1 vòng: server tick → chuyển message → agent tick → chuyển message."""
    if t is not None:
        clock["t"] = t
    devices.tick(db)
    db.commit()
    db.bus.pump()
    agent.tick(clock["t"])
    db.bus.pump()
    db.expire_all()


def test_job_created_when_scheduled(setup, db):
    order, agent, clock = setup
    job = order.jobs[-1]
    assert job.state == "queued" and job.device_id == "pi-demo-01" and job.play_at == order.scheduled_at
    run(db, agent, clock)
    assert db.bus.sent == []  # giờ hẹn còn xa (> 10 phút) → chưa gửi


def test_end_to_end_to_completed(setup, db, user_client):
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    cmd = db.bus.sent[-1][1]
    assert cmd["type"] == "play" and cmd["sha256"] == order.audio_sha256 and "/files/tts/" in cmd["audio_url"]
    assert "ho_ten" not in str(cmd) and "Nguyễn Văn A" not in str(cmd)  # thiết bị không nhận dữ liệu cá nhân
    assert cmd["tray"] == {"items": [{"name": "Hương (nhang)", "unit": "bó", "qty": 1}], "temple": "Đền Ngọc Sơn"}
    o = db.get(Order, order.id)
    assert o.status == "delivered" and o.jobs[-1].state == "downloaded"
    assert [e.note for e in o.evidence] == ["before"]
    run(db, agent, clock, at.timestamp() + 0.5)
    o = db.get(Order, order.id)
    assert o.status == "playing" and {e.note for e in o.evidence} == {"before", "start"}
    run(db, agent, clock, at.timestamp() + 6)
    assert db.get(Order, order.id).status == "played"
    run(db, agent, clock, at.timestamp() + 40)
    o = db.get(Order, order.id)
    assert o.status == "completed"
    assert [e.status for e in o.events][-6:] == ["scheduled", "delivered", "playing", "played", "evidence_received",
                                                  "completed"]
    page = user_client.get(f"{P}/don/{o.id}")
    assert "Ảnh mâm lễ" in page.text and "Hoàn tất" in page.text
    ev = o.evidence[0]
    assert user_client.get(f"{P}/don/{o.id}/anh/{ev.id}").headers["content-type"] == "image/jpeg"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "device.cmd", AuditLog.target == "device:pi-demo-01"))


def test_status_marks_device_online(setup, db, user_client):
    client = user_client
    order, agent, clock = setup
    agent.publish_status(clock["t"])
    db.bus.pump()
    db.expire_all()
    dev = db.get(Device, "pi-demo-01")
    assert dev.online and dev.net_type == "wifi" and dev.version
    assert "Đang trực tuyến" in client.get(f"{P}/").text
    devices.handle_status(db, "pi-demo-01", {"online": False})  # LWT
    assert not dev.online


def test_device_error_fails_order_and_resend(setup, db):
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    agent.on_cmd({"type": "stop"})
    run(db, agent, clock, at.timestamp() + 1)  # bắt đầu phát
    agent.on_cmd({"type": "stop"})
    db.bus.pump()
    db.expire_all()
    o = db.get(Order, order.id)
    assert o.status == "failed" and "Dừng theo lệnh" in o.note
    devices.resend(db, o, "user:1")
    db.commit()
    o = db.get(Order, order.id)
    assert o.status == "scheduled" and len(o.jobs) == 2 and o.jobs[0].state == "error"
    db.bus.pump()
    assert agent.store.get_job(o.jobs[-1].id)["state"] == "received"


def test_offline_device_times_out(setup, db):
    order, agent, clock = setup
    agent.transport.online = False
    move_play_time(db, order, seconds_from_now=-(get_settings().play_grace_seconds + 400))
    devices.tick(db)
    db.commit()
    o = db.get(Order, order.id)
    assert o.status == "failed" and "offline" in o.note


def test_late_ack_after_timeout_recovers(setup, db):
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    agent.transport.online = False  # mất mạng ngay sau khi tải xong
    clock["t"] = at.timestamp() + 1
    agent.tick(clock["t"])
    agent.tick(at.timestamp() + 7)
    o = db.get(Order, order.id)
    devices.tick(db, now=at + timedelta(hours=1))  # vòng kiểm tra đánh dấu failed
    db.commit()
    assert db.get(Order, order.id).status == "failed"
    agent.transport.online = True
    agent.tick(at.timestamp() + 8)  # ACK bù
    db.bus.pump()
    db.expire_all()
    assert db.get(Order, order.id).status == "played"


def test_reject_after_dispatch_sends_cancel(setup, db):
    order, agent, clock = setup
    move_play_time(db, order, seconds_from_now=500)
    agent.transport.online = False  # lệnh đã gửi nhưng thiết bị chưa xác nhận → đơn vẫn 'scheduled'
    run(db, agent, clock)
    o = db.get(Order, order.id)
    assert o.status == "scheduled" and o.jobs[-1].sent_at
    from app import orders as svc
    svc.reject(db, o, "user:1", "Đền đóng cửa")
    db.commit()
    assert db.bus.sent[-1][1] == {"type": "cancel", "job_id": o.jobs[-1].id}
    assert o.jobs[-1].state == "cancelled" and o.status == "refund_requested"
    devices.handle_ack(db, "pi-demo-01", {"job_id": o.jobs[-1].id, "state": "done"})  # ACK muộn bị bỏ qua
    assert o.status == "refund_requested"


def test_evidence_timeout_completes(setup, db):
    order, agent, clock = setup
    at = move_play_time(db, order)
    agent.camera = Camera("none")  # camera hỏng
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 1)
    run(db, agent, clock, at.timestamp() + 7)
    assert db.get(Order, order.id).status == "played"
    devices.tick(db, now=utcnow() + timedelta(seconds=get_settings().evidence_timeout_seconds + 5))
    db.commit()
    o = db.get(Order, order.id)
    assert o.status == "completed" and "Không nhận được ảnh" in o.note


def test_signed_url_and_device_auth(setup, db, client, tmp_path):
    order, agent, clock = setup
    move_play_time(db, order)
    run(db, agent, clock)
    url = db.bus.sent[-1][1]["audio_url"].replace("http://testserver", "")
    assert client.get(url).status_code == 200
    assert client.get(url.replace("sig=", "sig=0")).status_code == 403
    assert client.get(f"{P}/files/{order.audio_key}").status_code == 422  # thiếu chữ ký
    up = f"{P}/api/device/evidence"
    good = {"Authorization": "Bearer dev-device-token-change-me", "X-Device-Id": "pi-demo-01"}
    job_id = order.jobs[-1].id
    jpg = (tmp_path / "pi" / "photos")
    photo = Camera("simulate")
    photo.capture(tmp_path / "x.jpg", "t")
    data = (tmp_path / "x.jpg").read_bytes()
    r = client.post(up, headers={**good, "Authorization": "Bearer sai"}, data={"job_id": job_id, "phase": "after"},
                    files={"file": ("a.jpg", data, "image/jpeg")})
    assert r.status_code == 401
    r = client.post(up, headers=good, data={"job_id": job_id, "phase": "after"},
                    files={"file": ("a.jpg", b"GIF89a....", "image/jpeg")})
    assert r.status_code == 415
    r = client.post(up, headers={"Authorization": "Bearer tok-2", "X-Device-Id": "pi-test-02"},
                    data={"job_id": job_id, "phase": "after"}, files={"file": ("a.jpg", data, "image/jpeg")})
    assert r.status_code == 404  # job của thiết bị khác
    db.get(Device, "pi-demo-01").revoked = True
    db.commit()
    r = client.post(up, headers=good, data={"job_id": job_id, "phase": "after"},
                    files={"file": ("a.jpg", data, "image/jpeg")})
    assert r.status_code == 401  # token đã thu hồi


def test_ack_from_wrong_device_ignored(setup, db):
    order, agent, clock = setup
    job = order.jobs[-1]
    devices.handle_ack(db, "pi-test-02", {"job_id": job.id, "state": "done"})
    assert db.get(Order, order.id).status == "scheduled"


def test_concurrent_schedule_creates_one_job(user_client, db, monkeypatch):
    """Lỗi thật trên production: tác vụ nền sau thanh toán và vòng nền cùng xếp lịch 1 đơn → 2 job, Pi phát 2 lần."""
    from app import db as dbmod, orders as svc
    from helpers import create_booking
    monkeypatch.setattr(svc, "schedule_in_background", lambda *a, **k: None)  # giữ đơn ở 'paid'
    ref = create_booking(user_client, db, khi_nao="ngay", thoi_gian="")
    from helpers import confirm_and_pay
    confirm_and_pay(user_client, ref)
    oid = db.scalar(select(Order).where(Order.booking_ref == ref)).id
    s1, s2 = dbmod.SessionLocal(), dbmod.SessionLocal()
    o1, o2 = s1.get(Order, oid), s2.get(Order, oid)
    assert o1.status == o2.status == "paid"  # cả hai worker cùng thấy 'paid'
    assert svc.try_schedule(s1, o1) is True
    s1.commit()
    assert svc.try_schedule(s2, o2) is False  # worker thứ hai thua, không tạo job
    s2.commit()
    s1.close(), s2.close()
    db.expire_all()
    o = db.get(Order, oid)
    assert o.status == "scheduled" and len(o.jobs) == 1
    assert [e.status for e in o.events].count("scheduled") == 1


def test_video_upload_shown_as_temple_video(setup, db, client, user_client):
    """Pi gửi video mâm lễ + tiếng thu tại đền → trang đơn phát video đó thay cho clip ghép ảnh."""
    order, agent, clock = setup
    move_play_time(db, order)
    run(db, agent, clock)
    up = f"{P}/api/device/evidence"
    good = {"Authorization": "Bearer dev-device-token-change-me", "X-Device-Id": "pi-demo-01"}
    job_id = order.jobs[-1].id
    mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 4000
    r = client.post(up, headers=good, data={"job_id": job_id, "phase": "video"},
                    files={"file": ("v.mp4", b"\xff\xd8\xff" + b"0" * 100, "video/mp4")})
    assert r.status_code == 415  # không phải MP4
    r = client.post(up, headers=good, data={"job_id": job_id, "phase": "video"}, files={"file": ("v.mp4", mp4, "video/mp4")})
    assert r.status_code == 200 and r.json() == {"ok": True}
    r = client.post(up, headers=good, data={"job_id": job_id, "phase": "video"}, files={"file": ("v.mp4", mp4, "video/mp4")})
    assert r.json()["duplicate"] is True
    o = db.get(Order, order.id)
    db.refresh(o)
    assert o.video and o.video.kind == "video" and o.photos == [e for e in o.evidence if e.kind == "photo"]
    assert "Video tại đền" in user_client.get(f"{P}/don/{o.id}").text
    r = user_client.get(f"{P}/don/{o.id}/clip")
    assert r.status_code == 200 and r.content == mp4
