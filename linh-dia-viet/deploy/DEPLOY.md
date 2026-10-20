# Deploy lên VPS tuandv.id.vn (đang dùng)

VPS không có Docker, nên app chạy giống các app khác trên máy: **pm2 + nginx**, cộng thêm **Mosquitto** cài bằng apt.

| Thành phần | Ở đâu |
|---|---|
| Mã nguồn | `~/KinhDich/linh-dia-viet` (cùng repo Kinh Dịch; cron `auto-deploy.sh` tự `git pull` khi `main` có commit mới) |
| API | pm2 `linhdia-api` → uvicorn `127.0.0.1:8042`, venv `~/KinhDich/linh-dia-viet/.venv` |
| Cấu hình | `~/KinhDich/linh-dia-viet/.env` (chmod 600, không commit) |
| Dữ liệu | `~/linh-dia-viet-data/` (SQLite `linhdia.db`, `files/` audio + ảnh, `mqtt/devices.passwd`) |
| Web | nginx `tuandv.id.vn`: `include /etc/nginx/snippets/le-chua.conf` → `https://tuandv.id.vn/le-chua/` |
| MQTT | mosquitto: `127.0.0.1:1883` (API) + `:8883` TLS (thiết bị), cấu hình ở `/etc/mosquitto/conf.d/linhdia.conf` |
| Mật khẩu MQTT | `/usr/local/sbin/linhdia-mqtt-sync` dựng `/etc/mosquitto/linhdia.passwd`. Chạy tự động khi admin thêm hoặc thu hồi thiết bị (`linhdia-mqtt-sync.path`) và khi certbot gia hạn chứng chỉ |

## Cài lần đầu (đã làm ngày 2026-10-20)

```bash
ssh pc1@103.163.216.32
cd ~/KinhDich/linh-dia-viet && ADMIN_EMAIL=<email admin> bash deploy/server/setup.sh
echo 'bash /home/pc1/KinhDich/linh-dia-viet/deploy/server/update.sh' >> ~/deploy-kinhdich.sh
```

## Cập nhật

Chỉ cần push lên `main`. Khoảng 2 phút sau, `auto-deploy.sh` chạy `deploy-kinhdich.sh`: build frontend Kinh Dịch,
rồi chạy `update.sh` (pip install, `alembic upgrade`, seed, `pm2 restart linhdia-api`). Theo dõi trong `~/auto-deploy.log`.

## Kiểm tra từ máy dev (demo đầu-cuối trên production)

```bash
.venv/bin/python scripts/demo_e2e.py --base https://tuandv.id.vn/le-chua \
  --mqtt-host tuandv.id.vn --mqtt-port 8883 --mqtt-tls --device-token <DEMO_DEVICE_TOKEN trong .env máy chủ>
```

## Pi kết nối production

`LD_SERVER_URL=https://tuandv.id.vn/le-chua`, `LD_MQTT_HOST=tuandv.id.vn`, `LD_MQTT_PORT=8883`, `LD_MQTT_TLS=true`.
Nếu nhà cung cấp VPS có tường lửa riêng, cần mở cổng **8883/tcp**.

## Phương án Docker

Nếu sau này VPS có Docker: `DEPLOY_HOST=pc1@103.163.216.32 ./deploy/deploy.sh` dùng `docker-compose.prod.yml`.
Khi dùng phương án này, đặt `LD_API_BIND=127.0.0.1:8042`, vì cổng 8040 trên VPS đã có app Java chiếm.
