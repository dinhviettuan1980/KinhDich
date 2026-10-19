# Kịch bản demo

## A. Tự động (không cần Pi) — `scripts/demo_e2e.py`

```bash
cd linh-dia-viet
cp .env.example .env          # đổi SECRET_KEY, MQTT_PASSWORD, DEMO_DEVICE_TOKEN, ADMIN_PASSWORD
docker compose up -d --build
uv venv -p 3.11 .venv && uv pip install --python .venv/bin/python -r server/requirements-dev.txt -r pi-agent/requirements.txt
.venv/bin/python scripts/demo_e2e.py
```

Script tự làm các bước: đăng ký khách → đặt lễ ở Đền Ngọc Sơn (sinh sớ + TTS) với giờ hẹn khoảng 3 phút sau → thanh toán
giả lập → chạy `pi-agent --simulate` với thiết bị `pi-demo-01` qua MQTT thật → in dòng thời gian
`created → awaiting_payment → paid → scheduled → delivered → playing → played → evidence_received → completed`
và ba ảnh `before / start / after`. Kết quả mong đợi: `✅ DEMO THÀNH CÔNG` (mất khoảng 4 phút).

## B. Bằng tay trên trình duyệt (điện thoại)

1. Mở `http://<máy>:8000/le-chua/`, đăng ký hoặc đăng nhập.
   Có thể dùng OTP: mã in ra ở `docker compose logs api | grep OTP`.
2. Chọn **Đền Ngọc Sơn** → **Đặt lễ** → chọn gói → điền thông tin → chọn giờ (xem ngày âm hiện bên dưới).
3. Bấm **Xem trước bài khấn**, sửa nhẹ nếu muốn, bấm **Nghe thử giọng đọc**. Hoặc chọn **Tôi tự ghi âm** để ghi âm
   (tối đa 5 phút), nghe lại, rồi bấm **Dùng bản ghi này**.
4. **Xem lại đơn** → **Xác nhận và thanh toán** → **Thanh toán thành công** (giả lập).
5. Trang đơn tự cập nhật mỗi 3 giây. Chạy Pi giả lập ở terminal khác:
   ```bash
   cd pi-agent && LD_SERVER_URL=http://localhost:8000/le-chua LD_DEVICE_ID=pi-demo-01 \
     LD_DEVICE_TOKEN=<DEMO_DEVICE_TOKEN> LD_DATA_DIR=/tmp/ld-pi ../.venv/bin/python -m ld_agent --simulate --env /dev/null
   ```
6. Đăng nhập admin (`ADMIN_EMAIL`/`ADMIN_PASSWORD`) → **Quản lý**:
   - **Thiết bị**: thấy `pi-demo-01` Online; bấm **Phát âm thử**, **Chụp thử** (ảnh hiện sau vài giây), **Dừng ngay**.
   - **Lịch lễ & đơn hàng** → bấm số đơn để xem log từng job, **Gửi lại job**.
   - **Kiểm duyệt ghi âm**: đặt `AUTO_APPROVE_RECORDINGS=false`, ghi âm một đơn, rồi nghe, duyệt hoặc từ chối.
   - **KHÓA KHẨN CẤP**: mọi thiết bị nhận lệnh `stop`, và mọi lệnh mới bị chặn cho tới khi mở khóa.
7. Tài khoản nhân sự mẫu (chỉ khi `ENV=dev`), mật khẩu `DEMO_STAFF_PASSWORD` (mặc định `demo12345`):
   `kiosk@example.com` (bán hàng kiosk: lịch lễ không có dữ liệu cá nhân, nút "Mâm lễ đã bày", sửa gói lễ của đền)
   và `quanly@example.com` (quản lý đền: sửa thông tin đền, mẫu sớ riêng, từ chối đơn).

## C. Trên Raspberry Pi thật

Làm theo [pi-agent/README.md](../pi-agent/README.md), mục 1–7: đặt một đơn hẹn sau 2 phút, loa phát đúng giờ, ảnh mâm lễ
hiện trong trang đơn.
