#!/bin/sh
# (root) Dựng /etc/mosquitto/linhdia.passwd từ .env + danh sách thiết bị API ghi ra, chép chứng chỉ TLS, nạp lại mosquitto.
# Chạy tự động khi file thiết bị đổi (linhdia-mqtt-sync.path) và khi certbot gia hạn chứng chỉ.
set -e
APP=/home/pc1/KinhDich/linh-dia-viet
DOMAIN=tuandv.id.vn
envval() { grep -E "^$1=" "$APP/.env" | head -1 | cut -d= -f2- | sed 's/^"//; s/"$//'; }
PW=/etc/mosquitto/linhdia.passwd
FRAG=$(envval MQTT_PASSWD_FILE)
umask 077
: > "$PW.new"
mosquitto_passwd -b "$PW.new" ld-server "$(envval MQTT_PASSWORD)"
[ -n "$(envval DEMO_DEVICE_TOKEN)" ] && mosquitto_passwd -b "$PW.new" "$(envval DEMO_DEVICE_ID)" "$(envval DEMO_DEVICE_TOKEN)"
[ -f "$FRAG" ] && grep -E '^[a-z0-9-]+:\$7\$' "$FRAG" >> "$PW.new" || true
chown root:mosquitto "$PW.new" && chmod 640 "$PW.new" && mv "$PW.new" "$PW"
mkdir -p /etc/mosquitto/certs
cp -L "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /etc/mosquitto/certs/
chown -R mosquitto:mosquitto /etc/mosquitto/certs && chmod 600 /etc/mosquitto/certs/privkey.pem
if [ "$1" = "--restart" ]; then systemctl restart mosquitto; else systemctl reload mosquitto || systemctl restart mosquitto; fi
