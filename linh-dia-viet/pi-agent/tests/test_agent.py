import hashlib
import io
import json
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest
from PIL import Image

from ld_agent.agent import Agent, iso
from ld_agent.camera import Camera
from ld_agent.config import Config
from ld_agent.player import SimPlayer
from ld_agent.transport import Transport

AUDIO = b"ID3fake-mp3-bytes" * 100
SHA = hashlib.sha256(AUDIO).hexdigest()
VN = ZoneInfo("Asia/Ho_Chi_Minh")


class FakeTransport(Transport):
    def __init__(self):
        self.acks, self.statuses, self.online, self.on_cmd = [], [], True, None

    def start(self, on_cmd):
        self.on_cmd = on_cmd

    def connected(self):
        return self.online

    def publish_ack(self, payload, on_done):
        if not self.online:
            return False
        self.acks.append(payload)
        on_done()
        return True

    def publish_status(self, payload):
        self.statuses.append(payload)


class FakeServer:
    def __init__(self):
        self.uploads, self.fail_uploads, self.audio = [], 0, AUDIO

    def handler(self, req: httpx.Request):
        if req.url.path.endswith("/audio.mp3"):
            return httpx.Response(200, content=self.audio)
        if req.url.path.endswith("/api/device/evidence"):
            if self.fail_uploads:
                self.fail_uploads -= 1
                return httpx.Response(503)
            assert req.headers["authorization"] == "Bearer tok" and req.headers["x-device-id"] == "pi-x"
            self.uploads.append(req.content)
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)


def local_ts(h, m, day=20):
    return datetime(2026, 10, day, h, m, tzinfo=VN).timestamp()


@pytest.fixture
def env(tmp_path):
    cfg = Config(server_url="http://srv/le-chua", device_id="pi-x", device_token="tok", data_dir=tmp_path,
                 simulate=True, simulate_play_seconds=10, volume_max=80, quiet_start=dtime(22, 0), quiet_end=dtime(5, 0))
    srv = FakeServer()
    tr = FakeTransport()
    player = SimPlayer(10)
    agent = Agent(cfg, tr, httpx.Client(transport=httpx.MockTransport(srv.handler)), player, Camera("simulate"),
                  clock=lambda: local_ts(9, 0))
    agent.start()
    return agent, tr, srv, player


def play_cmd(job="j1", at=None, **kw):
    c = {"type": "play", "job_id": job, "audio_url": "http://srv/le-chua/files/audio.mp3", "sha256": SHA,
         "play_at": iso(at or local_ts(10, 0)), "volume": 70, "capture": {"before_s": 60, "at_start": True, "after_s": 30}}
    c.update(kw)
    return c


def states(tr, job="j1"):
    return [a["state"] for a in tr.acks if a["job_id"] == job]


def test_full_cycle(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    t = local_ts(9, 50)
    agent.tick(t)
    assert states(tr) == ["received", "downloaded"]
    assert (agent.audio_dir / "j1.mp3").read_bytes() == AUDIO
    agent.tick(local_ts(9, 59) + 1)  # 59 giây trước giờ: chụp ảnh "before"
    assert len(srv.uploads) == 1 and b'name="phase"\r\n\r\nbefore' in srv.uploads[0]
    agent.tick(local_ts(10, 0))
    assert states(tr)[-1] == "playing" and len(srv.uploads) == 2
    agent.tick(local_ts(10, 0) + 5)
    assert states(tr)[-1] == "playing"
    agent.tick(local_ts(10, 0) + 11)
    assert states(tr)[-1] == "done"
    agent.tick(local_ts(10, 0) + 42)
    assert len(srv.uploads) == 3 and b"after" in srv.uploads[2]
    jpeg = srv.uploads[2].split(b"\r\n\r\n", 4)[-1]
    assert jpeg.startswith(b"\xff\xd8\xff")


def test_duplicate_command_not_replayed(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    tr.on_cmd(play_cmd())  # server gửi lại
    assert len(agent.store.all_jobs()) == 1
    assert states(tr) == ["received", "downloaded", "downloaded"]


def test_quiet_hours_rejects(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd(at=local_ts(23, 30)))
    assert states(tr) == ["received", "error"]
    assert "giờ cấm" in tr.acks[-1]["detail"]


def test_quiet_hours_wrap():
    c = Config(quiet_start=dtime(22, 0), quiet_end=dtime(5, 0))
    assert c.in_quiet_hours(dtime(23, 0)) and c.in_quiet_hours(dtime(4, 59))
    assert not c.in_quiet_hours(dtime(5, 0)) and not c.in_quiet_hours(dtime(21, 59))


def test_volume_capped(env, monkeypatch):
    agent, tr, srv, player = env
    seen = {}
    monkeypatch.setattr(player, "start", lambda path, vol, now: seen.setdefault("vol", vol) or
                        SimPlayer.start(player, path, vol, now))
    tr.on_cmd(play_cmd(volume=100))
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(10, 0))
    assert seen["vol"] == 80


def test_offline_acks_are_sent_later(env):
    agent, tr, srv, player = env
    tr.online = False
    tr.on_cmd(play_cmd())
    for t in (local_ts(9, 50), local_ts(10, 0), local_ts(10, 0) + 11):
        agent.tick(t)
    assert tr.acks == []  # mất mạng nhưng vẫn phát bài đã tải
    tr.online = True
    agent.tick(local_ts(10, 0) + 12)
    assert states(tr) == ["received", "downloaded", "playing", "done"]


def test_bad_checksum_retries(env):
    agent, tr, srv, player = env
    srv.audio = b"corrupted"
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    j = agent.store.get_job("j1")
    assert j["state"] == "received" and "sha256" in j["error"] and j["attempts"] == 1
    srv.audio = AUDIO
    agent.tick(local_ts(9, 50))  # chưa tới lượt thử lại
    assert agent.store.get_job("j1")["state"] == "received"
    agent.tick(local_ts(9, 51))
    assert agent.store.get_job("j1")["state"] == "downloaded"


def test_too_late_is_error(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(10, 11))  # mất điện 11 phút > MAX_LATE (10 phút)
    assert states(tr)[-1] == "error"


def test_stop_command(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(10, 0))
    tr.on_cmd({"type": "stop"})
    assert states(tr)[-1] == "error" and tr.acks[-1]["detail"] == "Dừng theo lệnh"
    agent.tick(local_ts(10, 0) + 20)
    assert states(tr).count("done") == 0


def test_cancel_command(env):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    tr.on_cmd({"type": "cancel", "job_id": "j1"})
    agent.tick(local_ts(10, 0))
    assert "playing" not in states(tr)


def test_restart_while_playing_marks_error(env, tmp_path):
    agent, tr, srv, player = env
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(10, 0))
    agent2 = Agent(agent.cfg, tr, agent.http, SimPlayer(10), Camera("simulate"), clock=lambda: local_ts(10, 1))
    agent2.start()
    assert states(tr)[-1] == "error"


def test_upload_retry(env):
    agent, tr, srv, player = env
    srv.fail_uploads = 1
    agent.on_cmd({"type": "capture"})
    agent.tick(local_ts(9, 0))
    assert srv.uploads == [] and len(agent.store.due_uploads(local_ts(9, 0) + 3600)) == 1
    agent.tick(local_ts(9, 0) + 30)
    assert len(srv.uploads) == 1 and b"test" in srv.uploads[0]


def test_status_payload(env):
    agent, tr, srv, player = env
    agent.tick(local_ts(9, 0))
    st = tr.statuses[-1]
    assert st["online"] and st["net"] == "wifi" and st["version"] and "disk_free" in st


def test_simulated_photo_is_valid_jpeg(tmp_path):
    p = tmp_path / "x.jpg"
    assert Camera("simulate").capture(p, "before")
    with Image.open(io.BytesIO(p.read_bytes())) as im:
        assert im.format == "JPEG"


def test_config_from_env_file(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("LD_DEVICE_ID=pi-9\nLD_VOLUME_MAX=150\nLD_QUIET_START=21:30\nLD_SIMULATE=true\n")
    monkeypatch.setenv("LD_DEVICE_TOKEN", "abc")
    c = Config.load(f)
    assert c.device_id == "pi-9" and c.device_token == "abc" and c.volume_max == 100
    assert c.quiet_start == dtime(21, 30) and c.simulate


def test_status_sent_as_soon_as_connected(env):
    agent, tr, srv, player = env
    tr.online = False
    agent.tick(local_ts(9, 0))
    tr.online = True
    agent.tick(local_ts(9, 0) + 1)
    assert len(tr.statuses) == 1


def test_fake_tray_photo_from_order_items(tmp_path):
    from PIL import Image
    from ld_agent import fake_tray
    assert fake_tray.icon_for("Hương (nhang)") is None and fake_tray.icon_for("Gà luộc") == "🐓"
    assert fake_tray.icon_for("Món lạ") is False
    tray = {"items": [{"name": "Hương (nhang)", "unit": "bó", "qty": 3}, {"name": "Gà luộc", "unit": "con", "qty": 1},
                      {"name": "Món lạ", "unit": "phần", "qty": 2}], "temple": "Đền Ngọc Sơn"}
    p = tmp_path / "t.jpg"
    assert Camera("simulate").capture(p, "start", tray=tray)
    with Image.open(p) as im:
        assert im.format == "JPEG" and im.size == (1280, 960)
    assert Camera("simulate").capture(tmp_path / "e.jpg", "before")  # không có lễ vật → mâm trống


def test_waits_for_clock_sync_after_power_loss(tmp_path, monkeypatch):
    """Pi không có pin RTC: vừa có điện lại, chưa đồng bộ giờ thì chưa chụp/phát và cũng không coi là trễ."""
    cfg = Config(server_url="http://srv/le-chua", device_id="pi-x", device_token="tok", data_dir=tmp_path,
                 simulate=False, volume_max=80, quiet_start=dtime(22, 0), quiet_end=dtime(5, 0), clock_wait_seconds=600)
    srv, tr, synced = FakeServer(), FakeTransport(), {"v": False}
    agent = Agent(cfg, tr, httpx.Client(transport=httpx.MockTransport(srv.handler)), SimPlayer(10), Camera("simulate"),
                  clock=lambda: local_ts(9, 0), clock_synced=lambda: synced["v"])
    agent.start()
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    assert states(tr) == ["received", "downloaded"]  # tải trước vẫn được
    agent.tick(local_ts(10, 0))
    assert states(tr)[-1] == "downloaded" and srv.uploads == []  # chưa đồng bộ giờ → chưa chụp, chưa phát
    assert agent.status()["clock_synced"] is False
    synced["v"] = True
    agent.tick(local_ts(10, 0) + 3)
    assert states(tr)[-1] == "playing" and agent.status()["clock_synced"] is True
    # mất mạng hẳn: quá thời gian chờ thì phát theo giờ máy
    synced["v"] = False
    agent2 = Agent(cfg, FakeTransport(), agent.http, SimPlayer(10), Camera("simulate"), clock=lambda: local_ts(9, 0),
                   clock_synced=lambda: False)
    assert not agent2._clock_ready()
    monkeypatch.setattr("ld_agent.agent.time.monotonic", lambda: agent2._started_mono + 601)
    assert agent2._clock_ready()


def test_clock_synced_reads_timedatectl(monkeypatch):
    from ld_agent import sysinfo
    import subprocess
    monkeypatch.setattr(sysinfo, "_synced", False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="no\n"))
    assert sysinfo.clock_synced() is False
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="yes\n"))
    assert sysinfo.clock_synced() is True
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="no\n"))
    assert sysinfo.clock_synced() is True  # đã đồng bộ một lần thì nhớ


# ---------------- video tại đền (quay lúc đọc sớ) ----------------

class FakeRecorder:
    enabled = True

    def __init__(self, uses_camera: bool):
        self.uses_camera, self.running, self.started, self.stopped = uses_camera, False, [], 0

    def busy(self):
        return self.running

    def start(self, dst, audio=None, still=None):
        self.started.append((dst, audio, still))
        self.dst, self.running = dst, True
        return True

    def stop(self):
        self.stopped += 1

    def finish(self, timeout=20):
        self.running = False
        self.dst.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"\x00" * 2000)
        return self.dst


def rec_env(tmp_path, uses_camera):
    cfg = Config(server_url="http://srv/le-chua", device_id="pi-x", device_token="tok", data_dir=tmp_path,
                 simulate=True, simulate_play_seconds=10, record_tail_seconds=3)
    srv, tr, rec = FakeServer(), FakeTransport(), FakeRecorder(uses_camera)
    agent = Agent(cfg, tr, httpx.Client(transport=httpx.MockTransport(srv.handler)), SimPlayer(10), Camera("simulate"),
                  clock=lambda: local_ts(9, 0), recorder=rec)
    agent.start()
    return agent, tr, srv, rec


def phases(srv):
    return [up.split(b'name="phase"\r\n\r\n')[1].split(b"\r\n")[0].decode() for up in srv.uploads]


def test_simulated_video_recorded_during_prayer(tmp_path):
    agent, tr, srv, rec = rec_env(tmp_path, uses_camera=False)
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(9, 59) + 1)
    agent.tick(local_ts(10, 0))
    dst, audio, still = rec.started[0]
    assert audio.name == "j1.mp3" and still is not None  # giả lập: ảnh mâm giả + bài khấn
    assert phases(srv) == ["before", "start"]  # không chiếm webcam → vẫn chụp ảnh "start" như cũ
    agent.tick(local_ts(10, 0) + 11)  # đọc xong, quay thêm 3s
    assert states(tr)[-1] == "done" and phases(srv) == ["before", "start"]
    agent.tick(local_ts(10, 0) + 15)
    assert phases(srv) == ["before", "start", "video"]
    assert b"video/mp4" in srv.uploads[-1] and not dst.exists() and not still.exists()
    agent.tick(local_ts(10, 0) + 42)
    assert phases(srv)[-1] == "after"


def test_webcam_video_gives_start_frame(tmp_path, monkeypatch):
    import ld_agent.agent as agent_mod

    def fake_grab(video, dst, at_s=2.0):
        dst.write_bytes(b"\xff\xd8\xff" + b"0" * 100)
        return True
    monkeypatch.setattr(agent_mod, "grab_frame", fake_grab)
    agent, tr, srv, rec = rec_env(tmp_path, uses_camera=True)
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(9, 59) + 1)
    agent.tick(local_ts(10, 0))
    assert rec.started[0][2] is None and phases(srv) == ["before"]  # webcam bận quay: không chụp riêng
    agent.tick(local_ts(10, 0) + 11)
    assert rec.stopped == 0  # còn quay thêm 3s sau khi đọc xong
    agent.tick(local_ts(10, 0) + 15)
    assert rec.stopped == 1 and phases(srv) == ["before", "start", "video"]


def test_stop_command_ends_recording(tmp_path):
    agent, tr, srv, rec = rec_env(tmp_path, uses_camera=True)
    tr.on_cmd(play_cmd())
    agent.tick(local_ts(9, 50))
    agent.tick(local_ts(10, 0))
    tr.on_cmd({"type": "stop"})
    agent.tick(local_ts(10, 0) + 1)
    assert rec.stopped == 1 and "video" in phases(srv)


def test_record_disabled(tmp_path):
    cfg = Config(server_url="http://srv/le-chua", device_id="pi-x", device_token="tok", data_dir=tmp_path,
                 simulate=True, record=False)
    agent = Agent(cfg, FakeTransport(), httpx.Client(), SimPlayer(1), Camera("simulate"), recorder=FakeRecorder(False))
    assert agent.recorder is None
