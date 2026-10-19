# Kế hoạch – Linh Địa Việt (bản thử nghiệm)

## Cấu trúc thư mục

```
linh-dia-viet/
├── docker-compose.yml        # api + mosquitto
├── .env.example
├── pytest.ini                # chạy test cả server/ và pi-agent/
├── docs/                     # PLAN, DECISIONS, DEMO
├── mosquitto/                # cấu hình broker, ACL, entrypoint sinh passwd
├── scripts/                  # demo_e2e.py, add_device.py
├── server/                   # FastAPI
│   ├── Dockerfile, requirements.txt, alembic.ini, alembic/
│   └── app/
│       ├── main.py           # tạo app, mount mọi route dưới APP_PREFIX (mặc định /le-chua)
│       ├── config.py, db.py, models.py, seed.py
│       ├── security.py       # băm mật khẩu, phiên, CSRF, rate limit, token thiết bị
│       ├── state_machine.py  # MỘT chỗ duy nhất định nghĩa chuyển trạng thái đơn
│       ├── lunar.py          # dương → âm (Hồ Ngọc Đức, UTC+7), can chi
│       ├── prayer_text.py    # render mẫu sớ, chuẩn hoá đọc (từ điển phát âm)
│       ├── tts.py, audio.py, storage.py, payments.py
│       ├── device_bus.py     # DeviceBus: MqttDeviceBus | InMemoryDeviceBus
│       ├── devices.py        # xử lý ACK/status, giao job, khóa khẩn cấp
│       ├── scheduler.py      # vòng nền: gửi lệnh trước giờ hẹn, đánh dấu failed
│       ├── routers/          # auth, public, booking, orders, admin, device_api, files
│       ├── templates/        # layout tách: _header.html, _footer.html, base.html
│       └── static/
└── pi-agent/
    ├── ld_agent/             # config, queue (SQLite), player, camera, transport, agent
    ├── install.sh, linh-dia-viet-agent.service, .env.example, README.md
    └── tests/
```

## Schema (rút gọn)

users, otp_codes, temples, offering_packages, prayer_templates, prayers, orders,
payments, devices, device_jobs, evidence, audit_log, settings (khóa khẩn cấp).
Một `prayer` → nhiều `orders` (≤100 đền). Mỗi order có văn bản/audio cuối cùng
riêng (vì sớ chứa tên đền), payment riêng, device_job riêng, evidence riêng.

## Giao thức thiết bị

Theo đặc tả: `ld/{id}/cmd` (QoS1, phiên bền), `ld/{id}/ack`, `ld/{id}/status`
(retained + LWT). Thêm lệnh `{type:"capture", ref:"test"}` cho nút "chụp thử".
Audio tải qua URL có chữ ký HMAC (1 giờ); ảnh upload qua HTTPS
`POST {prefix}/api/device/evidence` với `Authorization: Bearer <token>`.

ACK → trạng thái đơn: `received`→delivered, `playing`→playing, `done`→played,
ảnh "after" → evidence_received → completed. `error`→failed.

## Mốc

M1 nền tảng → M2 đặt lễ & sớ → M3 thiết bị (simulate) → M4 phần cứng thật → M5 hoàn thiện.
Mỗi mốc: test pass + 1 commit.
