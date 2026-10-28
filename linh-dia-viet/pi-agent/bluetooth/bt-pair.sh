#!/usr/bin/env bash
# Ghép loa Bluetooth cho agent. Bật loa ở chế độ ghép đôi (đèn nháy nhanh) rồi chạy:
#   sudo ./bt-pair.sh            # quét 30s, liệt kê thiết bị có tên
#   sudo ./bt-pair.sh AA:BB:CC:DD:EE:FF [âm lượng 0-100]
# Ghép + tin cậy + kết nối, ghi địa chỉ vào /etc/linh-dia-viet/bt-speaker (timer tự kết nối lại),
# đặt LD_AUDIO_DEVICE trong agent.env sang loa này và khởi động lại agent.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo"; exit 1; }
ETC=/etc/linh-dia-viet
rfkill unblock bluetooth || true
bluetoothctl power on >/dev/null
bluetoothctl pairable on >/dev/null
M="${1:-}"
if [ -z "$M" ]; then
  echo "Đang quét 30s…"
  bluetoothctl --timeout 30 scan on >/dev/null 2>&1 || true
  bluetoothctl devices | grep -vE "Device ([0-9A-F]{2}:){5}[0-9A-F]{2} ([0-9A-F]{2}-){5}[0-9A-F]{2}$" || true
  echo "Chạy lại: sudo $0 <địa chỉ loa>"
  exit 0
fi
bluetoothctl --timeout 15 scan on >/dev/null 2>&1 || true
bluetoothctl --timeout 20 pair "$M" || true      # đã ghép từ trước thì báo AlreadyExists — bỏ qua
bluetoothctl trust "$M"
bluetoothctl --timeout 15 connect "$M"
echo "$M" > "$ETC/bt-speaker"
sed -i "s|^LD_AUDIO_DEVICE=.*|LD_AUDIO_DEVICE=alsa/bluealsa:DEV=$M,PROFILE=a2dp|" "$ETC/agent.env"
sleep 2
CTL=$(sudo -u linhdia amixer -D bluealsa scontrols | grep -m1 A2DP | sed "s/^Simple mixer control '\(.*\)',0$/\1/")
[ -n "$CTL" ] && sudo -u linhdia amixer -q -D bluealsa sset "$CTL" "${2:-100}%" && echo "Âm lượng loa: ${2:-100}%"
systemctl restart linh-dia-viet-agent
echo "Xong: agent phát qua loa $M"
