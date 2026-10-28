#!/usr/bin/env python3
"""Thử đầu-cuối trên production với thiết bị THẬT: khách mới đăng ký → thẻ giả → chọn lễ vật → chốt lễ (đọc ngay)
→ Pi ở đền phát + gửi ảnh/video → tải video tại đền về clip-<đơn>.mp4.

    python scripts/prod_order.py                       # Đền Ngọc Sơn (pi-demo-01)
    python scripts/prod_order.py --den chua-tran-quoc  # Chùa Trấn Quốc (pi-tranquoc-01)

Mỗi lần chạy tạo 1 tài khoản thử @example.com và 1 đơn thật (thẻ giả lập, không trừ tiền).
"""
import argparse
import re
import secrets
import sys
import time

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="https://tuandv.id.vn/le-chua")
ap.add_argument("--den", default="den-ngoc-son", help="slug trang đền, vd chua-tran-quoc")
args = ap.parse_args()
base = args.base
c = httpx.Client(base_url=base, follow_redirects=False, timeout=180)


def csrf(path):
    return re.search(r'name="csrf-token" content="([^"]+)"', c.get(path).text).group(1)


email = f"demo-{secrets.token_hex(3)}@example.com"
r = c.post("/dang-ky", data={"name": "Nguyễn Văn Demo", "identifier": email, "password": "demo-password",
                             "ngay_sinh": "1985-03-12", "dia_chi": "Cầu Giấy, Hà Nội", "csrf_token": csrf("/dang-ky")})
print("đăng ký →", r.headers.get("location"))
tok = csrf("/")
r = c.post("/tai-khoan/the", data={"so_the": "4242 4242 4242 4242", "het_han": "12/28", "cvc": "123",
                                   "chu_the": "NGUYEN VAN DEMO", "csrf_token": tok})
print("thẻ →", r.status_code, r.headers.get("location"))
temple_id = re.search(r"dat-le\?den=(\d+)", c.get(f"/den/{args.den}").text).group(1)
page = c.get(f"/dat-le?den={temple_id}").text
assert "Chốt lễ" in page, page[:500]
ids = {n: i for n, i in re.findall(r'ld-item-info"><b>([^<]+)</b>.*?name="sl_(\d+)"', page, re.S)}
want = {n: q for n, q in {"Hương (nhang)": 2, "Hoa tươi": 1, "Ngũ quả": 1, "Gà luộc": 1, "Xôi gấc": 1}.items() if n in ids}
print("lễ vật:", want)
t0 = time.time()
r = c.post("/dat-le", headers={"X-CSRF-Token": tok}, data={
    "den": temple_id, **{f"sl_{ids[n]}": str(q) for n, q in want.items()},
    "nguyen_vong": "gia đình mạnh khỏe, bình an", "cach_khan": "tts", "khi_nao": "ngay", "thanh_toan": "the"})
assert r.status_code == 200, r.text[:300]
print("chốt lễ →", r.json()["redirect"])
hist = c.get(r.json()["redirect"].replace("/le-chua", "", 1)).text
oid = int(re.search(r'href="/le-chua/don/(\d+)"', hist).group(1))
print(f"Đơn #{oid} ({email})", flush=True)
last = None
while time.time() - t0 < 600:
    j = c.get(f"/don/{oid}/json").json()
    if j["status"] != last:
        print(f"  +{time.time() - t0:5.1f}s  {j['status']}", flush=True)
        last = j["status"]
    if j["status"] in ("completed", "failed", "rejected", "cancelled"):
        break
    time.sleep(1)
t1 = time.time()
print("video tại đền:", j.get("video"), "| ảnh:", [e["phase"] for e in j["evidence"]])
v = c.get(f"/don/{oid}/clip")
print("clip:", v.status_code, v.headers.get("content-type"), len(v.content), f"bytes, dựng {time.time() - t1:.1f}s")
if v.status_code == 200:
    open(f"clip-{oid}.mp4", "wb").write(v.content)
sys.exit(0 if j["status"] == "completed" else 1)
