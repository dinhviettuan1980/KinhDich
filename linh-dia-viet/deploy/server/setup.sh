#!/usr/bin/env bash
# Cài / cập nhật Linh Địa Việt trên VPS tuandv.id.vn KHÔNG dùng Docker (theo kiểu các app khác: pm2 + nginx).
# Chạy bằng user pc1 trong ~/KinhDich/linh-dia-viet:  bash deploy/server/setup.sh   (cần sudo cho mosquitto/nginx)
# Chạy lại nhiều lần không sao. Bản cập nhật thường ngày chỉ cần: bash deploy/server/update.sh
set -euo pipefail
APP="$(cd "$(dirname "$0")/../.." && pwd)"
DATA="${LD_DATA:-$HOME/linh-dia-viet-data}"
PORT="${LD_PORT:-8042}"
DOMAIN="${LD_DOMAIN:-tuandv.id.vn}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@$DOMAIN}"
cd "$APP"
mkdir -p "$DATA/mqtt"

echo "==> .env"
if [ ! -f .env ]; then
  r() { openssl rand -hex 24; }
  ADMIN_PW=$(openssl rand -base64 12 | tr -d '/+=')
  cat > .env <<ENV
ENV=prod
SECRET_KEY=$(r)
DATABASE_URL=sqlite:///$DATA/linhdia.db
DATA_DIR=$DATA
APP_PREFIX=/le-chua
PUBLIC_BASE_URL=https://$DOMAIN
SESSION_HTTPS_ONLY=true
HOME_URL=/kinhdich/van-khan
HOME_LABEL="Kinh Dịch"
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PW
AUTO_APPROVE_RECORDINGS=true
MIN_LEAD_SECONDS=120
TTS_PROVIDER=edge
DEVICE_BUS=mqtt
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=ld-server
MQTT_PASSWORD=$(r)
MQTT_PASSWD_FILE=$DATA/mqtt/devices.passwd
DEMO_DEVICE_ID=pi-demo-01
DEMO_DEVICE_TOKEN=$(r)
ENV
  chmod 600 .env
  echo "   Tài khoản admin: $ADMIN_EMAIL / $ADMIN_PW   (ghi lại ngay, chỉ hiện 1 lần)"
fi

echo "==> Mosquitto (MQTT: 1883 nội bộ, 8883 TLS cho thiết bị)"
sudo apt-get install -y -q mosquitto mosquitto-clients >/dev/null
sudo install -m 644 deploy/server/mosquitto-linhdia.conf /etc/mosquitto/conf.d/linhdia.conf
sudo install -m 644 mosquitto/acl /etc/mosquitto/linhdia.acl
sudo install -m 755 deploy/server/mqtt-sync.sh /usr/local/sbin/linhdia-mqtt-sync
sudo sed -i "s|^APP=.*|APP=$APP|; s|^DOMAIN=.*|DOMAIN=$DOMAIN|" /usr/local/sbin/linhdia-mqtt-sync
sed "s|@FRAGMENT@|$DATA/mqtt/devices.passwd|" deploy/server/linhdia-mqtt-sync.path | sudo tee /etc/systemd/system/linhdia-mqtt-sync.path >/dev/null
sudo install -m 644 deploy/server/linhdia-mqtt-sync.service /etc/systemd/system/linhdia-mqtt-sync.service
printf '#!/bin/sh\n/usr/local/sbin/linhdia-mqtt-sync\n' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/linhdia-mosquitto.sh >/dev/null
sudo chmod 755 /etc/letsencrypt/renewal-hooks/deploy/linhdia-mosquitto.sh
touch "$DATA/mqtt/devices.passwd"
sudo /usr/local/sbin/linhdia-mqtt-sync --restart
sudo systemctl daemon-reload
sudo systemctl enable --now linhdia-mqtt-sync.path mosquitto >/dev/null

echo "==> API (pm2: linhdia-api, 127.0.0.1:$PORT)"
bash deploy/server/update.sh
if ! pm2 describe linhdia-api >/dev/null 2>&1; then
  pm2 start "$APP/.venv/bin/uvicorn" --name linhdia-api --cwd "$APP/server" --interpreter none -- \
    app.main:app --host 127.0.0.1 --port "$PORT" --proxy-headers --forwarded-allow-ips 127.0.0.1
  pm2 save >/dev/null
fi
for i in $(seq 1 20); do curl -fsS "http://127.0.0.1:$PORT/le-chua/healthz" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:$PORT/le-chua/healthz" && echo "   API OK"

echo "==> nginx /le-chua"
sed "s|127.0.0.1:8000|127.0.0.1:$PORT|" docs/nginx-le-chua.conf | sudo tee /etc/nginx/snippets/le-chua.conf >/dev/null
SITE=/etc/nginx/sites-enabled/$DOMAIN
if ! sudo grep -q "snippets/le-chua.conf" "$SITE"; then
  sudo cp "$SITE" "/home/pc1/nginx-$DOMAIN.bak.$(date +%Y%m%d%H%M%S)"
  # chèn trước "location / {" đầu tiên của server block HTTPS
  sudo sed -i '0,/^    location \/ {/s||    include /etc/nginx/snippets/le-chua.conf;\n\n    location / {|' "$SITE"
fi
sudo nginx -t && sudo systemctl reload nginx
echo "Xong: https://$DOMAIN/le-chua/"
