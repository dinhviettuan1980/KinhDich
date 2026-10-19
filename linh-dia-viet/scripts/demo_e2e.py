#!/usr/bin/env python3
"""Demo đầu-cuối: tạo đơn → thanh toán giả lập → Pi giả lập nhận lệnh, "phát", gửi ảnh → đơn 'completed'.

Cần server đang chạy (docker compose up) và .env chứa DEMO_DEVICE_TOKEN. Chạy từ thư mục linh-dia-viet/:
    .venv/bin/python scripts/demo_e2e.py
Mất khoảng 3–4 phút (giờ hẹn ≥ MIN_LEAD_SECONDS, ảnh "after" chụp sau CAPTURE_AFTER_S giây).
"""
import argparse
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

ROOT = Path(__file__).resolve().parents[1]
VN = ZoneInfo("Asia/Ho_Chi_Minh")


def env_file(path: Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"')
    return out


def step(msg):
    print(f"\n▶ {msg}", flush=True)


def csrf(c: httpx.Client, path: str) -> str:
    return re.search(r'name="csrf-token" content="([^"]+)"', c.get(path).text).group(1)


def main() -> int:
    env = env_file(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("DEMO_BASE", "http://localhost:8000/le-chua"))
    ap.add_argument("--mqtt-host", default="localhost")
    ap.add_argument("--device-id", default=env.get("DEMO_DEVICE_ID", "pi-demo-01"))
    ap.add_argument("--device-token", default=env.get("DEMO_DEVICE_TOKEN", ""))
    ap.add_argument("--temple", default="den-ngoc-son", help="slug đền đã gắn thiết bị demo")
    ap.add_argument("--lead-seconds", type=int, default=int(env.get("MIN_LEAD_SECONDS", 120)) + 30)
    ap.add_argument("--timeout", type=int, default=420)
    args = ap.parse_args()
    if not args.device_token:
        print("Thiếu DEMO_DEVICE_TOKEN (trong .env hoặc --device-token)")
        return 2
    base = args.base.rstrip("/")
    c = httpx.Client(base_url=base, follow_redirects=False, timeout=60)  # httpx nối path vào sau base_url
    prefix = ""

    step("Kiểm tra server")
    r = c.get(f"{prefix}/healthz")
    r.raise_for_status()
    print("  OK", r.json())

    step("Khởi động Pi giả lập (pi-agent --simulate)")
    data_dir = tempfile.mkdtemp(prefix="ld-demo-pi-")
    agent_env = {**os.environ, "LD_SERVER_URL": base, "LD_DEVICE_ID": args.device_id,
                 "LD_DEVICE_TOKEN": args.device_token, "LD_MQTT_HOST": args.mqtt_host, "LD_DATA_DIR": data_dir,
                 "LD_SIMULATE_PLAY_SECONDS": "5", "LD_QUIET_START": "00:00", "LD_QUIET_END": "00:00"}
    agent = subprocess.Popen([sys.executable, "-m", "ld_agent", "--simulate", "--env", "/dev/null"],
                             cwd=ROOT / "pi-agent", env=agent_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
    try:
        step("Đăng ký khách hàng demo")
        email = f"demo-{secrets.token_hex(3)}@example.com"
        tok = csrf(c, f"{prefix}/dang-ky")
        r = c.post(f"{prefix}/dang-ky", data={"name": "Khách Demo", "identifier": email, "password": "demo-password",
                                             "csrf_token": tok})
        assert r.status_code == 303, r.text[:300]
        tok = csrf(c, f"{prefix}/")
        print("  ", email)

        step("Đặt lễ (tự sinh sớ + TTS)")
        home = c.get(f"{prefix}/den/{args.temple}").text
        temple_id = re.search(r"dat-le\?den=(\d+)", home).group(1)
        form = c.get(f"{prefix}/dat-le?den={temple_id}").text
        pkg = re.search(r'name="goi" value="(\d+)"', form).group(1)
        at = datetime.now(VN) + timedelta(seconds=args.lead_seconds + 60)
        at = at.replace(second=0, microsecond=0)
        data = {"den": temple_id, "goi": pkg, "ho_ten": "Nguyễn Văn Demo", "nam_sinh": "1990",
                "dia_chi": "Cầu Giấy, Hà Nội", "nguyen_vong": "gia đình mạnh khỏe, bình an", "cach_khan": "tts",
                "thoi_gian": at.strftime("%Y-%m-%dT%H:%M")}
        r = c.post(f"{prefix}/dat-le", data=data, headers={"X-CSRF-Token": tok})
        assert r.status_code == 200, r.text
        ref = r.json()["redirect"].rsplit("/", 1)[1]
        print(f"  Mã đặt {ref}, giờ khấn {at:%H:%M %d/%m/%Y}")

        step("Xác nhận + thanh toán giả lập")
        r = c.post(f"{prefix}/dat-le/xem-lai/{ref}", data={"csrf_token": tok})
        txn = r.headers["location"].rsplit("/", 1)[1]
        r = c.post(f"{prefix}/thanh-toan/{txn}/gia-lap", data={"csrf_token": tok, "ket_qua": "thanh_cong"})
        order_id = int(r.headers["location"].rsplit("/", 1)[1])
        print(f"  Đơn #{order_id} — {base}/don/{order_id}")

        step("Theo dõi trạng thái đơn")
        seen, deadline = set(), time.time() + args.timeout
        while time.time() < deadline:
            j = c.get(f"{prefix}/don/{order_id}/json").json()
            for e in j["events"]:
                key = (e["status"], e["ts"])
                if key not in seen:
                    seen.add(key)
                    ts = datetime.fromisoformat(e["ts"]).astimezone(VN).strftime("%H:%M:%S")
                    print(f"  {ts}  {e['status']}" + (f" — {e['note']}" if e["note"] else ""), flush=True)
            if j["status"] in ("completed", "failed", "rejected", "cancelled"):
                break
            time.sleep(2)
        print(f"  Ảnh bằng chứng: {[e['phase'] for e in j['evidence']]}")
        ok = j["status"] == "completed" and j["evidence"]
        print("\n" + ("✅ DEMO THÀNH CÔNG — đơn đã 'completed' kèm ảnh." if ok else f"❌ DEMO LỖI — trạng thái {j['status']}"))
        return 0 if ok else 1
    finally:
        agent.terminate()
        try:
            out, _ = agent.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            agent.kill()
            out = ""
        print("\n--- log Pi giả lập (cuối) ---")
        print("\n".join(out.splitlines()[-15:]))


if __name__ == "__main__":
    sys.exit(main())
