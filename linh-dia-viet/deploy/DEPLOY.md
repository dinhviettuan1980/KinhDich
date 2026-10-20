# Deploy lên VPS (tuandv.id.vn)

```bash
cd linh-dia-viet
DEPLOY_HOST=root@103.163.216.32 ./deploy/deploy.sh --fe     # --fe: build lại và đẩy frontend Kinh Dịch
```

Script làm theo thứ tự:
1. Kiểm tra máy chủ có Docker Compose.
2. `rsync` mã nguồn tới `/opt/linh-dia-viet`. Không đụng `.env`, `data/` và passwd thiết bị trên máy chủ.
3. Lần đầu: tạo `.env` từ `.env.prod.example`, sinh ngẫu nhiên `SECRET_KEY`, `MQTT_PASSWORD`, `DEMO_DEVICE_TOKEN`, `ADMIN_PASSWORD`.
   Mật khẩu admin in ra **một lần**.
4. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`, sau đó kiểm tra `/le-chua/healthz`.
5. `--fe`: chạy `npm run build` ở repo Kinh Dịch rồi `rsync dist/` tới `FE_DIR` (mặc định `/var/www/kinhdich`).
6. Ghi `/etc/nginx/snippets/le-chua.conf`. Nếu server block đã `include` snippet này thì nạp lại nginx;
   nếu chưa, script in hướng dẫn thêm 1 dòng.

## Việc cần làm tay ở lần đầu

- Thêm `include /etc/nginx/snippets/le-chua.conf;` vào `server { listen 443 … server_name tuandv.id.vn; }`, rồi chạy
  `nginx -t && systemctl reload nginx`.
- Mở cổng thiết bị: `ufw allow 8883/tcp`. Không mở 1883, vì cổng này chỉ dùng nội bộ.
- Gia hạn chứng chỉ: thêm deploy hook để mosquitto nạp lại chứng chỉ mới:
  `echo 'cd /opt/linh-dia-viet && docker compose restart mosquitto' > /etc/letsencrypt/renewal-hooks/deploy/mosquitto.sh && chmod +x $_`
- Pi kết nối bằng `LD_MQTT_HOST=tuandv.id.vn`, `LD_MQTT_PORT=8883`, `LD_MQTT_TLS=true`, `LD_SERVER_URL=https://tuandv.id.vn/le-chua`.

## Biến điều khiển

`DEPLOY_HOST` (bắt buộc), `REMOTE_DIR` (mặc định `/opt/linh-dia-viet`), `FE_DIR` (mặc định `/var/www/kinhdich`).
Trong `.env` máy chủ: `LD_API_BIND=127.0.0.1:8040`, `LD_MQTT_BIND=127.0.0.1:1883`, `LD_DOMAIN=tuandv.id.vn`.

## Lưu ý SSH

Ngày 2026-10-20, `known_hosts` trên máy dev có khoá cũ cho `tuandv.id.vn` (báo *host key changed*). Khoá theo IP
`103.163.216.32` thì vẫn khớp. Kiểm tra fingerprint trên VPS (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`)
rồi mới chạy `ssh-keygen -R tuandv.id.vn`. Trước khi đó, dùng `DEPLOY_HOST=root@103.163.216.32`.
