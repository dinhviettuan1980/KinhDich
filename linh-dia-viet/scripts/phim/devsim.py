"""2 thiết bị GIẢ (Pi tại Đền Ngọc Sơn + điện thoại tại Chùa Trấn Quốc) nói chuyện với server qua kênh HTTP
/api/device/poll|ack|evidence — cùng giao thức thiết bị thật. Ảnh mâm dựng bằng camera simulate của pi-agent.
Đền Ngọc Sơn: kiosk "quên" bày Gà luộc (để quay cảnh cảnh báo mâm lễ chưa khớp)."""
import json, subprocess, sys, threading, time, traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]  # thư mục linh-dia-viet
sys.path.insert(0, str(ROOT / "pi-agent"))
from ld_agent.camera import Camera  # noqa: E402
from PIL import Image  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent))
import anim  # noqa: E402
import tray as tray_art  # noqa: E402

BASE = "http://127.0.0.1:8100/le-chua"
WORK = Path(__file__).parent / "dev-work"
DEVICES = json.loads((Path(__file__).parent / "devices.json").read_text())  # [{id, token, kind, video, drop}]
cam = Camera("simulate")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def wait_until(t):
    while time.time() < t:
        time.sleep(min(0.05, max(0, t - time.time())))


def run_device(d):
    h = {"Authorization": "Bearer " + d["token"], "X-Device-Id": d["id"]}
    c = httpx.Client(base_url=BASE, headers=h, timeout=30)
    done = set()

    def ack(job, state):
        c.post("/api/device/ack", json={"job_id": job["job_id"], "state": state, "ts": now_iso()})

    def shoot(job, phase, tray):
        p = WORK / d["id"] / f"{job['job_id'][:8]}-{phase}.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        tray_art.photo(tray["items"], d["temple"], phase, time.time()).save(
            p, "JPEG", quality=85, comment=("LD-MISSING:" + "|".join(d.get("drop", [])) + ";;").encode())
        c.post("/api/device/evidence", data={"job_id": job["job_id"], "phase": phase, "captured_at": now_iso()},
               files={"file": (p.name, p.read_bytes(), "image/jpeg")})
        return p

    def run_job(job):
        tray = dict(job.get("tray") or {})
        tray["items"] = [i for i in tray.get("items", []) if i["name"] not in d.get("drop", [])]
        play_at = datetime.fromisoformat(job["play_at"].replace("Z", "+00:00")).timestamp()
        ack(job, "received")
        mp3 = WORK / d["id"] / f"{job['job_id'][:8]}.mp3"
        mp3.parent.mkdir(parents=True, exist_ok=True)
        mp3.write_bytes(httpx.get(job["audio_url"], timeout=60).content)
        ack(job, "downloaded")
        cap = job.get("capture") or {}
        if time.time() < play_at - cap.get("before_s", 0):
            wait_until(play_at - cap.get("before_s", 0))
            shoot(job, "before", tray)
        wait_until(play_at)
        ack(job, "playing")
        print(d["id"], "PLAYING", datetime.now().strftime("%H:%M:%S.%f")[:-3], flush=True)
        time.sleep(2)
        still = shoot(job, "start", tray)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", str(mp3)]).decode())
        wait_until(play_at + dur)
        ack(job, "done")
        time.sleep(cap.get("after_s", 4))
        shoot(job, "after", tray)
        if d.get("video"):  # clip tại đền: thủ nhang hoạt hình đọc sớ cạnh mâm lễ, đồng hồ giờ thật
            v = tray_art.clip(tray["items"], mp3, d["temple"], play_at, WORK / d["id"] / f"{job['job_id'][:8]}.mp4")
            c.post("/api/device/evidence", data={"job_id": job["job_id"], "phase": "video", "captured_at": now_iso()},
                   files={"file": (v.name, v.read_bytes(), "video/mp4")})
        print(d["id"], "DONE", job["job_id"][:8], flush=True)

    while True:
        try:
            r = c.post("/api/device/poll", json={"kind": d["kind"], "version": "sim-1", "net": "wifi", "volume": 70,
                                                 "camera": "simulate", "clock_synced": True, "battery": d.get("battery")})
            for job in r.json().get("jobs", []):
                if job["job_id"] not in done:
                    done.add(job["job_id"])
                    threading.Thread(target=lambda j=job: _safe(run_job, j), daemon=True).start()
        except Exception as e:
            print(d["id"], "poll lỗi", e, flush=True)
        time.sleep(2)


def _safe(f, *a):
    try:
        f(*a)
    except Exception:
        traceback.print_exc()


for d in DEVICES:
    threading.Thread(target=run_device, args=(d,), daemon=True).start()
while True:
    time.sleep(60)
