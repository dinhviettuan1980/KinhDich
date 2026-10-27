"""Lõi agent: nhận lệnh, tải trước bài khấn, phát đúng giờ, chụp ảnh, báo ACK (kể cả bù khi mất mạng).

Toàn bộ logic chạy trong tick(now) để test được với đồng hồ giả. Luật cứng phía thiết bị (server không vượt được):
- Trần âm lượng VOLUME_MAX.
- Giờ cấm phát QUIET_START–QUIET_END (mặc định 22:00–05:00, theo giờ địa phương).
- Chống phát trùng theo job_id (job đã có trong SQLite thì bỏ qua lệnh lặp).
"""
import hashlib
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from . import __version__, sysinfo
from .camera import Camera
from .config import Config
from .player import Player
from .store import Store
from .transport import Transport

log = logging.getLogger("ld_agent")


def parse_iso(s: str) -> float:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


class Agent:
    def __init__(self, cfg: Config, transport: Transport, http: httpx.Client, player: Player, camera: Camera,
                 clock=time.time, clock_synced=sysinfo.clock_synced):
        self.cfg, self.transport, self.http, self.player, self.camera, self.clock = \
            cfg, transport, http, player, camera, clock
        self.clock_synced = clock_synced
        self._started_mono = time.monotonic()  # không phụ thuộc giờ hệ thống (có thể đang sai)
        self._clock_warned = False
        self.store = Store(cfg.data_dir / "agent.db")
        self.audio_dir = cfg.data_dir / "audio"
        self.photo_dir = cfg.data_dir / "photos"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.volume = cfg.volume_default
        self.actions: deque = deque()  # lệnh tức thời: test_tone, capture
        self.playing_job: str | None = None
        self._inflight: set[int] = set()
        self._last_status = 0.0
        self.headers = {"Authorization": f"Bearer {cfg.device_token}", "X-Device-Id": cfg.device_id}

    # ---------------- nhận lệnh ----------------

    def start(self) -> None:
        self.transport.start(self.on_cmd)
        # mất điện giữa lúc phát → coi như lỗi, không phát lại (tránh phát trùng)
        for j in self.store.jobs_in("playing"):
            self._fail(j["job_id"], "Thiết bị khởi động lại khi đang phát", self.clock())

    def on_cmd(self, cmd: dict) -> None:
        now = self.clock()
        t = cmd.get("type")
        log.info("Nhận lệnh %s %s", t, cmd.get("job_id", ""))
        if t == "play":
            self._on_play(cmd, now)
        elif t == "stop":
            self.player.stop()
            if self.playing_job:
                self._fail(self.playing_job, "Dừng theo lệnh", now)
                self.playing_job = None
        elif t == "cancel":
            j = self.store.get_job(str(cmd.get("job_id")))
            if j and j["state"] in ("received", "downloaded"):
                self.store.update_job(j["job_id"], now, state="cancelled")
        elif t in ("test_tone", "capture"):
            self.actions.append(cmd)
        elif t == "config":
            if "volume" in cmd:
                self.volume = max(0, min(self.cfg.volume_max, int(cmd["volume"])))
        else:
            log.warning("Lệnh không hỗ trợ: %s", t)

    def _on_play(self, cmd: dict, now: float) -> None:
        job_id = str(cmd.get("job_id", ""))
        existing = self.store.get_job(job_id)
        if existing:  # lệnh lặp (server gửi lại) → chỉ báo lại trạng thái, không phát lại
            state = existing["state"]
            ack = {"received": "received", "downloaded": "downloaded", "playing": "playing", "done": "done",
                   "error": "error"}.get(state)
            if ack:
                self._ack(job_id, ack, now, existing.get("error"))
            return
        try:
            play_at = parse_iso(cmd["play_at"])
            assert cmd["audio_url"] and cmd["sha256"]
        except (KeyError, ValueError, AssertionError):
            log.error("Lệnh play thiếu trường")
            return
        self.store.add_job(cmd, play_at, now)
        self._ack(job_id, "received", now)
        if self._quiet(play_at):
            self._fail(job_id, "Giờ hẹn rơi vào giờ cấm phát của thiết bị", now)

    # ---------------- vòng chính ----------------

    def tick(self, now: float | None = None) -> None:
        now = self.clock() if now is None else now
        self._flush_acks()
        while self.actions:
            self._run_action(self.actions.popleft(), now)
        self._downloads(now)
        self._captures_before(now)
        self._playback(now)
        self._captures_after(now)
        self._uploads(now)
        if now - self._last_status >= self.cfg.status_interval:
            self.publish_status(now)

    def _downloads(self, now: float) -> None:
        for j in self.store.jobs_in("received"):
            if j["next_try"] > now:
                continue
            if now > j["play_at"] + self.cfg.max_late_seconds:
                self._fail(j["job_id"], "Không tải được bài khấn trước giờ phát", now)
                continue
            cmd = json.loads(j["payload"])
            dst = self.audio_dir / f"{j['job_id']}.mp3"
            try:
                self._download(cmd["audio_url"], dst, cmd["sha256"])
            except Exception as e:
                n = j["attempts"] + 1
                log.warning("Tải audio lỗi (lần %d): %s", n, e)
                self.store.update_job(j["job_id"], now, attempts=n, next_try=now + min(300, 5 * 2 ** min(n, 6)),
                                      error=str(e)[:300])
                continue
            self.store.update_job(j["job_id"], now, state="downloaded", audio_path=str(dst), error=None)
            self._ack(j["job_id"], "downloaded", now)

    def _download(self, url: str, dst: Path, sha256: str) -> None:
        h = hashlib.sha256()
        tmp = dst.with_suffix(".part")
        with self.http.stream("GET", url, timeout=60) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes():
                    h.update(chunk)
                    f.write(chunk)
        if h.hexdigest() != sha256:
            tmp.unlink(missing_ok=True)
            raise ValueError("sai sha256")
        tmp.replace(dst)

    def _clock_ready(self) -> bool:
        """Chỉ chụp/phát khi giờ đã đồng bộ; quá clock_wait_seconds mà chưa được (mất mạng) thì đành theo giờ máy."""
        if self.cfg.simulate or self.clock_synced():
            return True
        if time.monotonic() - self._started_mono >= self.cfg.clock_wait_seconds:
            if not self._clock_warned:
                log.warning("Chưa đồng bộ được giờ sau %ss — phát theo giờ máy", self.cfg.clock_wait_seconds)
                self._clock_warned = True
            return True
        return False

    def _captures_before(self, now: float) -> None:
        if not self._clock_ready():
            return
        for j in self.store.jobs_in("downloaded"):
            cap = json.loads(j["payload"]).get("capture") or {}
            before = cap.get("before_s")
            if before is not None and not j["before_done"] and now >= j["play_at"] - before:
                self.store.update_job(j["job_id"], now, before_done=1)
                self._capture(j["job_id"], "before", now)

    def _playback(self, now: float) -> None:
        if self.playing_job:
            if self.player.is_playing(now):
                return
            job_id, self.playing_job = self.playing_job, None
            err = self.player.result()
            if err:
                self._fail(job_id, err, now)
                return
            cap = json.loads(self.store.get_job(job_id)["payload"]).get("capture") or {}
            after = cap.get("after_s")
            self.store.update_job(job_id, now, state="done",
                                  after_due=now + after if after is not None else None, after_done=0 if after is not None else 1)
            self._ack(job_id, "done", now)
        if not self._clock_ready():
            return  # vừa có điện lại, đồng hồ chưa đúng: chưa phát, cũng chưa coi là trễ
        for j in self.store.jobs_in("downloaded"):
            if now < j["play_at"]:
                break
            if self.playing_job:
                return  # phát lần lượt
            if now > j["play_at"] + self.cfg.max_late_seconds:
                self._fail(j["job_id"], "Quá giờ hẹn (thiết bị offline hoặc mất điện)", now)
                continue
            if self._quiet(now):
                self._fail(j["job_id"], "Đang trong giờ cấm phát", now)
                continue
            cmd = json.loads(j["payload"])
            vol = max(0, min(self.cfg.volume_max, int(cmd.get("volume", self.volume))))
            try:
                self.player.start(Path(j["audio_path"]), vol, now)
            except Exception as e:
                self._fail(j["job_id"], f"Không phát được: {e}", now)
                continue
            self.playing_job = j["job_id"]
            self.store.update_job(j["job_id"], now, state="playing")
            self._ack(j["job_id"], "playing", now, f"volume={vol}")
            if (cmd.get("capture") or {}).get("at_start"):
                self._capture(j["job_id"], "start", now)

    def _captures_after(self, now: float) -> None:
        for j in self.store.jobs_in("done"):
            if not j["after_done"] and j["after_due"] is not None and now >= j["after_due"]:
                self.store.update_job(j["job_id"], now, after_done=1)
                self._capture(j["job_id"], "after", now)

    def _run_action(self, cmd: dict, now: float) -> None:
        if cmd["type"] == "capture":
            self._capture(None, "test", now)
        elif cmd["type"] == "test_tone":
            if self.playing_job or self._quiet(now):
                log.warning("Bỏ qua phát âm thử (đang phát hoặc giờ cấm)")
                return
            tone = self.audio_dir / "test-tone.wav"
            if not tone.exists():
                import subprocess
                try:
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=660:duration=2",
                                    str(tone)], check=True, timeout=30)
                except Exception as e:
                    log.error("Không tạo được âm thử: %s", e)
                    return
            try:
                self.player.start(tone, min(self.volume, self.cfg.volume_max), now)
            except Exception as e:
                log.error("Phát âm thử lỗi: %s", e)

    # ---------------- ảnh ----------------

    def _capture(self, job_id: str | None, phase: str, now: float) -> None:
        path = self.photo_dir / f"{job_id or 'test'}-{phase}-{int(now)}.jpg"
        tray = None
        if job_id and (j := self.store.get_job(job_id)):
            tray = json.loads(j["payload"]).get("tray")
        if self.camera.capture(path, label=phase, tray=tray):
            self.store.push_upload(job_id or "", phase, path, iso(now))
        else:
            log.error("Không chụp được ảnh %s", phase)

    def _uploads(self, now: float) -> None:
        for up in self.store.due_uploads(now):
            path = Path(up["path"])
            if not path.exists():
                self.store.drop_upload(up["id"])
                continue
            try:
                with open(path, "rb") as f:
                    r = self.http.post(f"{self.cfg.server_url}/api/device/evidence", headers=self.headers, timeout=60,
                                       data={"job_id": up["job_id"], "phase": up["phase"],
                                             "captured_at": up["captured_at"]},
                                       files={"file": (path.name, f, "image/jpeg")})
                if r.status_code in (400, 401, 404, 413, 415):  # lỗi vĩnh viễn: bỏ, không thử lại vô hạn
                    log.error("Server từ chối ảnh (%s): %s", r.status_code, r.text[:200])
                    self.store.drop_upload(up["id"])
                    continue
                r.raise_for_status()
                self.store.drop_upload(up["id"])
                path.unlink(missing_ok=True)
            except Exception as e:
                n = up["attempts"] + 1
                log.warning("Upload ảnh lỗi (lần %d): %s", n, e)
                self.store.retry_upload(up["id"], n, now + min(600, 5 * 2 ** min(n, 7)))

    # ---------------- ACK / status ----------------

    def _ack(self, job_id: str, state: str, now: float, detail: str | None = None) -> None:
        self.store.push_ack({"job_id": job_id, "state": state, "ts": iso(now), "detail": detail})
        self._flush_acks()

    def _fail(self, job_id: str, reason: str, now: float) -> None:
        log.error("Job %s lỗi: %s", job_id, reason)
        self.store.update_job(job_id, now, state="error", error=reason)
        self._ack(job_id, "error", now, reason)

    def _flush_acks(self) -> None:
        if not self.transport.connected():
            self._inflight.clear()  # ACK chưa được broker xác nhận sẽ gửi lại khi có mạng
            return
        for ack_id, payload in self.store.pending_acks():
            if ack_id in self._inflight:
                continue

            def done(ack_id=ack_id):
                self.store.drop_ack(ack_id)
                self._inflight.discard(ack_id)
            self._inflight.add(ack_id)
            if not self.transport.publish_ack(payload, done):
                self._inflight.discard(ack_id)
                return

    def _quiet(self, ts: float) -> bool:
        local = datetime.fromtimestamp(ts, ZoneInfo(self.cfg.timezone)).time()
        return self.cfg.in_quiet_hours(local)

    def status(self) -> dict:
        net, rssi = sysinfo.net_info()
        if self.cfg.simulate:
            net, rssi = "wifi", -55
        return {"online": True, "net": net, "rssi": rssi, "temp": sysinfo.cpu_temp(), "volume": self.volume,
                "version": __version__, "uptime": sysinfo.uptime(), "disk_free": sysinfo.disk_free_mb(self.cfg.data_dir),
                "queue": len(self.store.jobs_in("received", "downloaded")), "camera": self.camera.kind,
                "clock_synced": bool(self.cfg.simulate or self.clock_synced())}

    def publish_status(self, now: float) -> None:
        if self.transport.connected():  # chưa kết nối thì thử lại ở tick sau, không đợi hết chu kỳ
            self._last_status = now
            self.transport.publish_status(self.status())
