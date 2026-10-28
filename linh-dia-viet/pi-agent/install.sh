#!/usr/bin/env bash
# Cài agent Linh Địa Việt trên Raspberry Pi OS (Bookworm). Chạy: sudo ./install.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo"; exit 1; }
SRC="$(cd "$(dirname "$0")" && pwd)"
APP=/opt/linh-dia-viet-agent
ETC=/etc/linh-dia-viet
DATA=/var/lib/linh-dia-viet

echo "==> Cài gói hệ thống"
apt-get update
apt-get install -y python3-venv python3-pil mpv ffmpeg alsa-utils fswebcam fonts-dejavu-core fonts-noto-color-emoji \
  bluez bluez-alsa-utils iw
# camera CSI: rpicam-apps + picamera2 có sẵn trên Raspberry Pi OS Bookworm; cài thêm nếu thiếu
apt-get install -y rpicam-apps python3-picamera2 || echo "(bỏ qua: không có gói camera CSI)"

echo "==> Tạo người dùng dịch vụ"
id linhdia >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin linhdia
usermod -aG audio,video linhdia

echo "==> Chép mã nguồn"
mkdir -p "$APP" "$ETC" "$DATA"
cp -r "$SRC/ld_agent" "$SRC/requirements.txt" "$APP/"
# --system-site-packages để dùng picamera2/libcamera của hệ thống
python3 -m venv --system-site-packages "$APP/venv"
"$APP/venv/bin/pip" install --upgrade pip
"$APP/venv/bin/pip" install -r "$APP/requirements.txt"

if [ ! -f "$ETC/agent.env" ]; then
  cp "$SRC/.env.example" "$ETC/agent.env"
  echo "!! Hãy sửa $ETC/agent.env (LD_DEVICE_ID, LD_DEVICE_TOKEN, LD_SERVER_URL, LD_MQTT_HOST) rồi chạy:"
  echo "   sudo systemctl restart linh-dia-viet-agent"
fi
chown -R linhdia:linhdia "$DATA"
chown root:linhdia "$ETC/agent.env"
chmod 640 "$ETC/agent.env"

echo "==> Wi-Fi: tắt tiết kiệm điện (ở đền chỉ có Wi-Fi; chip Broadcom ngủ giữa các gói → trễ, rớt MQTT)"
if [ -d /etc/NetworkManager/conf.d ]; then
  printf '[connection]\nwifi.powersave = 2\n' > /etc/NetworkManager/conf.d/ld-wifi-powersave.conf
  systemctl reload NetworkManager || true
fi
iw dev wlan0 set power_save off 2>/dev/null || true

echo "==> Đồng bộ giờ (NTP)"
timedatectl set-ntp true || true

echo "==> Loa Bluetooth (bluez-alsa: chạy như dịch vụ hệ thống, không cần phiên đăng nhập)"
systemctl disable --now bluealsa-aplay 2>/dev/null || true   # Pi là nguồn phát, không phải loa nhận
systemctl enable --now bluealsa || true
install -m 755 "$SRC/bluetooth/ld-bt-reconnect" /usr/local/bin/ld-bt-reconnect
install -m 644 "$SRC/bluetooth/ld-bt-reconnect.service" "$SRC/bluetooth/ld-bt-reconnect.timer" /etc/systemd/system/

echo "==> Cài dịch vụ systemd"
cp "$SRC/linh-dia-viet-agent.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ld-bt-reconnect.timer   # không có /etc/linh-dia-viet/bt-speaker thì không làm gì
systemctl enable linh-dia-viet-agent
systemctl restart linh-dia-viet-agent
systemctl --no-pager status linh-dia-viet-agent | head -5 || true
echo "Xong. Xem log: journalctl -u linh-dia-viet-agent -f"
