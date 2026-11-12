"""Chuẩn bị dữ liệu cho bản quay giả lập (server sim ở :8100 phải đang chạy):
- thiết bị phone-demo-01 gắn Chùa Trấn Quốc (Pi pi-demo-01 đã gắn Ngọc Sơn khi seed)
- khách demo-an@example.com (hồ sơ tín chủ + thẻ giả lập)
- đơn hẹn giờ ngày mai tại Ngọc Sơn (để thủ nhang từ chối → admin hoàn tiền)
- đơn tự ghi âm tại Trấn Quốc (chờ admin kiểm duyệt)"""
import json, os, re, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
for line in (HERE / "sim.env").read_text().splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        os.environ[k] = v
SERVER = HERE.parents[1] / "server"
sys.path.insert(0, str(SERVER))
os.chdir(SERVER)  # đường dẫn trong sim.env tính từ server/
import httpx  # noqa: E402
from sqlalchemy import select  # noqa: E402
from app import db as dbmod  # noqa: E402
from app.models import Device, OfferingPackage, Temple  # noqa: E402
from app.security import hash_token  # noqa: E402

# mỗi đền 1 thiết bị giả: Ngọc Sơn = Pi 4 (seed), Trấn Quốc = điện thoại, còn lại Pi
devs = []
dbmod.init_engine()
with dbmod.SessionLocal() as db:
    for t in db.scalars(select(Temple).order_by(Temple.id)):
        if t.slug == "den-ngoc-son":
            did, kind, tok = "pi-demo-01", "pi", os.environ["DEMO_DEVICE_TOKEN"]
            db.get(Device, did).name = "Pi 4 Đền Ngọc Sơn"
        else:
            kind = "phone" if t.slug == "chua-tran-quoc" else "pi"
            did, tok = f"{kind}-{t.slug}"[:64], f"sim-{t.slug}"
            if not db.get(Device, did):
                db.add(Device(id=did, name=("Điện thoại " if kind == "phone" else "Pi ") + t.name,
                              token_hash=hash_token(tok)))
                db.flush()
            t.device_id = did
        # kiosk Đền Ngọc Sơn "quên" bày gà luộc → AI báo thiếu
        devs.append({"id": did, "token": tok, "kind": kind, "temple": t.name, "video": True,
                     "drop": ["Gà luộc"] if t.slug == "den-ngoc-son" else [], "battery": 87 if kind == "phone" else None})
    pk = {p.name: p.id for p in db.scalars(select(OfferingPackage))}
    ids = {t.slug: t.id for t in db.scalars(select(Temple))}
    ids["ns"], ids["tq"] = ids["den-ngoc-son"], ids["chua-tran-quoc"]
    db.commit()
(HERE / "devices.json").write_text(json.dumps(devs, ensure_ascii=False))
(HERE / "ids.json").write_text(json.dumps({"temples": ids, "packages": pk}, ensure_ascii=False))

B = "http://127.0.0.1:8100/le-chua"
c = httpx.Client(base_url=B, timeout=120, follow_redirects=True)
tok = lambda path: re.search(r'name="csrf-token" content="([^"]+)"', c.get(path).text).group(1)
t = tok("/dang-ky")
c.post("/dang-ky", data={"name": "Nguyễn Văn An", "ngay_sinh": "1985-03-12", "dia_chi": "Cầu Giấy, Hà Nội",
                         "identifier": "demo-an@example.com", "password": "demo-password", "csrf_token": t})
t = tok("/tai-khoan/the")
c.post("/tai-khoan/the", data={"so_the": "4242 4242 4242 4242", "het_han": "12/28", "cvc": "123",
                               "chu_the": "NGUYEN VAN AN", "csrf_token": t})
tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=7, minute=0).strftime("%Y-%m-%dT%H:%M")

# đơn 1: Ngọc Sơn, hẹn giờ sáng mai (thủ nhang sẽ từ chối)
t = tok("/dat-le")
r = c.post("/dat-le", data={"csrf_token": t, "den": str(ids["ns"]), f"sl_{pk['Hương (nhang)']}": "1",
                            f"sl_{pk['Hoa tươi']}": "1", "nguyen_vong": "cầu cho mẹ con sớm khỏi bệnh",
                            "cach_khan": "tts", "khi_nao": "hen_gio", "thoi_gian": tomorrow, "thanh_toan": "the"})
print("đơn từ chối:", r.status_code, r.text[:200])

# đơn 2: Trấn Quốc, khách tự ghi âm (chờ kiểm duyệt)
mp3 = HERE / "data" / "tu-doc.mp3"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=20", str(mp3)], check=True)
t = tok("/dat-le")
up = c.post("/dat-le/ghi-am", data={"csrf_token": t}, files={"file": ("tu-doc.mp3", mp3.read_bytes(), "audio/mpeg")},
            headers={"X-CSRF-Token": t}).json()
print("ghi âm:", up)
r = c.post("/dat-le", data={"csrf_token": t, "den": str(ids["tq"]), f"sl_{pk['Hương (nhang)']}": "1",
                            f"sl_{pk['Oản']}": "1", "nguyen_vong": "cầu bình an cho gia đình",
                            "cach_khan": "recorded", "ghi_am": up.get("key", ""), "khi_nao": "hen_gio",
                            "thoi_gian": tomorrow, "thanh_toan": "the"})
print("đơn ghi âm:", r.status_code, r.text[:200])
