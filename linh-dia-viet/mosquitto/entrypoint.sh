#!/bin/sh
# Sinh file mật khẩu lúc khởi động và nạp lại khi API thêm/thu hồi thiết bị (không commit passwd).
#  - ld-server và thiết bị demo: lấy từ biến môi trường.
#  - Thiết bị thêm qua trang admin: API ghi dòng "device_id:<băm PBKDF2>" vào /mosquitto/extra/devices.passwd.
set -e
PW=/mosquitto/config/passwd
EXTRA=/mosquitto/extra/devices.passwd

build() {
  : > "$PW.new"
  chmod 0700 "$PW.new"
  mosquitto_passwd -b "$PW.new" ld-server "${MQTT_PASSWORD:?thiếu MQTT_PASSWORD}"
  if [ -n "$DEMO_DEVICE_ID" ] && [ -n "$DEMO_DEVICE_TOKEN" ]; then
    mosquitto_passwd -b "$PW.new" "$DEMO_DEVICE_ID" "$DEMO_DEVICE_TOKEN"
  fi
  if [ -f "$EXTRA" ]; then
    grep -E '^[a-z0-9-]+:\$7\$' "$EXTRA" >> "$PW.new" || true
  fi
  chown mosquitto:mosquitto "$PW.new" 2>/dev/null || true
  mv "$PW.new" "$PW"
}

cp /mosquitto/acl.src /mosquitto/config/acl
chown mosquitto:mosquitto /mosquitto/config/acl 2>/dev/null || true
chmod 0700 /mosquitto/config/acl
build

mosquitto -c /mosquitto/config/mosquitto.conf &
PID=$!
trap 'kill -TERM $PID; wait $PID; exit 0' TERM INT

last=$(stat -c %Y "$EXTRA" 2>/dev/null || echo 0)
while kill -0 $PID 2>/dev/null; do
  sleep 5
  now=$(stat -c %Y "$EXTRA" 2>/dev/null || echo 0)
  if [ "$now" != "$last" ]; then
    last=$now
    build
    kill -HUP $PID
    echo "Đã nạp lại danh sách thiết bị MQTT"
  fi
done
wait $PID
