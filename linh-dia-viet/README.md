# Linh Địa Việt – Lễ chùa từ xa (bản thử nghiệm)

Người dùng ở xa đặt một mâm lễ tại đền/chùa và chọn giờ. Đúng giờ đó, bài khấn được phát ra loa tại đền, camera chụp ảnh mâm lễ gửi về làm bằng chứng.
Bài khấn có hai cách tạo: hệ thống **tự sinh sớ** từ thông tin người dùng rồi đọc bằng TTS, hoặc người dùng **tự ghi âm** trên web.

```
Trình duyệt (mobile) ──HTTPS──▶ FastAPI (Jinja2 + HTMX) ──MQTT/TLS──▶ Mosquitto ◀──MQTT── Raspberry Pi (pi-agent)
                                  │  SQLite/Postgres                                     │  loa (mpv) + camera
                                  │  ffmpeg, TTS (edge/google/fpt)                        │
                                  └── /files (URL ký 1 giờ) ◀────── tải audio ───────────┤
                                      /api/device/evidence ◀─────── upload ảnh JPEG ─────┘
```

| Thư mục | Nội dung |
|---|---|
| `server/` | API + web (FastAPI, SQLAlchemy, Alembic), test trong `server/tests` |
| `pi-agent/` | chương trình trên Raspberry Pi, hướng dẫn cài: [pi-agent/README.md](pi-agent/README.md) |
| `mosquitto/` | cấu hình broker, ACL theo thiết bị, entrypoint sinh/nạp lại mật khẩu |
| `scripts/demo_e2e.py` | demo đầu-cuối tự động |
| `docs/` | [PLAN](docs/PLAN.md), [DECISIONS](docs/DECISIONS.md) (các quyết định thiết kế), [DEMO](docs/DEMO.md), [nginx](docs/nginx-le-chua.conf) |

## Chạy nhanh

```bash
cd linh-dia-viet
cp .env.example .env                 # đổi các giá trị bí mật
docker compose up -d --build         # api :8000 + mosquitto :1883
open http://localhost:8000/le-chua/
```

API tự chạy `alembic upgrade head` và seed dữ liệu mẫu: 3 đền, 4 gói lễ, thiết bị `pi-demo-01` gắn với Đền Ngọc Sơn, tài khoản admin lấy từ `ADMIN_EMAIL`/`ADMIN_PASSWORD`. Khi `ENV=dev`, seed thêm `kiosk@example.com` và `quanly@example.com`.

### Test

```bash
uv venv -p 3.11 .venv
uv pip install --python .venv/bin/python -r server/requirements-dev.txt -r pi-agent/requirements.txt
.venv/bin/python -m pytest                      # server + pi-agent (cần ffmpeg trong PATH)
# Test với Mosquitto thật (docker compose đang chạy):
MQTT_TEST_HOST=localhost MQTT_TEST_PASSWORD=<MQTT_PASSWORD> MQTT_TEST_DEVICE_TOKEN=<DEMO_DEVICE_TOKEN> \
  .venv/bin/python -m pytest -m mqtt
.venv/bin/python scripts/demo_e2e.py            # demo đầu-cuối (~4 phút)
```

Chạy API không qua Docker: `cd server && ../.venv/bin/alembic upgrade head && ../.venv/bin/python -m app.seed && ../.venv/bin/uvicorn app.main:app --reload`. Cần thêm `DEVICE_BUS=memory` nếu không có broker.

## Vai trò người dùng

| Vai trò | Làm được gì |
|---|---|
| Khách hàng (`customer`) | đặt lễ (1 hoặc nhiều đền, tối đa 100), theo dõi, hủy, đặt lại |
| Người bán hàng kiosk (`vendor`) | xem lịch lễ của đền mình (không thấy dữ liệu cá nhân), báo "mâm lễ đã bày", quản lý gói lễ của đền |
| Người quản lý đền (`temple_manager`) | như kiosk, thêm: sửa thông tin đền, mẫu sớ riêng của đền, từ chối đơn |
| Quản trị (`admin`) | toàn quyền: đền, gói, mẫu sớ, người dùng & phân quyền, thiết bị, kiểm duyệt ghi âm, đơn & log job, khóa khẩn cấp |

## Biến môi trường chính (`.env`)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `SECRET_KEY` | — | ký phiên đăng nhập và URL tải file. **Bắt buộc đổi** |
| `DATABASE_URL` | `sqlite:///./data/linhdia.db` | Postgres: `postgresql+psycopg://user:pass@host/db` |
| `APP_PREFIX` | `/le-chua` | tiền tố cho mọi route (để ghép dưới domain khác) |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | gốc URL mà thiết bị dùng để tải audio |
| `SESSION_HTTPS_ONLY` | `false` | đặt `true` khi chạy HTTPS |
| `HOME_URL`, `HOME_LABEL` | — | link "← Kinh Dịch" trên header |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | — | admin tạo lúc seed (chỉ khi chưa có admin) |
| `AUTO_APPROVE_RECORDINGS` | `true` | `false`: bản ghi âm vào hàng chờ duyệt |
| `MIN_LEAD_SECONDS` | `120` | giờ hẹn phải cách hiện tại ít nhất bao nhiêu giây |
| `MAX_PRAYER_CHARS`, `MAX_AUDIO_SECONDS`, `MAX_UPLOAD_BYTES` | 3000 / 300 / 20 MB | giới hạn sớ, audio, file tải lên |
| `TTS_PROVIDER`, `TTS_VOICE` | `edge`, `vi-VN-NamMinhNeural,-8%,-6Hz` (giọng nam miền Bắc; Edge: tên,tốc độ,cao độ) | `google` (`GOOGLE_TTS_API_KEY`), `fpt` (`FPT_TTS_API_KEY`), `fake` |
| `DEVICE_BUS` | `mqtt` | `memory` để chạy không cần broker |
| `MQTT_HOST/PORT/USERNAME/PASSWORD/TLS` | `localhost:1883`, `ld-server` | kết nối broker của server |
| `MQTT_PASSWD_FILE` | (compose đặt sẵn) | file passwd thiết bị dùng chung với mosquitto |
| `DISPATCH_LEAD_SECONDS` | `600` | gửi lệnh xuống Pi trước giờ phát bao lâu |
| `PLAY_GRACE_SECONDS`, `EVIDENCE_TIMEOUT_SECONDS` | 900 / 600 | quá hạn → `failed`; chờ ảnh tối đa |
| `CAPTURE_BEFORE_S`, `CAPTURE_AFTER_S`, `DEFAULT_VOLUME` | 60 / 30 / 70 | cấu hình chụp và âm lượng gửi trong lệnh |
| `DEMO_DEVICE_ID`, `DEMO_DEVICE_TOKEN` | `pi-demo-01` | thiết bị seed sẵn (token đồng thời là mật khẩu MQTT) |
| `PAYMENT_WEBHOOK_SECRET` | — | bật webhook `/api/thanh-toan/webhook/mock` (ký HMAC-SHA256) |

## Thêm thiết bị mới

1. **Quản lý → Thiết bị → Thêm thiết bị** (hoặc `docker compose exec api python -m app.cli add-device pi-ten-den-01 "Tên"`).
   Token hiện **một lần**. Mosquitto tự nạp lại mật khẩu sau khoảng 5 giây.
2. **Quản lý → Đền, chùa** → chọn đền → gắn thiết bị.
3. Cài Pi theo [pi-agent/README.md](pi-agent/README.md), điền `LD_DEVICE_ID`/`LD_DEVICE_TOKEN`.
4. Kiểm tra trên trang Thiết bị: Online, rồi thử **Phát âm thử** và **Chụp thử**.
   Có thể bấm **Cấp token mới** hoặc **Thu hồi token** bất cứ lúc nào.

## Ghép vào trang Kinh Dịch

Chọn cách **liên kết + proxy cùng domain**. App chạy độc lập dưới `/le-chua` ([cấu hình nginx](docs/nginx-le-chua.conf)).
Trang Văn khấn của Kinh Dịch có thẻ "🛕 Lễ chùa từ xa" trỏ sang (`VITE_LE_CHUA_URL`, mặc định `/le-chua/`).
Header của app có link "← Kinh Dịch" (`HOME_URL`). Mọi CSS nằm dưới lớp `.ld`, header/footer là partial riêng,
nên sau này có thể nhúng sang chỗ khác.

## Giới hạn đã biết

- **Chưa kiểm trên Raspberry Pi + loa + camera thật.** Phần cứng mới được kiểm bằng chương trình giả trong PATH, `ffplay` trên máy dev và chế độ `--simulate`.
  Cần chạy mục 7 trong `pi-agent/README.md` để nghiệm thu.
- Thanh toán, OTP (in ra log) và hoàn tiền (admin bấm tay) đều là **giả lập**.
- TTS Google/FPT đã viết nhưng **chưa thử với tài khoản thật**. Edge TTS là dịch vụ không chính thức và có thể đổi bất cứ lúc nào.
- Mẫu sớ khởi đầu **không phải văn khấn chuẩn**, cần người am hiểu chỉnh lại trong **Quản lý → Mẫu sớ**.
- Vòng nền và rate limit chạy trong tiến trình API, nên chỉ được chạy **1 tiến trình/1 replica**.
- File lưu trên đĩa cục bộ (interface `Storage` sẵn sàng đổi sang S3).
- Theo dõi đơn bằng polling 3 giây (không dùng SSE/WebSocket).
- Mosquitto trong compose mở cổng 1883 không TLS. Khi triển khai thật, bật listener 8883 + chứng chỉ và đóng 1883 ra ngoài.
- URL tải audio hết hạn sau 1 giờ. Thiết bị offline lâu hơn thời gian đó trước giờ phát cần admin bấm "Gửi lại job".
- Đặt nhiều đền dùng chung 1 giờ hẹn và 1 gói lễ dùng chung (gói riêng chỉ chọn được khi đặt 1 đền).
