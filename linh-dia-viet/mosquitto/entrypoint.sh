#!/bin/sh
# Sinh file mật khẩu từ biến môi trường mỗi lần khởi động (không commit passwd).
# Thiết bị thêm sau: scripts/add_device.py ghi vào mosquitto/devices.passwd.txt (device_id:token).
set -e
PW=/mosquitto/config/passwd
: > "$PW"
chmod 0700 "$PW"
mosquitto_passwd -b "$PW" ld-server "${MQTT_PASSWORD:?thiếu MQTT_PASSWORD}"
if [ -n "$DEMO_DEVICE_ID" ] && [ -n "$DEMO_DEVICE_TOKEN" ]; then
  mosquitto_passwd -b "$PW" "$DEMO_DEVICE_ID" "$DEMO_DEVICE_TOKEN"
fi
if [ -f /mosquitto/extra/devices.passwd.txt ]; then
  grep -v '^#' /mosquitto/extra/devices.passwd.txt | while IFS=: read -r id tok; do
    [ -n "$id" ] && mosquitto_passwd -b "$PW" "$id" "$tok"
  done
fi
cp /mosquitto/acl.src /mosquitto/config/acl
chown mosquitto:mosquitto "$PW" /mosquitto/config/acl 2>/dev/null || true
chmod 0700 /mosquitto/config/acl
exec mosquitto -c /mosquitto/config/mosquitto.conf
