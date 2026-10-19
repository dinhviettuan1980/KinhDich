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
